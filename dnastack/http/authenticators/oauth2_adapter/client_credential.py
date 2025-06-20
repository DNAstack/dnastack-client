from typing import Dict, Any, List

from dnastack.common.tracing import Span
from dnastack.http.authenticators.oauth2_adapter.abstract import OAuth2Adapter, AuthException
from dnastack.http.client_factory import HttpClientFactory


class ClientCredentialAdapter(OAuth2Adapter):
    __grant_type = 'client_credentials'

    @staticmethod
    def get_expected_auth_info_fields() -> List[str]:
        return [
            'client_id',
            'client_secret',
            'grant_type',
            'resource_url',
            'token_endpoint',
        ]

    def exchange_tokens(self, trace_context: Span) -> Dict[str, Any]:
        logger = trace_context.create_span_logger(self._logger)

        auth_info = self._auth_info
        resource_urls = self._prepare_resource_urls_for_request(auth_info.resource_url)

        trace_info = dict(
            oauth='client-credentials',
            token_url=auth_info.token_endpoint,
            client_id=auth_info.client_id,
            grant_type=self.__grant_type,
            resource_urls=resource_urls,
            scope=auth_info.scope,
        )
        logger.debug(f'exchange_token: Authenticating with {trace_info}')

        auth_params = dict(
            client_id=auth_info.client_id,
            client_secret=auth_info.client_secret,
            grant_type=self.__grant_type,
            resource=resource_urls,
        )

        if auth_info.scope:
            auth_params['scope'] = auth_info.scope

        with trace_context.new_span(metadata=trace_info) \
                as sub_span:
            sub_logger = sub_span.create_span_logger(self._logger)
            with HttpClientFactory.make() as http_session:
                span_headers = sub_span.create_http_headers()
                response = http_session.post(auth_info.token_endpoint, data=auth_params, headers=span_headers)

            sub_logger.debug(f'exchange_tokens: {auth_info.token_endpoint}: HTTP {response.status_code}:\n{response.text}')

            if not response.ok:
                sub_logger.debug('exchange_token: Token exchange fails.')
                raise AuthException(f'Failed to perform client-credential authentication for '
                                    f'{auth_info.client_id} as the server responds with HTTP {response.status_code}:'
                                    f'\n\n{response.text}\n',
                                    resource_urls)

            sub_logger.debug('exchange_token: Token exchange OK')
            return response.json()
