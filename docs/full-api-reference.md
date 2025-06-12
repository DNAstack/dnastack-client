---
title: "API Reference (v3)"
weight: 1
draft: false
lastmod: 2025-06-10
type: docs
layout: single-col
---

This API reference is only for dnastack-client-library 3.x.
#### Class `dnastack.cli.helpers.client_factory.ConfigurationBasedClientFactory(config_manager: dnastack.configuration.manager.ConfigurationManager)`
Configuration-based Client Factory

This class will provide a service client based on the CLI configuration.
##### Methods
###### `def get(cls: Type[~SERVICE_CLIENT_CLASS], endpoint_id: Optional[str], context_name: Optional[str], **kwargs) -> dnastack.client.constants.SERVICE_CLIENT_CLASS`
Instantiate a service client with the given service endpoint.


| Parameter | Description |
| --- | --- |
| `cls` | The class (type) of the target service client, e.g., cls=DataConnectClient |
| `endpoint_id` | The ID of the endpoint registered in the given context |
| `context_name` | The name of the given context |
| `kwargs` | Extra keyword arguments to the class factory method |

| Return |
| --- |
| an instance of the given class |
#### Class `dnastack.cli.helpers.client_factory.ServiceEndpointNotFound()`
Raised when the requested service endpoint is not found 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.cli.helpers.client_factory.UnknownAdapterTypeError()`
Raised when the given service adapter/short type is not registered or supported 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.cli.helpers.client_factory.UnknownClientShortTypeError()`
Raised when a given short service type is not recognized 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.client.collections.client.CollectionServiceClient(endpoint: dnastack.client.models.ServiceEndpoint)`
Client for Collection API
##### Properties
###### `endpoint`

###### `events`

###### `url`
The base URL to the endpoint
##### Methods
###### `def create_collection(collection: dnastack.client.collections.model.Collection, trace: Optional[dnastack.common.tracing.Span]) -> dnastack.client.collections.model.Collection`
Create a collection
###### `def create_collection_items(collection_id_or_slug_name_or_db_schema_name: str, create_items_request: dnastack.client.collections.model.CreateCollectionItemsRequest, trace: Optional[dnastack.common.tracing.Span])`
Add items to a collection
###### `def create_http_session(suppress_error: bool, no_auth: bool) -> dnastack.http.session.HttpSession`
Create HTTP session wrapper
###### `def data_connect_endpoint(collection: Union[str, dnastack.client.collections.model.Collection, NoneType], no_auth: bool) -> dnastack.client.models.ServiceEndpoint`
Get the URL to the corresponding Data Connect endpoint


| Parameter | Description |
| --- | --- |
| `collection` | The collection or collection ID. It is optional and only used by the explorer. |
| `no_auth` | Trigger this method without invoking authentication even if it is required. |
###### `def delete_collection_items(collection_id_or_slug_name_or_db_schema_name: str, delete_items_request: dnastack.client.collections.model.DeleteCollectionItemRequest, trace: Optional[dnastack.common.tracing.Span])`
Delete items from a collection
###### `def get(id_or_slug_name: str, no_auth: bool, trace: Optional[dnastack.common.tracing.Span]) -> dnastack.client.collections.model.Collection`
Get a collection by ID or slug name
###### `@staticmethod def get_adapter_type() -> str`
Get the descriptive adapter type
###### `def get_collection_status(collection_id_or_slug_name_or_db_schema_name: str, trace: Optional[dnastack.common.tracing.Span]) -> dnastack.client.collections.model.CollectionStatus`
Get the status of a collection
###### `@staticmethod def get_supported_service_types() -> List[dnastack.client.service_registry.models.ServiceType]`
The list of supported service types

The first one is always regarded as the default type.
###### `def list_collection_items(collection_id_or_slug_name_or_db_schema_name: str, list_options: Optional[dnastack.client.collections.model.CollectionItemListOptions], max_results: Optional[int], trace: Optional[dnastack.common.tracing.Span]) -> Iterator[dnastack.client.collections.model.CollectionItem]`
List all items in a collection
###### `def list_collections(no_auth: bool, trace: Optional[dnastack.common.tracing.Span]) -> List[dnastack.client.collections.model.Collection]`
List all available collections
###### `@staticmethod def make(endpoint: dnastack.client.models.ServiceEndpoint)`
Create this class with the given `endpoint`.
#### Class `dnastack.client.collections.model.Collection(id: Optional[str], name: str, slugName: str, metadata: Optional[Dict[str, Any]], description: Optional[str], itemsQuery: Optional[str], tags: Optional[List[dnastack.client.collections.model.Tag]], createdAt: Optional[datetime.datetime], updatedAt: Optional[datetime.datetime], dbSchemaName: Optional[str], itemsChangedAt: Optional[datetime.datetime], latestItemUpdatedTime: Optional[datetime.datetime], accessTypeLabels: Optional[Dict[str, str]], itemCounts: Optional[Dict[str, int]])`
A model representing a collection

.. note:: This is not a full representation of the object.
##### Properties
###### `id: Optional[str]`

###### `name: str`

###### `slugName: str`

###### `metadata: Optional[Dict[str, Any]]`

###### `description: Optional[str]`

###### `itemsQuery: Optional[str]`

###### `tags: Optional[List[dnastack.client.collections.model.Tag]]`

###### `createdAt: Optional[datetime.datetime]`

###### `updatedAt: Optional[datetime.datetime]`

###### `dbSchemaName: Optional[str]`

###### `itemsChangedAt: Optional[datetime.datetime]`

###### `latestItemUpdatedTime: Optional[datetime.datetime]`

###### `accessTypeLabels: Optional[Dict[str, str]]`

###### `itemCounts: Optional[Dict[str, int]]`

##### Methods
###### `@staticmethod def construct(_fields_set: Optional['SetStr'], **values) -> 'Model'`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], update: Optional['DictStrAny'], deep: bool) -> 'Model'`
Duplicate a model, optionally choose which fields to include, exclude and change.

    the new model: you should trust this data

| Parameter | Description |
| --- | --- |
| `include` | fields to include in new model |
| `exclude` | fields to exclude from new model, as with values this takes precedence over include |
| `update` | values to change/add in the new model. Note: the data is not validated before creating |
| `deep` | set to `True` to make a deep copy of the model |

| Return |
| --- |
| new model instance |
###### `def dict(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> 'DictStrAny'`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Optional[Callable[[Any], Any]], models_as_dict: bool= True, **dumps_kwargs) -> str`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.client.data_connect.DataConnectClient(endpoint: dnastack.client.models.ServiceEndpoint)`
A Client for the GA4GH Data Connect standard
##### Properties
###### `endpoint`

###### `events`

###### `url`
The base URL to the endpoint
##### Methods
###### `def create_http_session(suppress_error: bool, no_auth: bool) -> dnastack.http.session.HttpSession`
Create HTTP session wrapper
###### `@staticmethod def get_adapter_type() -> str`
Get the descriptive adapter type
###### `@staticmethod def get_supported_service_types() -> List[dnastack.client.service_registry.models.ServiceType]`
The list of supported service types

The first one is always regarded as the default type.
###### `def iterate_tables(no_auth: bool) -> Iterator[dnastack.client.data_connect.TableInfo]`
Iterate the list of tables
###### `def list_tables(no_auth: bool) -> List[dnastack.client.data_connect.TableInfo]`
List all tables
###### `@staticmethod def make(endpoint: dnastack.client.models.ServiceEndpoint)`
Create this class with the given `endpoint`.
###### `def query(query: str, no_auth: bool, trace: Optional[dnastack.common.tracing.Span]) -> Iterator[Dict[str, Any]]`
Run an SQL query
###### `def table(table: Union[dnastack.client.data_connect.TableInfo, dnastack.client.data_connect.Table, str], no_auth: bool) -> dnastack.client.data_connect.Table`
Get the table wrapper
#### Class `dnastack.client.data_connect.Table(table_name: str, url: str, http_session: Optional[dnastack.http.session.HttpSession])`
Table API Wrapper 
##### Properties
###### `data`
The iterator to the data in the table
###### `info`
The information of the table, such as schema
###### `name`
The name of the table
#### Class `dnastack.client.data_connect.TableInfo(name: str, description: Optional[str], data_model: Optional[Dict[str, Any]], errors: Optional[List[dnastack.client.data_connect.Error]])`
Table metadata 
##### Properties
###### `name: str`

###### `description: Optional[str]`

###### `data_model: Optional[Dict[str, Any]]`

###### `errors: Optional[List[dnastack.client.data_connect.Error]]`

##### Methods
###### `@staticmethod def construct(_fields_set: Optional['SetStr'], **values) -> 'Model'`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], update: Optional['DictStrAny'], deep: bool) -> 'Model'`
Duplicate a model, optionally choose which fields to include, exclude and change.

    the new model: you should trust this data

| Parameter | Description |
| --- | --- |
| `include` | fields to include in new model |
| `exclude` | fields to exclude from new model, as with values this takes precedence over include |
| `update` | values to change/add in the new model. Note: the data is not validated before creating |
| `deep` | set to `True` to make a deep copy of the model |

| Return |
| --- |
| new model instance |
###### `def dict(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> 'DictStrAny'`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Optional[Callable[[Any], Any]], models_as_dict: bool= True, **dumps_kwargs) -> str`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.client.drs.DrsClient(endpoint: dnastack.client.models.ServiceEndpoint)`
Client for Data Repository Service
##### Properties
###### `endpoint`

###### `events`

###### `url`
The base URL to the endpoint
##### Methods
###### `def create_http_session(suppress_error: bool, no_auth: bool) -> dnastack.http.session.HttpSession`
Create HTTP session wrapper
###### `def exit_download(url: str, status: dnastack.client.drs.DownloadStatus, message: str, exit_codes: dict)`
Report a file download with a status and message


| Parameter | Description |
| --- | --- |
| `url` | The downloaded resource's url |
| `status` | The reported status of the download |
| `message` | A message describing the reason for setting the status |
| `exit_codes` | A shared dict for all reports used by download_files |
###### `@staticmethod def get_adapter_type()`
Get the descriptive adapter type
###### `@staticmethod def get_supported_service_types() -> List[dnastack.client.service_registry.models.ServiceType]`
The list of supported service types

The first one is always regarded as the default type.
###### `@staticmethod def make(endpoint: dnastack.client.models.ServiceEndpoint)`
Create this class with the given `endpoint`.
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
#### Class `dnastack.client.explorer.models.FederatedQuestion(id: str, name: str, description: str, params: List[dnastack.client.explorer.models.QuestionParam], collections: List[dnastack.client.explorer.models.QuestionCollection])`
A federated question that can be asked across multiple collections.

Based on the Java FederatedQuestion record from the Explorer service.
##### Properties
###### `id: str`

###### `name: str`

###### `description: str`

###### `params: List[dnastack.client.explorer.models.QuestionParam]`

###### `collections: List[dnastack.client.explorer.models.QuestionCollection]`

##### Methods
###### `@staticmethod def construct(_fields_set: Optional['SetStr'], **values) -> 'Model'`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], update: Optional['DictStrAny'], deep: bool) -> 'Model'`
Duplicate a model, optionally choose which fields to include, exclude and change.

    the new model: you should trust this data

| Parameter | Description |
| --- | --- |
| `include` | fields to include in new model |
| `exclude` | fields to exclude from new model, as with values this takes precedence over include |
| `update` | values to change/add in the new model. Note: the data is not validated before creating |
| `deep` | set to `True` to make a deep copy of the model |

| Return |
| --- |
| new model instance |
###### `def dict(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> 'DictStrAny'`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Optional[Callable[[Any], Any]], models_as_dict: bool= True, **dumps_kwargs) -> str`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.client.explorer.models.QuestionCollection(id: str, slug: str, name: str, questionId: str)`
A collection reference within a federated question.
##### Properties
###### `id: str`

###### `slug: str`

###### `name: str`

###### `question_id: str`

##### Methods
###### `@staticmethod def construct(_fields_set: Optional['SetStr'], **values) -> 'Model'`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], update: Optional['DictStrAny'], deep: bool) -> 'Model'`
Duplicate a model, optionally choose which fields to include, exclude and change.

    the new model: you should trust this data

| Parameter | Description |
| --- | --- |
| `include` | fields to include in new model |
| `exclude` | fields to exclude from new model, as with values this takes precedence over include |
| `update` | values to change/add in the new model. Note: the data is not validated before creating |
| `deep` | set to `True` to make a deep copy of the model |

| Return |
| --- |
| new model instance |
###### `def dict(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> 'DictStrAny'`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Optional[Callable[[Any], Any]], models_as_dict: bool= True, **dumps_kwargs) -> str`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.client.explorer.models.QuestionParam(id: str, name: str, label: str, inputType: str, description: Optional[str], required: bool, defaultValue: Optional[str], testValue: Optional[str], inputSubtype: Optional[str], allowedValues: Optional[str], table: Optional[str], column: Optional[str], values: Optional[str])`
A parameter definition for a question.

Based on the Java QuestionParam class from the Explorer service.
##### Properties
###### `id: str`

###### `name: str`

###### `label: str`

###### `input_type: str`

###### `description: Optional[str]`

###### `required: bool`

###### `default_value: Optional[str]`

###### `test_value: Optional[str]`

###### `input_subtype: Optional[str]`

###### `allowed_values: Optional[str]`

###### `table: Optional[str]`

###### `column: Optional[str]`

###### `values: Optional[str]`

##### Methods
###### `@staticmethod def construct(_fields_set: Optional['SetStr'], **values) -> 'Model'`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], update: Optional['DictStrAny'], deep: bool) -> 'Model'`
Duplicate a model, optionally choose which fields to include, exclude and change.

    the new model: you should trust this data

| Parameter | Description |
| --- | --- |
| `include` | fields to include in new model |
| `exclude` | fields to exclude from new model, as with values this takes precedence over include |
| `update` | values to change/add in the new model. Note: the data is not validated before creating |
| `deep` | set to `True` to make a deep copy of the model |

| Return |
| --- |
| new model instance |
###### `def dict(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> 'DictStrAny'`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Optional[Callable[[Any], Any]], models_as_dict: bool= True, **dumps_kwargs) -> str`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.client.service_registry.client.ServiceListingError()`
Raised when the service listing encounters error 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.client.service_registry.client.ServiceRegistry(endpoint: dnastack.client.models.ServiceEndpoint)`
The base class for all DNAStack Clients 
##### Properties
###### `endpoint`

###### `events`

###### `url`
The base URL to the endpoint
##### Methods
###### `def create_http_session(suppress_error: bool, no_auth: bool) -> dnastack.http.session.HttpSession`
Create HTTP session wrapper
###### `@staticmethod def get_adapter_type() -> str`
Get the descriptive adapter type
###### `@staticmethod def get_supported_service_types() -> List[dnastack.client.service_registry.models.ServiceType]`
The list of supported service types

The first one is always regarded as the default type.
###### `@staticmethod def make(endpoint: dnastack.client.models.ServiceEndpoint)`
Create this class with the given `endpoint`.
#### Class `dnastack.client.service_registry.factory.ClientFactory(registries: List[dnastack.client.service_registry.client.ServiceRegistry])`
Service Client Factory using Service Registries 
##### Methods
###### `def find_services(url: Optional[str], types: Optional[List[dnastack.client.service_registry.models.ServiceType]], exact_match: bool= True) -> Iterable[dnastack.client.service_registry.models.Service]`
Find GA4GH services
###### `@staticmethod def use(*service_registry_endpoints)`
.. note:: This only works with public registries.
#### Class `dnastack.client.service_registry.factory.UnregisteredServiceEndpointError(services: Iterable[dnastack.client.service_registry.models.Service])`
Raised when the requested service endpoint is not registered 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.client.service_registry.factory.UnsupportedClientClassError(cls: Type)`
Raised when the given client class is not supported 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.client.service_registry.models.Organization(name: str, url: str)`
Organization 
##### Properties
###### `name: str`

###### `url: str`

##### Methods
###### `@staticmethod def construct(_fields_set: Optional['SetStr'], **values) -> 'Model'`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], update: Optional['DictStrAny'], deep: bool) -> 'Model'`
Duplicate a model, optionally choose which fields to include, exclude and change.

    the new model: you should trust this data

| Parameter | Description |
| --- | --- |
| `include` | fields to include in new model |
| `exclude` | fields to exclude from new model, as with values this takes precedence over include |
| `update` | values to change/add in the new model. Note: the data is not validated before creating |
| `deep` | set to `True` to make a deep copy of the model |

| Return |
| --- |
| new model instance |
###### `def dict(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> 'DictStrAny'`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Optional[Callable[[Any], Any]], models_as_dict: bool= True, **dumps_kwargs) -> str`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.client.service_registry.models.Service(id: str, name: str, type: dnastack.client.service_registry.models.ServiceType, url: Optional[str], description: Optional[str], organization: Optional[dnastack.client.service_registry.models.Organization], contactUrl: Optional[str], documentationUrl: Optional[str], createdAt: Optional[str], updatedAt: Optional[str], environment: Optional[str], version: Optional[str], authentication: Optional[List[Dict[str, Any]]])`
GA4GH Service

* https://github.com/ga4gh-discovery/ga4gh-service-registry/blob/develop/service-registry.yaml#/components/schemas/ExternalService
* https://raw.githubusercontent.com/ga4gh-discovery/ga4gh-service-info/v1.0.0/service-info.yaml#/components/schemas/Service
##### Properties
###### `id: str`

###### `name: str`

###### `type: ServiceType`

###### `url: Optional[str]`

###### `description: Optional[str]`

###### `organization: Optional[dnastack.client.service_registry.models.Organization]`

###### `contactUrl: Optional[str]`

###### `documentationUrl: Optional[str]`

###### `createdAt: Optional[str]`

###### `updatedAt: Optional[str]`

###### `environment: Optional[str]`

###### `version: Optional[str]`

###### `authentication: Optional[List[Dict[str, Any]]]`

##### Methods
###### `@staticmethod def construct(_fields_set: Optional['SetStr'], **values) -> 'Model'`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], update: Optional['DictStrAny'], deep: bool) -> 'Model'`
Duplicate a model, optionally choose which fields to include, exclude and change.

    the new model: you should trust this data

| Parameter | Description |
| --- | --- |
| `include` | fields to include in new model |
| `exclude` | fields to exclude from new model, as with values this takes precedence over include |
| `update` | values to change/add in the new model. Note: the data is not validated before creating |
| `deep` | set to `True` to make a deep copy of the model |

| Return |
| --- |
| new model instance |
###### `def dict(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> 'DictStrAny'`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Optional[Callable[[Any], Any]], models_as_dict: bool= True, **dumps_kwargs) -> str`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.client.service_registry.models.ServiceType(group: str, artifact: str, version: str)`
GA4GH Service Type

https://raw.githubusercontent.com/ga4gh-discovery/ga4gh-service-info/v1.0.0/service-info.yaml#/components/schemas/ServiceType
##### Properties
###### `group: str`

###### `artifact: str`

###### `version: str`

##### Methods
###### `@staticmethod def construct(_fields_set: Optional['SetStr'], **values) -> 'Model'`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], update: Optional['DictStrAny'], deep: bool) -> 'Model'`
Duplicate a model, optionally choose which fields to include, exclude and change.

    the new model: you should trust this data

| Parameter | Description |
| --- | --- |
| `include` | fields to include in new model |
| `exclude` | fields to exclude from new model, as with values this takes precedence over include |
| `update` | values to change/add in the new model. Note: the data is not validated before creating |
| `deep` | set to `True` to make a deep copy of the model |

| Return |
| --- |
| new model instance |
###### `def dict(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> 'DictStrAny'`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Optional[Callable[[Any], Any]], models_as_dict: bool= True, **dumps_kwargs) -> str`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.configuration.exceptions.ConfigurationError()`
General Error. 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.configuration.exceptions.MissingEndpointError()`
Raised when a request endpoint is not registered. 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.configuration.exceptions.UnknownClientShortTypeError()`
Raised when a given short service type is not recognized 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.configuration.manager.ConfigurationManager(file_path: str)`
##### Methods
###### `def load() -> dnastack.configuration.models.Configuration`
Load the configuration object
###### `def load_raw() -> str`
Load the raw configuration content
###### `@staticmethod def migrate(configuration: dnastack.configuration.models.Configuration) -> dnastack.configuration.models.Configuration`
Perform on-line migration on the Configuration object.
###### `@staticmethod def migrate_endpoint(endpoint: dnastack.client.models.ServiceEndpoint) -> dnastack.client.models.ServiceEndpoint`
Perform on-line migration on the ServiceEndpoint object.
###### `def save(configuration: dnastack.configuration.models.Configuration)`
Save the configuration object
#### Class `dnastack.configuration.wrapper.ConfigurationWrapper(configuration: dnastack.configuration.models.Configuration, context_name: Optional[str])`
##### Properties
###### `current_context`

###### `defaults`

###### `endpoints`

###### `original`

##### Methods
#### Class `dnastack.configuration.wrapper.UnsupportedModelVersionError()`
Unspecified run-time error.
##### Properties
###### `args`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.http.session.AuthenticationError()`
Authentication Error 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.http.session.HttpError(response: requests.models.Response, trace_context: Optional[dnastack.common.tracing.Span])`
Unspecified run-time error.
##### Properties
###### `args`

###### `response`

###### `trace`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.http.session.HttpSession(uuid: Optional[str], authenticators: List[dnastack.http.authenticators.abstract.Authenticator], suppress_error: bool= True, enable_auth: bool= True, session: Optional[requests.sessions.Session])`
An abstract base class for context managers.
##### Properties
###### `authenticators`

###### `events`

##### Methods
#### Class `dnastack.http.session_info.BaseSessionStorage()`
Base Storage Adapter for Session Information Manager

It requires the implementations of `__contains__` for `in` operand, `__getitem__`, `__setitem__`, and `__delitem__`
for dictionary-like API.
#### Class `dnastack.http.session_info.FileSessionStorage(dir_path: str)`
Filesystem Storage Adapter for Session Information Manager

This is used by default.
#### Class `dnastack.http.session_info.InMemorySessionStorage()`
In-memory Storage Adapter for Session Information Manager

This is for testing.
#### Class `dnastack.http.session_info.SessionInfo(model_version: float= 3.0, config_hash: Optional[str], access_token: Optional[str], refresh_token: Optional[str], scope: Optional[str], token_type: str, handler: Optional[dnastack.http.session_info.SessionInfoHandler], issued_at: int, valid_until: int)`
##### Properties
###### `dnastack_schema_version: float`

###### `config_hash: Optional[str]`

###### `access_token: Optional[str]`

###### `refresh_token: Optional[str]`

###### `scope: Optional[str]`

###### `token_type: str`

###### `handler: Optional[dnastack.http.session_info.SessionInfoHandler]`

###### `issued_at: int`

###### `valid_until: int`

##### Methods
###### `@staticmethod def construct(_fields_set: Optional['SetStr'], **values) -> 'Model'`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], update: Optional['DictStrAny'], deep: bool) -> 'Model'`
Duplicate a model, optionally choose which fields to include, exclude and change.

    the new model: you should trust this data

| Parameter | Description |
| --- | --- |
| `include` | fields to include in new model |
| `exclude` | fields to exclude from new model, as with values this takes precedence over include |
| `update` | values to change/add in the new model. Note: the data is not validated before creating |
| `deep` | set to `True` to make a deep copy of the model |

| Return |
| --- |
| new model instance |
###### `def dict(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> 'DictStrAny'`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Optional[Callable[[Any], Any]], models_as_dict: bool= True, **dumps_kwargs) -> str`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.http.session_info.SessionInfoHandler(auth_info: Dict[str, Any])`
##### Properties
###### `auth_info: Dict[str, Any]`

##### Methods
###### `@staticmethod def construct(_fields_set: Optional['SetStr'], **values) -> 'Model'`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], update: Optional['DictStrAny'], deep: bool) -> 'Model'`
Duplicate a model, optionally choose which fields to include, exclude and change.

    the new model: you should trust this data

| Parameter | Description |
| --- | --- |
| `include` | fields to include in new model |
| `exclude` | fields to exclude from new model, as with values this takes precedence over include |
| `update` | values to change/add in the new model. Note: the data is not validated before creating |
| `deep` | set to `True` to make a deep copy of the model |

| Return |
| --- |
| new model instance |
###### `def dict(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> 'DictStrAny'`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], exclude: Optional[Union['AbstractSetIntStr', 'MappingIntStrAny']], by_alias: bool, skip_defaults: Optional[bool], exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Optional[Callable[[Any], Any]], models_as_dict: bool= True, **dumps_kwargs) -> str`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.http.session_info.SessionManager(storage: dnastack.http.session_info.BaseSessionStorage, static_session: Optional[str], static_session_file: Optional[str])`
Session Information Manager 
##### Methods
#### Class `dnastack.http.session_info.UnknownSessionError()`
Raised when an unknown session is requested 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def add_note()`
Exception.add_note(note) --
add a note to the exception
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.