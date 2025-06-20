---
title: "API Reference (v3)"
weight: 1
draft: false
lastmod: 2022-05-18
type: docs
layout: single-col
---

This API reference is only for dnastack-client-library 3.x.
#### Class `dnastack.client.collections.client.CollectionServiceClient(endpoint: dnastack.configuration.models.ServiceEndpoint)`
Client for Collection API
##### Properties
###### `endpoint`

###### `url`
The base URL to the endpoint
##### Methods
###### `def create_http_session(suppress_error: bool= True) -> dnastack.http.session.HttpSession`
Create HTTP session wrapper
###### `def data_connect_endpoint(collection: Union[str, dnastack.client.collections.model.Collection, NoneType]) -> dnastack.configuration.models.ServiceEndpoint`
Get the URL to the corresponding Data Connect endpoint


| Parameter | Description |
| --- | --- |
| `collection` | The collection or collection ID. It is optional and only used by the explorer. |
###### `def get(id_or_slug_name: str) -> dnastack.client.collections.model.Collection`
Get a collection by ID or slug name
###### `@staticmethod def get_adapter_type() -> str`
Get the descriptive adapter type
###### `@staticmethod def get_supported_service_types() -> List[dnastack.client.service_registry.models.ServiceType]`
The list of supported service types

The first one is always regarded as the default type.
###### `def list_collections() -> List[dnastack.client.collections.model.Collection]`
List all available collections
###### `@staticmethod def make(endpoint: dnastack.configuration.models.ServiceEndpoint)`
Create this class with the given `endpoint`.
#### Class `dnastack.client.collections.model.Collection(id: str, name: str, slugName: str, description: str, itemsQuery: str)`
A model representing a collection

.. note:: This is not a full representation of the object.
##### Properties
###### `id: Union[str, NoneType]`

###### `name: str`

###### `slugName: str`

###### `description: Union[str, NoneType]`

###### `itemsQuery: str`

##### Methods
###### `@staticmethod def construct(_fields_set: Union[ForwardRef('SetStr'), NoneType], **values) -> Model`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], update: DictStrAny, deep: bool) -> Model`
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
###### `def dict(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> DictStrAny`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Union[Callable[[Any], Any], NoneType], models_as_dict: bool= True, **dumps_kwargs) -> unicode`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.client.data_connect.DataConnectClient(endpoint: dnastack.configuration.models.ServiceEndpoint)`
A Client for the GA4GH Data Connect standard
##### Properties
###### `endpoint`

###### `url`
The base URL to the endpoint
##### Methods
###### `def create_http_session(suppress_error: bool= True) -> dnastack.http.session.HttpSession`
Create HTTP session wrapper
###### `@staticmethod def get_adapter_type() -> str`
Get the descriptive adapter type
###### `@staticmethod def get_supported_service_types() -> List[dnastack.client.service_registry.models.ServiceType]`
The list of supported service types

The first one is always regarded as the default type.
###### `def get_table(table: Union[dnastack.client.data_connect.Table, dnastack.client.data_connect.TableWrapper, str]) -> dnastack.client.data_connect.Table`
Get the table metadata
###### `def iterate_tables() -> Iterator[dnastack.client.data_connect.Table]`
Iterate the list of tables
###### `def list_tables() -> List[dnastack.client.data_connect.Table]`
List all tables
###### `@staticmethod def make(endpoint: dnastack.configuration.models.ServiceEndpoint)`
Create this class with the given `endpoint`.
###### `def query(query: str) -> Iterator[Dict[str, Any]]`
Run an SQL query
###### `def table(table: Union[dnastack.client.data_connect.Table, dnastack.client.data_connect.TableWrapper, str]) -> dnastack.client.data_connect.TableWrapper`
Get the table wrapper
#### Class `dnastack.client.data_connect.Table(name: str, description: str, data_model: Dict[str, Any], errors: List[dnastack.client.data_connect.Error])`
Table metadata 
##### Properties
###### `name: str`

###### `description: Union[str, NoneType]`

###### `data_model: Union[Dict[str, Any], NoneType]`

###### `errors: Union[List[dnastack.client.data_connect.Error], NoneType]`

##### Methods
###### `@staticmethod def construct(_fields_set: Union[ForwardRef('SetStr'), NoneType], **values) -> Model`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], update: DictStrAny, deep: bool) -> Model`
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
###### `def dict(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> DictStrAny`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Union[Callable[[Any], Any], NoneType], models_as_dict: bool= True, **dumps_kwargs) -> unicode`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.client.data_connect.TableWrapper(table_name: str, url: str, http_session: Union[dnastack.http.session.HttpSession, NoneType])`
Table API Wrapper 
##### Properties
###### `data`
The iterator to the data in the table
###### `info`
The information of the table, such as schema
###### `name`
The name of the table
#### Class `dnastack.client.drs.DrsClient(endpoint: dnastack.configuration.models.ServiceEndpoint)`
Client for Data Repository Service
##### Properties
###### `endpoint`

###### `url`
The base URL to the endpoint
##### Methods
###### `def create_http_session(suppress_error: bool= True) -> dnastack.http.session.HttpSession`
Create HTTP session wrapper
###### `def download_file(url: str, output_dir: str, display_progress_bar: bool, output_buffer_list: Union[list, NoneType], exit_codes: Union[dict, NoneType])`
Download a single DRS resource and output to a file or list


| Parameter | Description |
| --- | --- |
| `url` | The DRS resource url to download |
| `output_dir` | The directory to download output to. |
| `display_progress_bar` | Display a progress bar for the downloads to standard output |
| `output_buffer_list` | If specified, output downloaded data to the list specified in the argument |
| `exit_codes` | A shared dictionary of the exit statuses and messages |
###### `def download_files(urls: List[str], output_dir: str= "/Users/jnopporn/Projects/dnastack/dnastack-client-library", display_progress_bar: bool, parallel_download: bool= True, out: List)`
Download a list of files and output either to files in the current directory or dump to a specified list

:raises: DRSDownloadException if one or more of the downloads fail

| Parameter | Description |
| --- | --- |
| `urls` | A list of DRS resource urls to download |
| `output_dir` | The directory to download output to. |
| `display_progress_bar` | Display a progress bar for the downloads to standard output |
| `out` | If specified, output downloaded data to the list specified in the argument |
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
###### `def get_download_url(drs_url: str) -> Union[str, NoneType]`
Get the URL to download the DRS object
###### `@staticmethod def get_supported_service_types() -> List[dnastack.client.service_registry.models.ServiceType]`
The list of supported service types

The first one is always regarded as the default type.
###### `@staticmethod def make(endpoint: dnastack.configuration.models.ServiceEndpoint)`
Create this class with the given `endpoint`.
#### Class `dnastack.client.service_registry.client.ServiceListingError()`
Raised when the service listing encounters error 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.client.service_registry.client.ServiceRegistry(endpoint: dnastack.configuration.models.ServiceEndpoint)`
The base class for all DNAStack Clients 
##### Properties
###### `endpoint`

###### `url`
The base URL to the endpoint
##### Methods
###### `def create_http_session(suppress_error: bool= True) -> dnastack.http.session.HttpSession`
Create HTTP session wrapper
###### `@staticmethod def get_adapter_type() -> str`
Get the descriptive adapter type
###### `@staticmethod def get_supported_service_types() -> List[dnastack.client.service_registry.models.ServiceType]`
The list of supported service types

The first one is always regarded as the default type.
###### `@staticmethod def make(endpoint: dnastack.configuration.models.ServiceEndpoint)`
Create this class with the given `endpoint`.
#### Class `dnastack.client.service_registry.factory.ClientFactory(registries: List[dnastack.client.service_registry.client.ServiceRegistry])`
Service Client Factory using Service Registries 
##### Methods
###### `def find_services(url: Union[str, NoneType], types: Union[List[dnastack.client.service_registry.models.ServiceType], NoneType], exact_match: bool= True) -> Iterable[dnastack.client.service_registry.models.Service]`
Find GA4GH services
###### `@staticmethod def use(*service_registry_endpoints)`
.. note:: This only works with public registries.
#### Class `dnastack.client.service_registry.factory.UnregisteredServiceEndpointError(services: Iterable[dnastack.client.service_registry.models.Service])`
Raised when the requested service endpoint is not registered 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.client.service_registry.factory.UnsupportedClientClassError(cls: Type)`
Raised when the given client class is not supported 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.client.service_registry.models.Organization(name: str, url: str)`
Organization 
##### Properties
###### `name: str`

###### `url: str`

##### Methods
###### `@staticmethod def construct(_fields_set: Union[ForwardRef('SetStr'), NoneType], **values) -> Model`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], update: DictStrAny, deep: bool) -> Model`
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
###### `def dict(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> DictStrAny`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Union[Callable[[Any], Any], NoneType], models_as_dict: bool= True, **dumps_kwargs) -> unicode`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.client.service_registry.models.Service(id: str, name: str, type: dnastack.client.service_registry.models.ServiceType, url: str, description: str, organization: dnastack.client.service_registry.models.Organization, contactUrl: str, documentationUrl: str, createdAt: str, updatedAt: str, environment: str, version: str, authentication: List[Dict[str, Any]])`
GA4GH Service

* https://github.com/ga4gh-discovery/ga4gh-service-registry/blob/develop/service-registry.yaml#/components/schemas/ExternalService
* https://raw.githubusercontent.com/ga4gh-discovery/ga4gh-service-info/v1.0.0/service-info.yaml#/components/schemas/Service
##### Properties
###### `id: str`

###### `name: str`

###### `type: ServiceType`

###### `url: str`

###### `description: Union[str, NoneType]`

###### `organization: Organization`

###### `contactUrl: Union[str, NoneType]`

###### `documentationUrl: Union[str, NoneType]`

###### `createdAt: Union[str, NoneType]`

###### `updatedAt: Union[str, NoneType]`

###### `environment: Union[str, NoneType]`

###### `version: str`

###### `authentication: Union[List[Dict[str, Any]], NoneType]`

##### Methods
###### `@staticmethod def construct(_fields_set: Union[ForwardRef('SetStr'), NoneType], **values) -> Model`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], update: DictStrAny, deep: bool) -> Model`
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
###### `def dict(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> DictStrAny`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Union[Callable[[Any], Any], NoneType], models_as_dict: bool= True, **dumps_kwargs) -> unicode`
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
###### `@staticmethod def construct(_fields_set: Union[ForwardRef('SetStr'), NoneType], **values) -> Model`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], update: DictStrAny, deep: bool) -> Model`
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
###### `def dict(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> DictStrAny`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Union[Callable[[Any], Any], NoneType], models_as_dict: bool= True, **dumps_kwargs) -> unicode`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.configuration.exceptions.ConfigurationError()`
General Error. 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.configuration.exceptions.MissingEndpointError()`
Raised when a request endpoint is not registered. 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.configuration.exceptions.UnknownClientShortTypeError()`
Raised when a given short service type is not recognized 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.configuration.manager.ConfigurationManager(file_path: str)`
##### Methods
###### `def load() -> dnastack.configuration.models.Configuration`
Load the configuration object
###### `def load_raw() -> str`
Load the raw configuration content
###### `def load_then_save() -> AbstractContextManager[dnastack.configuration.wrapper.ConfigurationWrapper]`
Load the configuration wrapper in a context and save it on exit
###### `def load_wrapper() -> dnastack.configuration.wrapper.ConfigurationWrapper`
Load the configuration wrapper
###### `def save(configuration: dnastack.configuration.models.Configuration)`
Save the configuration object
#### Class `dnastack.configuration.models.Configuration(version: float= 3, defaults: Dict[str, str], endpoints: List[dnastack.configuration.models.ServiceEndpoint])`
Configuration (v3)
##### Properties
###### `version: float`

###### `defaults: Dict[str, str]`

###### `endpoints: List[dnastack.configuration.models.ServiceEndpoint]`

##### Methods
###### `@staticmethod def construct(_fields_set: Union[ForwardRef('SetStr'), NoneType], **values) -> Model`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], update: DictStrAny, deep: bool) -> Model`
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
###### `def dict(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> DictStrAny`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Union[Callable[[Any], Any], NoneType], models_as_dict: bool= True, **dumps_kwargs) -> unicode`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.configuration.models.OAuth2Authentication(authorization_endpoint: str, client_id: str, client_secret: str, device_code_endpoint: str, grant_type: str, personal_access_endpoint: str, personal_access_email: str, personal_access_token: str, redirect_url: str, resource_url: str, scope: str, token_endpoint: str, type: str= "oauth2")`
OAuth2 Authentication Information
##### Properties
###### `authorization_endpoint: Union[str, NoneType]`

###### `client_id: Union[str, NoneType]`

###### `client_secret: Union[str, NoneType]`

###### `device_code_endpoint: Union[str, NoneType]`

###### `grant_type: str`

###### `personal_access_endpoint: Union[str, NoneType]`

###### `personal_access_email: Union[str, NoneType]`

###### `personal_access_token: Union[str, NoneType]`

###### `redirect_url: Union[str, NoneType]`

###### `resource_url: str`

###### `scope: Union[str, NoneType]`

###### `token_endpoint: Union[str, NoneType]`

###### `type: str`

##### Methods
###### `@staticmethod def construct(_fields_set: Union[ForwardRef('SetStr'), NoneType], **values) -> Model`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], update: DictStrAny, deep: bool) -> Model`
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
###### `def dict(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> DictStrAny`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Union[Callable[[Any], Any], NoneType], models_as_dict: bool= True, **dumps_kwargs) -> unicode`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.configuration.models.ServiceEndpoint(model_version: float= 2.0, id: str= "ac258324-04a3-48ab-9574-32b4488d99cf", adapter_type: str, authentication: Dict[str, Any], fallback_authentications: List[Dict[str, Any]], type: dnastack.client.service_registry.models.ServiceType, url: str, mode: str, source: dnastack.configuration.models.EndpointSource)`
API Service Endpoint
##### Properties
###### `model_version: float`

###### `id: str`

###### `adapter_type: Union[str, NoneType]`

###### `authentication: Union[Dict[str, Any], NoneType]`

###### `fallback_authentications: Union[List[Dict[str, Any]], NoneType]`

###### `type: Union[dnastack.client.service_registry.models.ServiceType, NoneType]`

###### `url: str`

###### `mode: Union[str, NoneType]`

###### `source: Union[dnastack.configuration.models.EndpointSource, NoneType]`

##### Methods
###### `@staticmethod def construct(_fields_set: Union[ForwardRef('SetStr'), NoneType], **values) -> Model`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], update: DictStrAny, deep: bool) -> Model`
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
###### `def dict(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> DictStrAny`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def get_authentications() -> List[Dict[str, Any]]`
Get the list of authentication information
###### `def json(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Union[Callable[[Any], Any], NoneType], models_as_dict: bool= True, **dumps_kwargs) -> unicode`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.configuration.wrapper.ConfigurationWrapper(configuration: dnastack.configuration.models.Configuration)`
##### Properties
###### `endpoints`

###### `original`

##### Methods
#### Class `dnastack.configuration.wrapper.UnsupportedModelVersionError()`
Unspecified run-time error.
##### Properties
###### `args`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.helpers.client_factory.ConfigurationBasedClientFactory(config_manager: dnastack.configuration.manager.ConfigurationManager)`
Configuration-based Client Factory

This class will provide a service client based on the CLI configuration.
##### Methods
#### Class `dnastack.helpers.client_factory.ServiceEndpointNotFound()`
Raised when the requested service endpoint is not found 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.helpers.client_factory.UnknownAdapterTypeError()`
Raised when the given service adapter/short type is not registered or supported 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.helpers.client_factory.UnknownClientShortTypeError()`
Raised when a given short service type is not recognized 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.http.session.AuthenticationError()`
Authentication Error 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.http.session.HttpError(response: requests.models.Response)`
Unspecified run-time error.
##### Properties
###### `args`

###### `response`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.
#### Class `dnastack.http.session.HttpSession(authenticators: List[dnastack.http.authenticators.abstract.Authenticator], suppress_error: bool= True)`
An abstract base class for context managers.
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
#### Class `dnastack.http.session_info.SessionInfo(model_version: int= 3, config_hash: str, access_token: str, refresh_token: str, scope: str, token_type: str, handler: dnastack.http.session_info.SessionInfoHandler, issued_at: int, valid_until: int)`
##### Properties
###### `model_version: int`

###### `config_hash: Union[str, NoneType]`

###### `access_token: Union[str, NoneType]`

###### `refresh_token: Union[str, NoneType]`

###### `scope: Union[str, NoneType]`

###### `token_type: str`

###### `handler: Union[dnastack.http.session_info.SessionInfoHandler, NoneType]`

###### `issued_at: int`

###### `valid_until: int`

##### Methods
###### `@staticmethod def construct(_fields_set: Union[ForwardRef('SetStr'), NoneType], **values) -> Model`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], update: DictStrAny, deep: bool) -> Model`
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
###### `def dict(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> DictStrAny`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Union[Callable[[Any], Any], NoneType], models_as_dict: bool= True, **dumps_kwargs) -> unicode`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.http.session_info.SessionInfoHandler(auth_info: Dict[str, Any])`
##### Properties
###### `auth_info: Dict[str, Any]`

##### Methods
###### `@staticmethod def construct(_fields_set: Union[ForwardRef('SetStr'), NoneType], **values) -> Model`
Creates a new model setting __dict__ and __fields_set__ from trusted or pre-validated data.
Default values are respected, but no other validation is performed.
Behaves as if `Config.extra = 'allow'` was set since it adds all passed values
###### `def copy(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], update: DictStrAny, deep: bool) -> Model`
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
###### `def dict(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool) -> DictStrAny`
Generate a dictionary representation of the model, optionally specifying which fields to include or exclude.
###### `def json(include: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], exclude: Union[ForwardRef('AbstractSetIntStr'), ForwardRef('MappingIntStrAny')], by_alias: bool, skip_defaults: bool, exclude_unset: bool, exclude_defaults: bool, exclude_none: bool, encoder: Union[Callable[[Any], Any], NoneType], models_as_dict: bool= True, **dumps_kwargs) -> unicode`
Generate a JSON representation of the model, `include` and `exclude` arguments as per `dict()`.

`encoder` is an optional function to supply as `default` to json.dumps(), other arguments as per `json.dumps()`.
###### `@staticmethod def update_forward_refs(**localns)`
Try to update ForwardRefs on fields based on this Model, globalns and localns.
#### Class `dnastack.http.session_info.SessionManager(storage: dnastack.http.session_info.BaseSessionStorage, static_session: Union[str, NoneType], static_session_file: Union[str, NoneType])`
Session Information Manager 
##### Methods
#### Class `dnastack.http.session_info.UnknownSessionError()`
Raised when an unknown session is requested 
##### Properties
###### `args`

##### Methods
###### `@staticmethod def with_traceback()`
Exception.with_traceback(tb) --
set self.__traceback__ to tb and return self.