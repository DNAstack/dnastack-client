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
