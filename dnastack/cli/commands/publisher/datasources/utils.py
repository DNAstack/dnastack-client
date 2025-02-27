from typing import Dict, Any, Optional
from imagination import container
from dnastack.cli.helpers.client_factory import ConfigurationBasedClientFactory
from dnastack.client.datasources.client import DataSourceServiceClient


def _get_datasource_client() -> DataSourceServiceClient:
    """Get the data source service client."""
    factory: ConfigurationBasedClientFactory = container.get(ConfigurationBasedClientFactory)
    return factory.get(DataSourceServiceClient)

def _filter_datasource_fields(datasource: Dict[str, Any]) -> Dict[str, Any]:
    """Filter and transform datasource fields for display."""
    return {
        'id': datasource.get('id'),
        'name': datasource.get('name'),
        'type': datasource.get('type'),
    }