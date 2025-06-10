# Glossary

## Service Endpoint

| Reference Class                           |
|-------------------------------------------|
| `dnastack.configuration.ServiceEndpoint`  |

A service endpoint is where the API is available, for example, "`https://foo.com/data-connect/` is a Data Connect service
endpoint" means "`https://foo.com/data-connect` is considered as the base URL of the API for a Data Connect client."

In terms of configuration, the model of the service endpoint will contain information related to the service endpoint,
such as base URL, [authentication information](authentations.md), etc.

## Service Endpoint Types

The CLI tool and library supports different types of service endpoints, according to the API specification.

| Client Type                                                    | Short Type     |
|----------------------------------------------------------------|----------------|
| Collection Service Client (`dnastack.CollectionServiceClient`) | `collections`  |
| Explorer Service Client (`dnastack.ExplorerClient`)            | `explorer`     |
| Data Connect Client (`dnastack.DataConnectClient`)             | `data_connect` |
| Data Repository Service Client (`dnastack.DrsClient`)          | `drs`          |

See more on [service clients](service-clients.md).

## Default Service Endpoints

| Reference Class                           | Reference Attribute |
|-------------------------------------------|---------------------|
| `dnastack.configuration.ServiceEndpoint`  | `defaults`          |

Each type of [adapters](#service-endpoint-types) may has the default service endpoint which is defined in the
configuration file like this:

```yaml
defaults:
  <adapter-type-id>: <service-endpoint-uuid>
```

The default service endpoints can be set by [updating the configuration file directly](cli-configuration.md#update-the-configuration-file-directly)
or [the set-default command](cli.md#set-the-default-service-endpoint).

## Federated Questions

| Reference Class                                    |
|----------------------------------------------------|
| `dnastack.client.explorer.models.FederatedQuestion` |

Federated questions are pre-defined analytical queries that can be executed across multiple collections in the Explorer network. These questions:

- Have standardized parameters and expected outputs
- Can query multiple data collections simultaneously
- Support various export formats (JSON, CSV, YAML)
- Provide consistent analytical interfaces across different data sources

### Question Parameters

| Reference Class                                |
|------------------------------------------------|
| `dnastack.client.explorer.models.QuestionParam` |

Parameters are the inputs required for a federated question. Each parameter has:
- A name and description
- A data type (string, number, boolean, etc.)
- Validation rules (required/optional, format constraints)
- Default values where applicable

### Question Collections

| Reference Class                                     |
|-----------------------------------------------------|
| `dnastack.client.explorer.models.QuestionCollection` |

Collections represent the data sources that a federated question can query. Each question specifies which collections it can operate on, allowing users to:
- Query all available collections (default behavior)
- Target specific collections for focused analysis
- Understand data availability across the Explorer network
