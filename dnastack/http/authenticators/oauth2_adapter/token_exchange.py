from typing import Dict, Any, List, Optional

from imagination import container

from dnastack.common.tracing import Span
from dnastack.http.authenticators.oauth2_adapter.abstract import OAuth2Adapter, AuthException
from dnastack.http.authenticators.oauth2_adapter.models import OAuth2Authentication, GRANT_TYPE_TOKEN_EXCHANGE
from dnastack.http.authenticators.oauth2_adapter.cloud_providers import (
    CloudProviderFactory, CloudMetadataProvider, CloudMetadataConfig
)
from dnastack.http.client_factory import HttpClientFactory


class TokenExchangeAdapter(OAuth2Adapter):
    __grant_type = GRANT_TYPE_TOKEN_EXCHANGE
    __subject_token_type = 'urn:ietf:params:oauth:token-type:jwt'
    __METADATA_TIMEOUT = 10
    
    def __init__(self, auth_info: OAuth2Authentication):
        super().__init__(auth_info)
        self._cloud_provider: Optional[CloudMetadataProvider] = None

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
        if self._auth_info.subject_token:
            return self._auth_info.subject_token
        
        context_subject_token = self._get_and_clear_context_subject_token()
        if context_subject_token:
            return context_subject_token

        audience = self._auth_info.audience or self._auth_info.client_id or self._auth_info.resource_url
        token = self._fetch_cloud_identity_token(audience, trace_context)
        if token:
            return token
        
        raise AuthException(
            'No subject token provided and unable to fetch from cloud. '
            'Please provide a subject token or run from a supported cloud environment.'
        )
    
    def _fetch_cloud_identity_token(self, audience: str, trace_context: Span) -> Optional[str]:
        """Fetch identity token from cloud metadata service."""
        logger = trace_context.create_span_logger(self._logger)
        
        if self._cloud_provider:
            logger.debug(f'Attempting to fetch identity token from {self._cloud_provider.name}')
            token = self._cloud_provider.get_identity_token(audience, trace_context)
            if token:
                return token
            logger.error(f'Failed to fetch token from configured provider: {self._cloud_provider.name}')
        
        logger.info('Auto-detecting cloud provider...')
        config = CloudMetadataConfig(timeout=self.__METADATA_TIMEOUT)
        detected_provider = CloudProviderFactory.detect_provider(config)
        if detected_provider:
            logger.info(f'Detected cloud provider: {detected_provider.name}')
            self._cloud_provider = detected_provider
            token = detected_provider.get_identity_token(audience, trace_context)
            if token:
                return token
            logger.error(f'Failed to fetch token from detected provider: {detected_provider.name}')
        else:
            logger.error('No cloud provider detected')
        
        return None

    def _get_and_clear_context_subject_token(self) -> Optional[str]:
        """Get subject token from current context if available and clear it after use"""
        from dnastack.context.manager import ContextManager
        context_manager = container.get(ContextManager)
        current_context = context_manager.contexts.current_context
        if current_context and current_context.platform_subject_token:
            token = current_context.platform_subject_token
            current_context.platform_subject_token = None
            context_manager.contexts.set(context_manager.contexts.current_context_name, current_context)
            return token
        return None

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
            cloud_provider=self._cloud_provider.name if self._cloud_provider else 'none',
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