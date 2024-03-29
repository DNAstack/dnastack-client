# Service Clients

The library provides several clients to specifically support different (GA4GH-like) types
of [service endpoints](glossary.md#service-endpoint), according to the API specification.

* [Collection Service and Explorer Service](#collection-service-and-explorer-service-collection-api)
* [Data Connect Service](#data-connect-service-ga4gh-data-connect-api)
* [Data Repository Service (DRS)](#data-repository-service-ga4gh-drs-api)
* [Service Registry Service](#service-registry-service-ga4gh-service-registry-api)

## Collection Service and Explorer Service (Collection API)

* **Class:** `dnastack.CollectionServiceClient` ([docs](api/dnastack.client.collections.client.CollectionServiceClient.md))
* **Short Type:** `collections`

The client provide read-only interfaces to **the Collection API**. Currently, it supports two variations of the API
specification.

```yaml
# Standard Collection API Type
group: com.dnastack
artifact: collection-service
version: 1.0.0
```

or

```yaml
# Explorer's Collection API Type
group: com.dnastack.explorer
artifact: collection-service
version: 1.0.0
```

> ↑ This is the **default type** of the client.

Please note that the explorer service, e.g., Viral AI, is another implementation of the collection service. While there
could be slight differences in API specification, this client will normalize the differences.

### How to initialize a client

Here are examples on how to initialize a client for Collection Service.

#### Example: Use the default type

```python
from dnastack import CollectionServiceClient
from dnastack.configuration.models import ServiceEndpoint

# Use the default service type.
client = CollectionServiceClient.make(ServiceEndpoint(url='https://viral.ai/api/'))
```

This uses the default type, which is **the explorer service** and predefined as
`EXPLORER_COLLECTION_SERVICE_TYPE_V1_0` in `dnastack.client.collections.client`.

Here is how to do the same thing with the CLI tool.

```shell
dnastack config collections.url "https://viral.ai/api/"
```

#### Example: Override the type

```python
from dnastack import CollectionServiceClient
from dnastack.client.collections.client import STANDARD_COLLECTION_SERVICE_TYPE_V1_0
from dnastack.configuration.models import ServiceEndpoint

# Use the default service type.
client = CollectionServiceClient.make(ServiceEndpoint(url='https://collection-service.viral.ai/',
                                                      type=STANDARD_COLLECTION_SERVICE_TYPE_V1_0,
                                                      authentication=dict(...)))
```

This is an example to override a service type to **the standard collection service** and predefined as
`STANDARD_COLLECTION_SERVICE_TYPE_V1_0` in `dnastack.client.collections.client`.

Here is how to do the same thing with the CLI tool.

```shell
dnastack config collections.url "https://collection-service.viral.ai/"
dnastack config collections.type.group "com.dnastack"
dnastack config collections.type.artifact "collection-service"
dnastack config collections.type.version "1.0.0"
# dnastack config collections.authentication.<KEY> <VALUE>
```

### How to switch from the Collection Service client to the Data Connect client

While a collection service provides Data Connect API, each implementation has different routing for the data connect
APIs. Therefore, it is highly recommended to use `switch_to_data_connect` from `dnastack.helpers.collections` to create
a Data Connect client based on the available collection service client.

Here is how to switch from a **Explorer's** Collection Service client.

```python
from dnastack.cli.helpers import switch_to_data_connect

# noinspection PyUnresolvedReferences
data_connect_client = switch_to_data_connect(collection_service_client,
                                             COLLECTION_SLUG_NAME)
```

> The Explorer's collection service requires **the slug name of the target collection (`COLLECTION_SLUG_NAME`)**.

Here is how to switch from a **standard** Collection Service client.

```python
from dnastack.cli.helpers import switch_to_data_connect

# noinspection PyUnresolvedReferences
data_connect_client = switch_to_data_connect(collection_service_client)
```

> The standard collection service **DOES NOT** require the ID or slug name of the target collection.

For the CLI tool, you don't need to do anything as the CLI handler will handle the switch automatically.

## Data Connect Service (GA4GH Data Connect API)

* Class: `dnastack.DataConnectClient` ([docs](api/dnastack.client.data_connect.DataConnectClient.md))
* **Short Type:** `data_connect`

The client provide read-only interfaces to **the Data Connect API**. Currently, it supports ONE variation of the API
specification.

```yaml
group: org.ga4gh
artifact: data-connect
version: 1.0.0
```

### How to initialize a client

Here are examples on how to initialize a client for Collection Service.

```python
from dnastack import DataConnectClient
from dnastack.configuration.models import ServiceEndpoint

client = DataConnectClient.make(ServiceEndpoint(url='https://collection-service.viral.ai/data-connect/',
                                                authentication=dict(...)))
```

Here is how to do the same thing for the CLI tool.

```shell
dnastack config set data_connect.url "https://collection-service.viral.ai/data-connect/"
# dnastack config data_connect.authentication.<KEY> <VALUE>
```

## Data Repository Service (GA4GH DRS API)

* **Class:** `dnastack.DrsClient` ([docs](api/dnastack.client.drs.DrsClient.md))
* **Short Type:** `drs`

The client provide read-only interfaces to **the DRS API**. Currently, it supports ONE variation of the API
specification.

```yaml
group: org.ga4gh
artifact: drs
version: 1.1.0
```

### How to initialize a client

Here are examples on how to initialize a client for Collection Service.

```python
from dnastack import DrsClient
from dnastack.configuration.models import ServiceEndpoint

client = DrsClient.make(ServiceEndpoint(url='https://collection-service.viral.ai/',
                                        authentication=dict(...)))
```

> The collection service also provides DRS APIs.

Here is how to do the same thing for the CLI tool.

```shell
dnastack config set drs.url "https://collection-service.viral.ai/"
# dnastack config drs.authentication.<KEY> <VALUE>
```

## Service Registry Service (GA4GH Service Registry API)

* **Class:** `dnastack.DrsClient` ([docs](api/dnastack.client.drs.DrsClient.md))
* **Short Type:** `drs`

The client provide read-only interfaces to **the DRS API**. Currently, it supports ONE variation of the API
specification.

```yaml
group: org.ga4gh
artifact: service-registry
version: 1.0.0
```

> This type of clients is mainly used as an extension to the library or CLI tool. Therefore, there is no CLI
> command that directly relies on the type of clients.

### How to initialize a client

Here are examples on how to initialize a client for Collection Service.

```python
from dnastack.client.service_registry.client import ServiceRegistry
from dnastack.configuration.models import ServiceEndpoint

client = ServiceRegistry.make(ServiceEndpoint(url='https://collection-service.viral.ai/service-registry/'))
```

> The collection service also provides service registry APIs.

Here is how to do the same thing for the CLI tool.

```shell
dnastack config set registry.url "https://collection-service.viral.ai/service-registry/"
```
