#!/bin/bash
set +e

echo "Please ensure that this script is run from the root directory of the project"

# Install dependencies
echo "Installing test dependencies..."
# Check if uv is available, if not fall back to pip
if command -v uv &> /dev/null; then
    uv pip install --system -q selenium
else
    python3 -m pip install --disable-pip-version-check -q selenium
fi

# Import the environment variables
if [[ -z "${E2E_ENV_FILE}" ]]; then
  echo "The environment variable file for testing is not defined, i.e., E2E_ENV_FILE is not set. Use the default settings."
  E2E_ENV_FILE=".env"
fi

if [[ -f "${E2E_ENV_FILE}" ]]; then
  echo "Using environment variables from ${E2E_ENV_FILE} ..."
  set -a
  source ${E2E_ENV_FILE}
  set +a
else
  echo "The environment variables for testing is set be from ${E2E_ENV_FILE} but the file does not exist."
  exit 1
fi

if [[ -n "${DNASTACK_SESSION_DIR}" ]] && [[ -d "${DNASTACK_SESSION_DIR}" ]]; then
  echo "Removing saved session direction"
  rm -rf ${DNASTACK_SESSION_DIR}
fi

# Run the tests
if [[ -z "$@" ]]; then
  echo "Running the full test set..."
  python3 -m unittest discover -vs .
else
  echo "Running the custom test set..."
  python3 -m unittest $@
fi

export EXIT_CODE=$?

if [[ "${EXIT_CODE}" == "0" ]]; then
  echo "Test Result: Complete"
else

  set -e
  echo "Test Result: Failed"
  exit 1
fi
