#### Class `dnastack.client.explorer.client.ExplorerClient(endpoint: dnastack.client.models.ServiceEndpoint)`
Client for Explorer services supporting federated questions.

This client provides access to federated questions that can be asked
across multiple collections in the Explorer network.
##### Properties
###### `endpoint`

###### `events`

###### `url`
The base URL to the endpoint
##### Methods
###### `def ask_federated_question(question_id: str, inputs: Dict[str, str], collections: Optional[List[str]], trace: Optional[dnastack.common.tracing.Span]) -> ResultIterator[Dict[str, Any]]`
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
###### `def create_http_session(suppress_error: bool, no_auth: bool) -> dnastack.http.session.HttpSession`
Create HTTP session wrapper
###### `def describe_federated_question(question_id: str, trace: Optional[dnastack.common.tracing.Span]) -> FederatedQuestion`
Get detailed information about a specific federated question.

Args:
    question_id: The ID of the question to describe
    trace: Optional tracing span
    
Returns:
    FederatedQuestion: The question details including parameters and collections
    
Raises:
    ClientError: If the question is not found or access is denied
###### `@staticmethod def get_adapter_type() -> str`
Get the descriptive adapter type
###### `@staticmethod def get_supported_service_types() -> List[dnastack.client.service_registry.models.ServiceType]`
The list of supported service types

The first one is always regarded as the default type.
###### `def list_federated_questions(trace: Optional[dnastack.common.tracing.Span]) -> ResultIterator[FederatedQuestion]`
List all available federated questions.

Returns:
    ResultIterator[FederatedQuestion]: Iterator over federated questions
###### `@staticmethod def make(endpoint: dnastack.client.models.ServiceEndpoint)`
Create this class with the given `endpoint`.