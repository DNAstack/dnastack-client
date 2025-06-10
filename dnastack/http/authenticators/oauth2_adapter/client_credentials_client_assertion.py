from typing import Dict, Any, List

import requests

from dnastack.common.tracing import Span
from dnastack.http.authenticators.oauth2_adapter.abstract import OAuth2Adapter, AuthException


class ClientCredentialsClientAssertionAdapter(OAuth2Adapter):
    __grant_type = 'client_credentials'

    @staticmethod
    def get_expected_auth_info_fields() -> List[str]:
        return [
            'client_id',
            'client_assertion_file', # normally at /var/run/secrets/kubernetes.io/serviceaccount/token
            'grant_type',
            'resource_url',
            'token_endpoint',
        ]

    def exchange_tokens(self, trace_context: Span) -> Dict[str, Any]:
        auth_info = self._auth_info
        resource_urls = self._prepare_resource_urls_for_request(auth_info.resource_url)
        with open(auth_info.client_assertion_file, 'r') as f:
            client_assertion = f.read()
        auth_params = dict(
            client_id=auth_info.client_id,
            grant_type=self.__grant_type,
            resource=resource_urls,
            client_assertion_type='urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
            client_assertion=client_assertion,
        )

        if auth_info.scope:
            auth_params['scope'] = auth_info.scope

        with trace_context.new_span(metadata={'oauth': 'client-credentials', 'init_url': auth_info.token_endpoint}) \
                as sub_span:
            span_headers = sub_span.create_http_headers()
            response = requests.post(auth_info.token_endpoint, data=auth_params, headers=span_headers)

        if not response.ok:
            raise AuthException(f'Client assertion authentication for {auth_info.client_id} failed with '
                                f'HTTP {response.status_code}:\n\n{response.text}\n',
                                resource_urls)

        return response.json()
