# Command line tool

The package provides the CLI tool, which allows users to interact with DNAstack services without writing a single line of Python.

The CLI tool is available in two forms:

* Shell executable: `dnastack`
* [Python's Top-level Module](https://docs.python.org/3/using/cmdline.html#cmdoption-m): `python3 -m dnastack`<sup>1</sup>.

> **Note 1:** On Windows, if a user installs Python via Windows App Store, after installing the library with `pip`, he or she can only run the CLI tool this way.

## Getting Started

Here is the basic usage of the CLI. The full list of commands is available for the following types of service endpoints:
* [Collection Service Endpoint](#collection-service-endpoint)
* [Data Connect Endpoint](#data-connect-service-endpoint)
* [Data Repository Service Endpoint](#data-repository-service-endpoint)
* [Workflow Execution Service Endpoint](#workflow-execution-service-endpoint)

### Basic setup with no authentication

First, let's define where the endpoint of the collection service is.

```shell
# ↓ Add a Collection Service endpoint.
dnastack config endpoints add viral-ai -t collections

# ↓ Set the URL to the endpoint.
dnastack config endpoints set viral-ai url "https://viral.ai/api/"
```

> Please note that, in this example, the endpoint is publicly accessible.

Then, you can use [any commands for collection service endpoint](#collection-service-endpoint).

### Setup with device-code authentication

This guide would set up the CLI tool for the device-code authentication.

Support we want to set up a protected Data Connect endpoint with the device code authentication. Here is how you can do it. 

```shell
# ↓ Add a Data Connect endpoint.
dnastack config endpoints add viral-ai-dc -t data_connect
# Alternatively, you can replace "data_connect" with "org.ga4gh:data-connect:1.0" (full service type) 

# ↓ Set the URL to the endpoint.
dnastack config endpoints set viral-ai-dc url "https://collection-service.viral.ai/data-connect/"

# ↓ Set the authentication information. 
dnastack config endpoints set viral-ai-dc authentication.client_id "dnastack-client-library"
dnastack config endpoints set viral-ai-dc authentication.device_code_endpoint "https://wallet.viral.ai/oauth/device/code"
dnastack config endpoints set viral-ai-dc authentication.grant_type "urn:ietf:params:oauth:grant-type:device_code"
dnastack config endpoints set viral-ai-dc authentication.resource_url "https://collection-service.viral.ai/"
dnastack config endpoints set viral-ai-dc authentication.token_endpoint "https://wallet.viral.ai/oauth/token"
```

Then, you can use [any commands for Data Connect service endpoint](#data-connect-service-endpoint)

### Automatically setup with service registries

```shell
dnastack config registries add viral-ai-reg "https://collection-service.viral.ai/service-registry/"
dnastack dataconnect tables list --endpoint-id viral-ai-reg:data-connect
```

For more information, please check out [the documentation on service registries](./service-registry.md).

## Command Structure

* dnastack
  * alpha
    * auth
      * import
      * export
    * wes
      * get
      * list
      * logs
      * submit
  * [auth](#authentication-and-session-management)
    * login
    * revoke
    * status
  * [collections](#collection-service-endpoint) (aliases: `cs`)
    * list
    * list-items
    * query
    * tables
      * list
  * [config](#global-configuration)
    * schema
    * [endpoints](#service-endpoint-configuration)
      * add
      * available-properties
      * get-defaults
      * list
      * remove
      * schema
      * set
      * set-default
      * unset
      * unset-default
    * [registries](#service-registry-endpoint) (aliases: `reg`)
      * add
      * list
      * list-endpoints
      * remove
      * sync
  * [data-connect](#data-connect-service-endpoint) (aliases: `dataconnect`, `dc`)
    * tables
      * list
      * get
    * query
  * [files](#data-repository-service-endpoint) (aliases: `drs`)
    * download
  * [publisher](#publisher-service-endpoint) 
    * datasources
      * list
  * use<sup>1</sup>

> <sup>1</sup>This command group is deprecated.

> <sup>2</sup>This will be implemented due to [this ticket](https://www.pivotaltracker.com/story/show/182289347).

## Global Configuration

### Show the schema of the configuration file

```shell
dnastack config schema
```

## Service Endpoint Configuration

These are commands designed for managing service endpoints.

### Add a new endpoint

```shell
dnastack config endpoints add [OPTIONS] ID

Options:
  -t, --type [collections|data_connect|drs|registry]
                                  Client short type  [required]
```

where:
* `ID` is the ID of the service endpoint.

### List all available configuration property

```shell
dnastack config endpoints available-properties
```

### Get the command-group-to-default-endpoint-id map

```shell
dnastack config endpoints get-defaults
```

### List all registered service endpoint

```shell
dnastack config endpoints list [OPTIONS]

  List all registered service endpoint

Options:
  --context TEXT            Context
  -t, --type TEXT           Short of full service type, e.g., "data_connect"
                            or "org.ga4gh:data-connect:1.0"
  -o, --output [json|yaml]  Output format
```

### Remove an endpoint

```shell
dnastack config endpoints remove ID
```

where:
* `ID` is the ID of the service endpoint.

### Show the schema of the endpoint configuration

```shell
dnastack config endpoints schema
```

> This is mainly for development.

### Set the endpoint property

```shell
dnastack config endpoints set ID CONFIG_PROPERTY CONFIG_VALUE
```

where:
* `ID` is the ID of the service endpoint,
* `CONFIG_PROPERTY` is [the property path](#list-all-available-configuration-property) of the endpoint configuration,
* `CONFIG_VALUE` is the value of the target endpoint property.

### Set the given endpoint as the default for its type

```shell
dnastack config endpoints set-default ID
```

where:
* `ID` is the ID of the service endpoint.

### Unset the endpoint property

```shell
dnastack config endpoints unset ID CONFIG_PROPERTY
```

where:
* `ID` is the ID of the service endpoint,
* `CONFIG_PROPERTY` is [the property path](#list-all-available-configuration-property) of the endpoint configuration.

### Unset the given endpoint as the default for its type

```shell
dnastack config endpoints unset-default ID
```

where:
* `ID` is the ID of the service endpoint.

## Service Registry Endpoint

### Add a new service registry to the configuration and import all endpoints registered with it.

```
dnastack config registries add REGISTRY_ENDPOINT_ID REGISTRY_URL
```

where:
* `REGISTRY_ENDPOINT_ID` is the ID of the service registry endpoint, which is technically a service endpoint,
* `REGISTRY_URL` is the base URL to the service registry endpoint.

The local ID of each imported endpoint will be
`<registry_endpoint_id>:<external_id>`.

If there exists at least ONE service endpoints from the given registry then,
throw an error.

If the registry URL is already registered, then throw an error.

### List registered service registries

```
dnastack config registries list
```

### List all service endpoints imported from given registry

```
dnastack config registries list-endpoints REGISTRY_ENDPOINT_ID
```

where:
* `REGISTRY_ENDPOINT_ID` is the ID of the service registry endpoint, which is technically a service endpoint.

### Remove the entry of the service registry from the configuration and remove all endpoints registered with it.

```
dnastack config registries remove REGISTRY_ENDPOINT_ID
```

where:
* `REGISTRY_ENDPOINT_ID` is the ID of the service registry endpoint, which is technically a service endpoint.

### Synchronize the service endpoints associated to the given service registry.

```
dnastack config registries sync REGISTRY_ENDPOINT_ID
```

where:
* `REGISTRY_ENDPOINT_ID` is the ID of the service registry endpoint, which is technically a service endpoint.

This command will add new endpoints, update existing ones, and/or remove
endpoints that are no longer registered with the given service registry.

## Authentication Commands

### Log in to one or all endpoints

```
dnastack auth login [OPTIONS]

  Log in to ALL service endpoints or ONE specific service endpoint.

  If the endpoint ID is not specified, it will initiate the auth process for all endpoints.

Options:
  --endpoint-id TEXT  Endpoint ID
  --revoke-existing   If used, the existing session will be automatically
                      revoked before the re-authentication
```

### Check the status of all authenticators

```
dnastack auth status

Check the status of all authenticator
```

### Revoke the authorization for one or all endpoints

```
dnastack auth revoke [OPTIONS]

  Revoke the authorization to one to many endpoints.

  If the endpoint ID is not specified, it will revoke all authorizations.

Options:
  --endpoint-id TEXT  Endpoint ID
  --force             Force the auth revocation without prompting the user for
                      confirmation
```

## Authentication and session management

### Log in to all service endpoint or ONE specific.

```shell
dnastack auth login [OPTIONS]

  Log in to ALL service endpoints or ONE specific service endpoint.

  If the endpoint ID is not specified, it will initiate the auth process for
  all endpoints.

Options:
  --context TEXT      Context
  --endpoint-id TEXT  Endpoint ID
  --revoke-existing   If set, the existing session(s) will be automatically
                      revoked before the re-authentication
```

### Revoke the session of one or all endpoints

```shell
dnastack auth revoke [OPTIONS]

  Revoke the authorization to one to many endpoints.

  If the endpoint ID is not specified, it will revoke all authorizations.

Options:
  --context TEXT      Context
  --endpoint-id TEXT  Endpoint ID
  --force             Force the auth revocation without prompting the user for
                      confirmation
```

### Check the status of all authenticators (session)

```shell
dnastack auth status [OPTIONS]

  Check the status of all authenticators.

Options:
  --context TEXT            Context
  --endpoint-id TEXT        Endpoint ID
  -o, --output [json|yaml]  Output format
```

## Collection Service Endpoint

To use this set of commands, you need to configure at least one [Collection Service](glossary.md#service-endpoint-types) endpoint.

### List all collections.

```
dnastack collections list
```

| Output Reference Schema                               |
|-------------------------------------------------------|
| `List[dnastack.client.collections_client.Collection]` |

### List items from a collection

```
dnastack collections list-items [OPTIONS]

  List items of the given collection

Options:
  --endpoint-id TEXT     Endpoint ID
  -c, --collection TEXT  The ID or slug name of the target collection;
                         required only by an explorer service  [required]
  -l, --limit INTEGER    The maximum number of items to display  [default: 50]
```

### List collection tables
```shell
dnastack collections tables list [OPTIONS]

  List all accessible tables

Options:
  --collection TEXT    The ID or slug name of the target collection; required
                       only by an explorer service
  --endpoint-id TEXT   Service Endpoint ID
```

| Output Reference Schema                          |
|--------------------------------------------------|
| `List[dnastack.client.dataconnect_client.Table]` |

### Query the collection data with SQL string

```shell
dnastack collections query [OPTIONS] QUERY

  Query data

Options:
  --collection TEXT            The ID or slug name of the target collection;
                               required only by an explorer service
  -f, --format [json|csv]      [default: json]
  --decimal-as [string|float]  [default: string]
  --endpoint-id TEXT           Service Endpoint ID
```

where:                            
* `QUERY` is a SQL-formatted query string, e.g., `SELECT * FROM oncology.public.samples`.

| Output Reference Schema |
|-------------------------|
| `List[Dict[str, Any]`   |

## Data Connect Service Endpoint

To use this set of commands, you need to configure at least one [Data Connect](glossary.md#service-endpoint-types) endpoint.

### List tables

```shell
dnastack dataconnect tables list
```

| Output Reference Schema                          |
|--------------------------------------------------|
| `List[dnastack.client.dataconnect_client.Table]` |

### Query the data with SQL string

```shell
dnastack dataconnect query [OPTIONS] QUERY

Options:
  -o, --output TEXT        The path to the output file (Note: When the option
                           is specified, there will be no output to stdout.)
  -f, --format [json|csv]  Output Format  [default: json]
  --decimal-as [string|float]  [default: string]
```

where:
* `QUERY` is a SQL-formatted query string, e.g., `SELECT * FROM cat_1.sch_2.tbl_3`.

| Output Reference Schema |
|-------------------------|
| `List[Dict[str, Any]`   |

## Data Repository Service Endpoint

To use this set of commands, you need to configure at least one [DRS](glossary.md#service-endpoint-types) endpoint.

### Download files

```shell
dnastack files download [OPTIONS] [URLS]...

Options:
  -o, --output-dir TEXT  [default: /opt]
  -i, --input-file TEXT
```

## Workflow Execution Service Endpoint

> Not officially supported and will by moved to the alpha command group.

To use this set of commands, you need to configure at least one [WES](glossary.md#service-endpoint-types) endpoint.

### Get the information of the service instance

```shell
dnastack wes info
```

### Submit a workflow run

```shell
dnastack wes runs execute [OPTIONS]

Options:
  -u, --workflow-url TEXT        [required]
  -a, --attachment TEXT
  --inputs-file TEXT
  -e, --engine-parameter TEXT
  --engine-parameters-file TEXT
  -t, --tag TEXT
  --tags-file TEXT
```

### Get the list of workflow runs

```shell
dnastack wes runs list [OPTIONS]

Options:
  -s, --page-size INTEGER
  -t, --page-token TEXT
```

## Publisher Service Endpoint

To use this set of commands, you need to configure at least one Publisher Service endpoint.

### List data sources

```shell
dnastack publisher datasources list [OPTIONS]

  List all data sources

Options:
  --type TEXT              Filter datasources by type (e.g., "AWS")
  -o, --output [json|yaml] Output format  [default: json]
```

| Output Reference Schema |
|------------------------|
| `List[Dict[str, Any]]` |

Example:
```shell
# List all datasources
dnastack publisher datasources list

# List only AWS datasources
dnastack publisher datasources list --type AWS

# Get output in YAML format
dnastack publisher datasources list -o yaml
```

### Get the information of a specific workflow run

```shell
dnastack wes run get [OPTIONS] RUN_ID

Options:
  --status  Flag to return only status
```

### Get a log from a specific run

```shell
dnastack wes run logs [OPTIONS] RUN_ID

Options:
  --stdout             Flag to get the logs of stdout. Note that This is mutually exclusive with --stderr and --url.
  --stderr             Flag to get the logs of stderr. Note that This is mutually exclusive with --stdout and --url.
  --url TEXT           The URL where the log is. Note that This is mutually exclusive with --stderr and --stdout.
  -t, --task TEXT
  -i, --index INTEGER
```

### Cancel a workflow run

```shell
dnastack wes run cancel RUN_ID
```

### Experimental Features Command (Alpha)
New/unstable/unsupported features can be prototyped easily using this command.
However, keep in mind that alpha commands are experimental and can change incompatibly.

There are currently no alpha commands available but the usage will follow this pattern:
```shell
dnastack alpha <command> [--args]
```
