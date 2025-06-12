from typing import List, Optional, Dict, Iterator, Any, TYPE_CHECKING

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
    QuestionQueryResult
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
                    raise ClientError(f"Question '{question_id}' not found")
                else:
                    raise ClientError(
                        f"Failed to retrieve question '{question_id}': {e.response.text}"
                    )

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
                    raise ClientError(
                        f"Failed to load federated questions: {e.response.text}"
                    )


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
                    json=self.__request_payload.dict(),
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
                    raise ClientError(
                        f"Invalid question parameters: {e.response.text}"
                    )
                else:
                    raise ClientError(
                        f"Failed to execute federated question: {e.response.text}"
                    )