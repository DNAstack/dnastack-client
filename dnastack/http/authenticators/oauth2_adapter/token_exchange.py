from typing import Dict, Any, List

from dnastack.common.tracing import Span
from dnastack.http.authenticators.oauth2_adapter.abstract import OAuth2Adapter, AuthException
from dnastack.http.authenticators.oauth2_adapter.models import OAuth2Authentication
from dnastack.http.client_factory import HttpClientFactory


class TokenExchangeAdapter(OAuth2Adapter):
    __grant_type = 'urn:ietf:params:oauth:grant-type:token-exchange'
    __subject_token_type = 'urn:ietf:params:oauth:token-type:jwt'
    __METADATA_TIMEOUT = 5
    __GCP_METADATA_FLAVOR = 'Google'
    __GCP_METADATA_BASE_URL = 'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity'
    
    @classmethod
    def is_compatible_with(cls, auth_info: OAuth2Authentication) -> bool:
        if auth_info.grant_type != cls.__grant_type:
            return False
        required_fields = ['token_endpoint', 'resource_url']
        return all(getattr(auth_info, field, None) for field in required_fields)

    @staticmethod
    def get_expected_auth_info_fields() -> List[str]:
        return [
            'grant_type',
            'resource_url',
            'token_endpoint',
        ]

    def _get_subject_token(self, trace_context: Span) -> str:
        """
        Get ID token from cloud metadata service or use provided token.
        For re-authentication, always tries cloud metadata fetch.
        """
        logger = trace_context.create_span_logger(self._logger)
        
        if self._auth_info.subject_token:
            return self._auth_info.subject_token
        
        audience = self._auth_info.audience or self._auth_info.resource_url
        
        # TODO: refactor to handle multiple clouds
        metadata_url = (
            f'{self.__GCP_METADATA_BASE_URL}?audience={audience}&format=full'
        )
        
        try:
            with HttpClientFactory.make() as http_session:
                response = http_session.get(
                    metadata_url,
                    headers={'Metadata-Flavor': self.__GCP_METADATA_FLAVOR}, # TODO: refactor to handle multiple clouds
                    timeout=self.__METADATA_TIMEOUT
                )
                if response.ok:
                    token = response.text.strip()
                    return token
                else:
                    logger.warning(f'cloud service returned {response.status_code}')
        except Exception as e:
            logger.warning(f'Failed to fetch token from cloud service: {e}')
        
        raise AuthException(
            'No subject token provided and unable to fetch from cloud. '
            'Please provide a subject token or run from a cloud environment.'
        )

    def exchange_tokens(self, trace_context: Span) -> Dict[str, Any]:
        logger = trace_context.create_span_logger(self._logger)
        auth_info = self._auth_info
        resource_urls = self._prepare_resource_urls_for_request(auth_info.resource_url)
        subject_token = self._get_subject_token(trace_context)
        client_id = auth_info.client_id
        client_secret = auth_info.client_secret

        trace_info = dict(
            oauth='token-exchange',
            token_url=auth_info.token_endpoint,
            client_id=client_id,
            grant_type=self.__grant_type,
            resource_urls=resource_urls,
            subject_token_type=self.__subject_token_type,
        )
        logger.debug(f'exchange_token: Authenticating with {trace_info}')
        auth_params = {
            'grant_type': self.__grant_type,
            'subject_token_type': self.__subject_token_type,
            'subject_token': subject_token,
            'resource': resource_urls,
            **({'requested_token_type': self._auth_info.requested_token_type} if self._auth_info.requested_token_type else {}),
            **({'scope': auth_info.scope} if auth_info.scope else {})
        }

        with trace_context.new_span(metadata=trace_info) as sub_span:
            with HttpClientFactory.make() as http_session:
                span_headers = sub_span.create_http_headers()
                response = http_session.post(
                    auth_info.token_endpoint,
                    data=auth_params,
                    headers=span_headers,
                    auth=(client_id, client_secret)
                )

            if not response.ok:
                raise AuthException(
                    f'Failed to perform token exchange for {client_id} as the server responds with HTTP {response.status_code}:'
                    f'\n\n{response.text}\n',
                    resource_urls
                )

            return response.json()