# How to run end-to-end tests

## Prerequisites

* Python 3.7 or higher
* `chromedriver`
  * On MacOS, you need to ensure that the `chromedriver` command is executable.
* The test environment variable file
  * The plain-text env file for your local testing 
  * The encrypted `test-env.enc` file, [which is only for the CI/CD pipeline](#configuration-file-for-cicd-pipeline)

## Setup

### Set up from template (Recommended for local development)

1. Copy `.env.dist` to `.env`:
   ```bash
   cp .env.dist .env
   ```
2. Update the values in `.env` with your test credentials.
   * You may need access to Wallet APIs to create a client, set grants and access policies.
   * At minimum, you'll need to fill in `E2E_PUBLISHER_AUTH_DEVICE_CODE_TEST_EMAIL` and `E2E_PUBLISHER_AUTH_DEVICE_CODE_TEST_TOKEN`.
3. Run `pip3 install -r requirements.txt`.
   * `requirements.txt` contains more requirements than the ones in `setup.cfg` for the build and testing processes.

### Set up with Google Secret Manager (For team members with GCloud access)

**Note:** This method requires Google Cloud authentication to be set up first.

1. Ensure you are using the correct Google Cloud project:
   ```bash
   gcloud config set project dnastack-product-development
   ```

2. Set up Google Cloud authentication:
   ```bash
   gcloud auth application-default login --no-launch-browser
   ```
   Open the link in your browser, log in with your Google account, and copy the authentication code back to the terminal.

3. Run
   ```shell
   ./scripts/test_env_manager.py read default > .env
   ```
   * This script will pull the envfile from the secret manager.
   * If you need to manage the shared envfiles, use `test_env_manager.py`. Use `--help` for more information.

4. Run 
   ```shell
   pip3 install -r requirements.txt
   ```
   * `requirements.txt` contains more requirements than the ones in `setup.cfg` for the build and testing processes.

### Note on the test suite

The test suite will generate a temporary folder during the test and generally clear any files used by the test suite.
The location of the temp files or directories can be found in [the advanced configuration section](#advanced-configuration).

## Running the test suite

There are three ways to run the test suite.

### 1. Use `python3 -m unittest` directly.

1. Set environment variables from `.env`.
   * For example: `source .env` 
2. Run `python3 -m unittest discover -v -s .` to run all tests.
   * Alternatively, run `python3 -m unittest -v <FILE_PATH_OR_PYTHON_MODULE>` to run specific tests.
     * Example 1: `python3 -m unittest -v tests.cli.test_dataconnect`
     * Example 2: `python3 -m unittest -v tests/cli/test_dataconnect.py`
   * You can use `-f` to end the test on the first failure.
   * See [the official docs](https://docs.python.org/3/library/unittest.html) for more information.

### Use `./scripts/run-e2e-tests.sh`

The script is used by the CI/CD pipeline and will work with `.env` right out of the box. It is technically the shortcut
of [the first method](#1-use-python3--m-unittest-directly)

### Run with IntelliJ or PyCharm

1. Add a new **Configuration** for **Python tests → Unittests**.
2. Set target to the root of your working copy, e.g., `/Users/jnopporn/workspace/dnastack-client-library`.
3. Copy everything in `.env` as environment variables.

## Advanced Configuration

On top of the environment variables described in [the main configuration doc](cli-configuration.md#environment-variables),
here are more specifically for testing.

### Configuration for Standard Tests

Here are the variables for **all tests**.

|              | Environment Variable           | Type    | Usage                                                                                                        | Default |
|--------------|--------------------------------|---------|--------------------------------------------------------------------------------------------------------------|---------|
| **Required** | E2E_ENV_FILE                   | String  | The location of the env file                                                                                 | -       |
| **Required** | E2E_CLIENT_ID                  | String  | Wallet/OAuth2 Client ID<sup>(1)</sup>                                                                        | -       |
| **Required** | E2E_CLIENT_SECRET              | String  | Wallet/OAuth2 Client Secret<sup>(1)(2)</sup>                                                                 | -       |
| **Required** | E2E_WALLET_BASE_URL            | String  | The base URL to the Wallet service                                                                           | -       |
| Optional     | E2E_CONFIG_OVERRIDING_ALLOWED  | Boolean | If `true`, the test suite may override the existing configuration file located at `${DNASTACK_CONFIG_FILE}`. | `false` |
| Optional     | E2E_HEADLESS                   | Boolean | If `true`, the test suite will run in the headless mode.                                                     | `true`  |
| Optional     | E2E_WEBDRIVER_TESTS_DISABLED   | Boolean | If `true`, the test suite will disable any tests requiring Web Driver.                                       | `false` |

Here are the variables for **test resources**.

|          | Environment Variable       | Type   | Usage                                        | Default                                                 |
|----------|----------------------------|--------|----------------------------------------------|---------------------------------------------------------|
| Optional | E2E_COLLECTION_SERVICE_BASE_URL | String | The base URL to the collection service       | `https://collection-service.viral.ai/`                  |
| Optional | E2E_DATA_CONNECT_URL       | String | The base URL to the data connect service     | `https://collection-service.viral.ai/`                  |
| Optional | E2E_DRS_URL                | String | The base URL to the data respository service | `https://collection-service.viral.ai/`                  |
| Optional | E2E_SERVICE_REGISTRY_URL   | String | The base URL to the service registry service | `https://collection-service.viral.ai/service-registry/` |

Here are the variables for **the device-code-flow auth test**.

|          | Environment Variable            | Type    | Usage                                                              | Default |
|----------|---------------------------------|---------|--------------------------------------------------------------------|---------|
| Optional | E2E_PUBLISHER_AUTH_DEVICE_CODE_TEST_EMAIL | String  | E-mail address for device-code authentication<sup>(4)</sup>        | -       |
| Optional | E2E_PUBLISHER_AUTH_DEVICE_CODE_TEST_TOKEN | String  | Personal access token for device-code authentication<sup>(4)</sup> | -       |

Here are the variables for **the personal-access-token auth test**.

|          | Environment Variable    | Type    | Usage                                                      | Default |
|----------|-------------------------|---------|------------------------------------------------------------|---------|
| Optional | E2E_AUTH_PAT_TEST_EMAIL | String  | E-mail address for PAT authentication<sup>(3)</sup>        | -       |
| Optional | E2E_AUTH_PAT_TEST_TOKEN | String  | Personal access token for PAT authentication<sup>(3)</sup> | -       |

Here is the additional variable for **testing on the staging environment**.

|          | Environment Variable                    | Type   | Usage                                                              | Default                                           |
|----------|-----------------------------------------|--------|--------------------------------------------------------------------|---------------------------------------------------|
| Optional | E2E_STAGING_AUTH_DEVICE_CODE_TEST_EMAIL | String | E-mail address for device-code authentication<sup>(4)</sup>        | -                                                 |
| Optional | E2E_STAGING_AUTH_DEVICE_CODE_TEST_TOKEN | String | Personal access token for device-code authentication<sup>(4)</sup> | -                                                 |
| Optional | E2E_STAGING_CLIENT_ID                   | String | The OAuth client ID for staging                                    | `dnastack-client-library-testing`                 |
| Optional | E2E_STAGING_CLIENT_SECRET               | String | The OAuth client secret for staging                                | -                                                 |
| Optional | E2E_STAGING_TOKEN_URI                   | String | The URI to the OAuth2 token endpoint on the staging environment    | `https://wallet.staging.dnastack.com/oauth/token` |

**Notes:**
1. This client must at least allow the client-credential flow for the functionality tests. For the authentication tests, it must allow the client-credential flow, the PAT flow (if tested), and the device-code flow.
2. For security reason, please be careful not to commit or publicly publish the test credential as it requires write permissions to some services.
3. Both email and personal access token are needed to enable the tests for the personal-access-token authentication flow. The token must be from **WalletZ**.
4. Both email and personal access token are needed to enable the tests for the device-code authentication flow. The token must be from the corresponding **WalletN**, like Passport.

### Configuration for Stress Tests

|          | Environment Variable    | Type    | Usage                   | Default |
|----------|-------------------------|---------|-------------------------|---------|
| Optional | E2E_STRESS_TEST_ENABLED | Boolean | Enable the stress tests | `false` |

### Configuration for WES Tests

> This set to tests is only runnable in **the staging environment**.

|             | Environment Variable       | Type    | Usage                | Default                                                   |
|-------------|----------------------------|---------|----------------------|-----------------------------------------------------------|
| Optional    | E2E_WES_TEST_ENABLED       | Boolean | Enable the WES tests | `false`                                                   |
| Conditional | E2E_WES_ENDPOINT_URI       | String  |                      | `https://workspaces-wes.alpha.dnastack.com/ga4gh/wes/v1/` |
| Conditional | E2E_WES_OAUTH_RESOURCE_URI | String  | The resource URL     | `https://workspaces-wes.alpha.dnastack.com/`              |

## Configuration file for CI/CD pipeline

The CI/CD pipeline for the library requires its own encrypted configuration file (with environment variables), namedly
`test-env.enc`. The file can be encrypted with this command. 

```shell
export E2E_ENV_FILE=.env
```

```shell
gcloud kms encrypt \
  --plaintext-file=${E2E_ENV_FILE} \
  --ciphertext-file=test-env.enc\
  --location=global \
  --keyring=cloud-build-webhook \
  --project=cloud-builld-webhook \
  --key=secret_key
```

where it uses the same encryption key with the main CBW service. Then, _commit the file in this repository_.

> **WARNING:** Please DO NOT commit the plain text file.
