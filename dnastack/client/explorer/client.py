from typing import List, Optional, Dict, Any, TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

if TYPE_CHECKING:
    from dnastack.client.explorer.models import FederatedQuestion
from urllib.parse import urljoin

from dnastack.client.base_client import BaseServiceClient
from dnastack.client.base_exceptions import UnauthenticatedApiAccessError, UnauthorizedApiAccessError
from dnastack.client.models import ServiceEndpoint
from dnastack.client.explorer.models import (
    FederatedQuestion,
    FederatedQuestionListResponse,
    FederatedQuestionQueryRequest,
    QuestionCollection
)
from dnastack.client.result_iterator import ResultLoader, InactiveLoaderError, ResultIterator
from dnastack.client.service_registry.models import ServiceType
from dnastack.common.tracing import Span
from dnastack.http.session import ClientError, HttpSession, HttpError


EXPLORER_SERVICE_TYPE_V1_0 = ServiceType(
    group='com.dnastack.explorer',
    artifact='collection-service',
    version='1.0.0'
)


class ExplorerClient(BaseServiceClient):
    """
    Client for Explorer services supporting federated questions.
    
    This client provides access to federated questions that can be asked
    across multiple collections in the Explorer network.
    """

    def __init__(self, endpoint: ServiceEndpoint):
        super().__init__(endpoint)
        self._session = self.create_http_session()

    @staticmethod
    def get_supported_service_types() -> List[ServiceType]:
        return [EXPLORER_SERVICE_TYPE_V1_0]

    @staticmethod
    def get_adapter_type() -> str:
        return "com.dnastack.explorer:questions:1.0.0"

    def list_federated_questions(self, trace: Optional[Span] = None) -> 'ResultIterator[FederatedQuestion]':
        """
        List all available federated questions.
        
        Returns:
            ResultIterator[FederatedQuestion]: Iterator over federated questions
        """
        return ResultIterator(
            loader=FederatedQuestionListResultLoader(
                service_url=urljoin(self.url, "questions"),
                http_session=self._session,
                trace=trace
            )
        )

    def describe_federated_question(self, question_id: str, trace: Optional[Span] = None) -> 'FederatedQuestion':
        """
        Get detailed information about a specific federated question.
        
        Args:
            question_id: The ID of the question to describe
            trace: Optional tracing span
            
        Returns:
            FederatedQuestion: The question details including parameters and collections
            
        Raises:
            ClientError: If the question is not found or access is denied
        """
        url = urljoin(self.url, f"questions/{question_id}")
        
        with self._session as session:
            try:
                response = session.get(url, trace_context=trace)
                return FederatedQuestion(**response.json())
            except HttpError as e:
                status_code = e.response.status_code
                if status_code == 401:
                    raise UnauthenticatedApiAccessError(
                        f"Authentication required to access question '{question_id}'"
                    )
                elif status_code == 403:
                    raise UnauthorizedApiAccessError(
                        f"Not authorized to access question '{question_id}'"
                    )
                elif status_code == 404:
                    raise ClientError(e.response, e.trace, f"Question '{question_id}' not found")
                else:
                    raise ClientError(e.response, e.trace, f"Failed to retrieve question '{question_id}'")

    def ask_federated_question(
        self,
        question_id: str,
        inputs: Dict[str, str],
        collections: Optional[List[str]] = None,
        trace: Optional[Span] = None
    ) -> 'ResultIterator[Dict[str, Any]]':
        """
        Ask a federated question with the provided parameters.
        
        Args:
            question_id: The ID of the question to ask
            inputs: Dictionary of parameter name -> value mappings
            collections: Optional list of collection IDs to query. If None, all collections are used.
            trace: Optional tracing span
            
        Returns:
            ResultIterator[Dict[str, Any]]: Iterator over query results
            
        Raises:
            ClientError: If the request fails or parameters are invalid
        """
        # If no collections specified, get all collections from question metadata
        if collections is None:
            question = self.describe_federated_question(question_id, trace=trace)
            collections = [col.id for col in question.collections]
        
        request_payload = FederatedQuestionQueryRequest(
            inputs=inputs,
            collections=collections
        )
        
        return ResultIterator(
            loader=FederatedQuestionQueryResultLoader(
                service_url=urljoin(self.url, f"questions/{question_id}/query"),
                http_session=self._session,
                request_payload=request_payload,
                trace=trace
            )
        )

    def ask_question_local_federated(
        self,
        federated_question_id: str,
        inputs: Dict[str, str],
        collections: Optional[List[str]] = None,
        trace: Optional[Span] = None
    ) -> 'ResultIterator[Dict[str, Any]]':
        """
        Query collections directly via local federation instead of server-side federation.
        
        Args:
            federated_question_id: The ID of the federated question to ask
            inputs: Dictionary of parameter name -> value mappings
            collections: Optional list of collection IDs to query. If None, all collections are used.
            trace: Optional tracing span
            
        Returns:
            ResultIterator[Dict[str, Any]]: Iterator over aggregated query results in federated format
        """
        # Get federated question metadata to obtain per-collection question IDs
        question = self.describe_federated_question(federated_question_id, trace=trace)
        
        # Filter collections if specified
        if collections is not None:
            # Create a map of collection ID to QuestionCollection for filtering
            collection_map = {col.id: col for col in question.collections}
            target_collections = [collection_map[cid] for cid in collections if cid in collection_map]
            
            # Check for invalid collection IDs
            invalid_ids = [cid for cid in collections if cid not in collection_map]
            if invalid_ids:
                raise ClientError(
                    response=None,
                    trace=trace,
                    message=f"Invalid collection IDs for question '{federated_question_id}': {', '.join(invalid_ids)}"
                )
        else:
            target_collections = question.collections
        
        # Create the result loader for local federation
        return ResultIterator(
            LocalFederatedQuestionQueryResultLoader(
                explorer_client=self,
                collections=target_collections,
                inputs=inputs,
                trace=trace
            )
        )


class FederatedQuestionListResultLoader(ResultLoader):
    """
    Result loader for listing federated questions.
    """
    
    def __init__(self, service_url: str, http_session: HttpSession, trace: Optional[Span] = None):
        self.__http_session = http_session
        self.__service_url = service_url
        self.__trace = trace
        self.__loaded = False

    def has_more(self) -> bool:
        return not self.__loaded

    def load(self) -> 'List[FederatedQuestion]':
        if self.__loaded:
            raise InactiveLoaderError(self.__service_url)
        
        with self.__http_session as session:
            try:
                response = session.get(self.__service_url, trace_context=self.__trace)
                response_data = response.json()
                
                # Parse the response
                question_list = FederatedQuestionListResponse(**response_data)
                self.__loaded = True
                
                return question_list.questions
                
            except HttpError as e:
                status_code = e.response.status_code
                if status_code == 401:
                    raise UnauthenticatedApiAccessError(
                        "Authentication required to list federated questions"
                    )
                elif status_code == 403:
                    raise UnauthorizedApiAccessError(
                        "Not authorized to list federated questions"
                    )
                else:
                    
                    raise ClientError(e.response, e.trace, "Failed to load federated questions")


class FederatedQuestionQueryResultLoader(ResultLoader):
    """
    Result loader for federated question query results.
    """
    
    def __init__(
        self, 
        service_url: str, 
        http_session: HttpSession, 
        request_payload: FederatedQuestionQueryRequest,
        trace: Optional[Span] = None
    ):
        self.__http_session = http_session
        self.__service_url = service_url
        self.__request_payload = request_payload
        self.__trace = trace
        self.__loaded = False

    def has_more(self) -> bool:
        return not self.__loaded

    def load(self) -> List[Dict[str, Any]]:
        if self.__loaded:
            raise InactiveLoaderError(self.__service_url)
        
        with self.__http_session as session:
            try:
                response = session.post(
                    self.__service_url,
                    json=self.__request_payload.model_dump(),
                    trace_context=self.__trace
                )
                
                response_data = response.json()
                self.__loaded = True
                
                # Handle different response formats
                if isinstance(response_data, list):
                    # Direct list of results
                    return response_data
                elif isinstance(response_data, dict):
                    # Check for common pagination patterns
                    if 'data' in response_data:
                        return response_data['data']
                    elif 'results' in response_data:
                        return response_data['results']
                    else:
                        # Single result object
                        return [response_data]
                else:
                    return [response_data]
                    
            except HttpError as e:
                status_code = e.response.status_code
                if status_code == 401:
                    raise UnauthenticatedApiAccessError(
                        "Authentication required to ask federated questions"
                    )
                elif status_code == 403:
                    raise UnauthorizedApiAccessError(
                        "Not authorized to ask federated questions"
                    )
                elif status_code == 400:
                    
                    raise ClientError(e.response, e.trace, "Invalid question parameters")
                else:
                    
                    raise ClientError(e.response, e.trace, "Failed to execute federated question")


class LocalFederatedQuestionQueryResultLoader(ResultLoader):
    """
    Result loader for local federation queries that queries each collection directly.
    """
    
    def __init__(
        self,
        explorer_client: 'ExplorerClient',
        collections: List[QuestionCollection],
        inputs: Dict[str, str],
        trace: Optional[Span] = None
    ):
        self.__explorer_client = explorer_client
        self.__collections = collections
        self.__inputs = inputs
        self.__trace = trace
        self.__loaded = False
        
    def has_more(self) -> bool:
        return not self.__loaded
        
    def load(self) -> List[Dict[str, Any]]:
        if self.__loaded:
            raise InactiveLoaderError("LocalFederatedQuestionQueryResultLoader")
            
        # Execute parallel queries to each collection
        with ThreadPoolExecutor() as executor:
            # Submit all queries
            future_to_collection = {
                executor.submit(
                    self._query_single_collection,
                    collection
                ): collection
                for collection in self.__collections
            }
            
            # Collect results
            results = []
            for future in as_completed(future_to_collection):
                result = future.result()
                results.append(result)
        
        # Return results directly as a list to match federated format
        self.__loaded = True
        return results  # Return as list to match federated endpoint format
        
    def _query_single_collection(self, collection: QuestionCollection) -> Dict[str, Any]:
        """
        Query a single collection and return the result in federated format.
        """
        start_time = time.time()
        
        # Build the collection-specific endpoint URL
        # Note: explorer URL already ends with /api/, so we don't need to add it again
        url = urljoin(
            self.__explorer_client.url,
            f"collections/{collection.slug}/questions/{collection.question_id}/query"
        )
        
        
        try:
            # Make the request using the explorer client's session
            with self.__explorer_client._session as session:
                # Try using 'params' instead of 'inputs' for the collection endpoint
                response = session.post(
                    url,
                    json={"params": self.__inputs},
                    trace_context=self.__trace
                )
                
                # Parse the Data Connect response
                table_data = response.json()
                
                # Add collection_name to each data item to match federated format
                if 'data' in table_data and isinstance(table_data['data'], list):
                    for item in table_data['data']:
                        item['collection_name'] = collection.name
                
                # Return in federated format
                return {
                    "collectionId": collection.id,
                    "collectionSlug": collection.slug,
                    "results": table_data,  # GA4GH Data Connect format
                    "error": None,
                    "failureInfo": None
                }
                
        except HttpError as e:
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Determine failure reason
            status_code = e.response.status_code if e.response else None
            if status_code == 401:
                reason = "UNAUTHORIZED"
                message = f"Authentication required for collection {collection.name}"
            elif status_code == 403:
                reason = "FORBIDDEN"
                message = f"Access denied to collection {collection.name}"
            elif status_code == 404:
                reason = "NOT_FOUND"
                message = f"Question not found in collection {collection.name}"
            elif status_code == 400:
                reason = "BAD_REQUEST"
                message = f"Invalid parameters for collection {collection.name}"
            elif status_code and status_code >= 500:
                reason = "SERVER_ERROR"
                message = f"Server error for collection {collection.name}"
            else:
                reason = "UNKNOWN"
                message = str(e)
            
            # Return error in federated format
            return {
                "collectionId": collection.id,
                "collectionSlug": collection.slug,
                "results": None,
                "error": message,
                "failureInfo": {
                    "reason": reason,
                    "message": message,
                    "responseTimeMs": response_time_ms
                }
            }
            
        except Exception as e:
            # Handle non-HTTP errors
            response_time_ms = int((time.time() - start_time) * 1000)
            
            return {
                "collectionId": collection.id,
                "collectionSlug": collection.slug,
                "results": None,
                "error": str(e),
                "failureInfo": {
                    "reason": "CLIENT_ERROR",
                    "message": str(e),
                    "responseTimeMs": response_time_ms
                }
            }