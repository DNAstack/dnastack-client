"""
Common mock objects for unit testing.
"""
from typing import Dict, Any, Optional, List
import json


class MockResponse:
    """Mock HTTP response object."""
    
    def __init__(self, json_data: Optional[Dict[str, Any]] = None, 
                 status_code: int = 200, text: str = ""):
        self.json_data = json_data
        self.status_code = status_code
        self.text = text or json.dumps(json_data or {})
        self.headers = {'Content-Type': 'application/json'}
        self.ok = 200 <= status_code < 300
        
    def json(self):
        if self.json_data is None:
            raise ValueError("No JSON data")
        return self.json_data
    
    def raise_for_status(self):
        if not self.ok:
            from requests import HTTPError
            raise HTTPError(f"{self.status_code} Error", response=self)


class MockOAuth2Authenticator:
    """Mock OAuth2 authenticator for testing."""
    
    def __init__(self, access_token: str = "test_token", expires_in: int = 3600):
        self.access_token = access_token
        self.expires_in = expires_in
        self.authenticated = False
        self.refresh_count = 0
        
    def authenticate(self, force: bool = False) -> Dict[str, Any]:
        self.authenticated = True
        return {
            'access_token': self.access_token,
            'token_type': 'Bearer',
            'expires_in': self.expires_in,
            'refresh_token': 'test_refresh_token'
        }
    
    def refresh_token(self) -> Dict[str, Any]:
        self.refresh_count += 1
        return self.authenticate()
    
    def get_access_token(self) -> str:
        if not self.authenticated:
            self.authenticate()
        return self.access_token


class MockHTTPSession:
    """Mock HTTP session for testing."""
    
    def __init__(self):
        self.requests = []
        self.responses = {}
        self.default_response = MockResponse({})
        
    def set_response(self, url: str, response: MockResponse, method: str = 'GET'):
        """Set a response for a specific URL and method."""
        key = f"{method.upper()}:{url}"
        self.responses[key] = response
        
    def get(self, url: str, **kwargs) -> MockResponse:
        self.requests.append(('GET', url, kwargs))
        key = f"GET:{url}"
        return self.responses.get(key, self.default_response)
    
    def post(self, url: str, **kwargs) -> MockResponse:
        self.requests.append(('POST', url, kwargs))
        key = f"POST:{url}"
        return self.responses.get(key, self.default_response)
    
    def put(self, url: str, **kwargs) -> MockResponse:
        self.requests.append(('PUT', url, kwargs))
        key = f"PUT:{url}"
        return self.responses.get(key, self.default_response)
    
    def delete(self, url: str, **kwargs) -> MockResponse:
        self.requests.append(('DELETE', url, kwargs))
        key = f"DELETE:{url}"
        return self.responses.get(key, self.default_response)
    
    def patch(self, url: str, **kwargs) -> MockResponse:
        self.requests.append(('PATCH', url, kwargs))
        key = f"PATCH:{url}"
        return self.responses.get(key, self.default_response)


class MockServiceRegistry:
    """Mock service registry for testing."""
    
    def __init__(self):
        self.services = []
        
    def add_service(self, service_id: str, name: str, service_type: str, url: str):
        """Add a mock service."""
        from dnastack.client.service_registry.models import Service, ServiceType
        
        # Parse service type (e.g., "com.dnastack:collection-service:1.0.0")
        parts = service_type.split(':')
        if len(parts) == 3:
            group, artifact, version = parts
        else:
            group, artifact, version = 'com.dnastack', service_type, '1.0.0'
            
        service = Service(
            id=service_id,
            name=name,
            type=ServiceType(group=group, artifact=artifact, version=version),
            url=url
        )
        self.services.append(service)
        
    def list_services(self) -> List:
        """List all services."""
        return self.services
    
    def get_service(self, service_id: str):
        """Get a specific service by ID."""
        for service in self.services:
            if service.id == service_id:
                return service
        return None


class MockCollectionServiceClient:
    """Mock Collections service client."""
    
    def __init__(self):
        self.collections = {}
        
    def list_collections(self):
        """List all collections."""
        return list(self.collections.values())
    
    def get_collection(self, collection_id: str):
        """Get a specific collection."""
        return self.collections.get(collection_id)
    
    def create_collection(self, name: str, description: str = None) -> Dict[str, Any]:
        """Create a new collection."""
        collection_id = f"collection-{len(self.collections) + 1}"
        collection = {
            'id': collection_id,
            'name': name,
            'description': description or '',
            'items': []
        }
        self.collections[collection_id] = collection
        return collection


class MockDataConnectClient:
    """Mock Data Connect client."""
    
    def __init__(self):
        self.tables = {}
        self.query_results = []
        
    def list_tables(self):
        """List all tables."""
        return list(self.tables.keys())
    
    def get_table_info(self, table_name: str):
        """Get table information."""
        return self.tables.get(table_name)
    
    def query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a query."""
        return self.query_results
    
    def set_query_results(self, results: List[Dict[str, Any]]):
        """Set the results for the next query."""
        self.query_results = results