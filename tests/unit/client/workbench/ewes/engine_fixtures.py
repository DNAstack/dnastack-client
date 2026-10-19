"""One engine per adapter type, in the engines service's wire format.

Every secret value contains "SECRET-" so tests can assert it never reaches output.
"""
import copy
import json


GCP_SERVICE_ACCOUNT = {"type": "service_account", "project_id": "demo-project", "private_key": "SECRET-GCP-KEY"}

GCP_ENGINE = {
    "id": "hifi-solves-cromwell",
    "name": "HiFi Solves Demo Cromwell",
    "provider": "GCP",
    "region": "us-central1",
    "default": True,
    "engine_adapter_configuration": {
        "type": "GCP_CLOUD_RUN_CROMWELL",
        "url": "https://cromwell.example.com",
        "project_id": "demo-project",
        "auth_config": {"service_account_json": json.dumps(GCP_SERVICE_ACCOUNT)},
    },
}

WES_OAUTH_ENGINE = {
    "id": "wes-oauth",
    "name": "WES OAuth",
    "provider": "LOCAL",
    "region": "local",
    "engine_adapter_configuration": {
        "type": "WES_ON_CROMWELL",
        "url": "https://wes.example.com",
        "authentication_method": "OAUTH",
        "oauth_config": {
            "clientId": "wes-client",
            "clientSecret": "SECRET-OAUTH",
            "tokenUri": "https://auth.example.com/token",
            "resource": "https://wes.example.com",
            "scope": "wes",
        },
    },
}

WES_MTLS_ENGINE = {
    "id": "wes-mtls",
    "name": "WES mTLS",
    "provider": "LOCAL",
    "region": "local",
    "engine_adapter_configuration": {
        "type": "WES_ON_CROMWELL",
        "url": "https://wes.example.com",
        "authentication_method": "MTLS",
        "ssl_config": {
            "server_certificate_chain": "-----BEGIN CERTIFICATE-----\nSERVER\n-----END CERTIFICATE-----\n",
            "client_key_and_certificate_chain": "-----BEGIN PRIVATE KEY-----\nSECRET-MTLS\n-----END PRIVATE KEY-----\n",
        },
    },
}

AZURE_ENGINE = {
    "id": "azure-cromwell",
    "name": "Azure Cromwell",
    "provider": "AZURE",
    "region": "eastus",
    "engine_adapter_configuration": {
        "type": "AZURE_CONTAINER_APP_CROMWELL",
        "url": "https://cromwell.azure.example.com",
        "tenant_id": "tenant",
        "client_id": "azure-client",
        "client_secret": "SECRET-AZURE",
        "scope": "azure-client/.default",
        "storage_account_name": "account",
        "storage_container_name": "container",
    },
}

AWS_ENGINE = {
    "id": "aws-omics",
    "name": "AWS HealthOmics",
    "provider": "AWS",
    "region": "us-east-1",
    "engine_adapter_configuration": {
        "type": "AWS_HEALTH_OMICS",
        "access_key_id": "AKIAEXAMPLE",
        "secret_access_key": "SECRET-AWS",
        "output_bucket": "s3://omics-output",
        "role_arn": "arn:aws:iam::123456789012:role/omics",
    },
}

ALL_ENGINES = {
    "gcp": GCP_ENGINE,
    "wes_oauth": WES_OAUTH_ENGINE,
    "wes_mtls": WES_MTLS_ENGINE,
    "azure": AZURE_ENGINE,
    "aws": AWS_ENGINE,
}

SECRET_VALUES = ["SECRET-GCP-KEY", "SECRET-OAUTH", "SECRET-MTLS", "SECRET-AZURE", "SECRET-AWS"]


def engine(key: str) -> dict:
    """A deep copy, so tests can mutate it freely."""
    return copy.deepcopy(ALL_ENGINES[key])


def as_service_response(engine_body: dict) -> dict:
    """What the service returns for an engine: the body plus server-set fields."""
    response = copy.deepcopy(engine_body)
    response.update({"version": "v-1", "state": "ONLINE", "created_at": "2026-10-13T00:00:00Z",
                     "updated_at": "2026-10-13T00:00:00Z", "default": bool(engine_body.get("default"))})
    return response
