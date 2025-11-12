from typing import List, Any, Dict, Optional
import logging

from dnastack.client.models import ServiceEndpoint
from dnastack.common.model_mixin import JsonModelMixin
from dnastack.http.authenticators.abstract import Authenticator
from dnastack.http.authenticators.oauth2 import OAuth2Authenticator
from dnastack.http.authenticators.oauth2_adapter.models import OAuth2Authentication, SUPPORTED_GRANT_TYPES


class UnsupportedAuthenticationInformationError(RuntimeError):
    pass


class HttpAuthenticatorFactory:
    @staticmethod
    def create_multiple_from(endpoint: Optional[ServiceEndpoint] = None,
                             endpoints: Optional[List[ServiceEndpoint]] = None) -> List[Authenticator]:
        iterating_endpoints: List[ServiceEndpoint] = []

        if endpoint:
            iterating_endpoints.append(endpoint)

        if endpoints:
            iterating_endpoints.extend(endpoints)

        return [
            OAuth2Authenticator.make(endpoint, HttpAuthenticatorFactory._parse_auth_info(auth_info))
            for auth_info in HttpAuthenticatorFactory.get_unique_auth_info_list(iterating_endpoints)
        ]

    @staticmethod
    def _parse_auth_info(auth_info: Dict[str, Any]) -> Dict[str, Any]:
        auth_type = auth_info.get('type') or 'oauth2'
        if auth_type == 'oauth2':
            # Use the model to validate the configuration.
            config = OAuth2Authentication(**auth_info)

            # NOTE: Should raise a custom exception if it fails the model validation.

            return config.model_dump()
        else:
            raise UnsupportedAuthenticationInformationError(auth_info)

    @staticmethod
    def get_unique_auth_info_list(endpoints: List[ServiceEndpoint]) -> List[Dict[str, Any]]:
        logger = logging.getLogger(__name__)
        unique_auth_info_map: Dict[str, Dict[str, Any]] = {}

        for endpoint in endpoints:
            for auth_info in endpoint.get_authentications():
                grant_type = auth_info.get('grant_type')

                # Skip authentication methods with unsupported grant types
                if grant_type and grant_type not in SUPPORTED_GRANT_TYPES:
                    logger.debug("Skipping authentication with unsupported grant type '{}' for resource '{}'".format(
                        grant_type,
                        auth_info.get('resource_url', 'unknown')
                    ))
                    continue

                unique_auth_info_map[JsonModelMixin.hash(auth_info)] = auth_info

        return sorted(unique_auth_info_map.values(), key=lambda a: a.get('resource_url') or a.get('type'))
