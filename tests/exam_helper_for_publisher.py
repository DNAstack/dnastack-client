import json
import re
from typing import List, Optional, Callable

from dnastack import ServiceEndpoint
from dnastack.client.factory import EndpointRepository
from dnastack.client.workbench.ewes.client import EWesClient
from dnastack.common.environments import env
from dnastack.http.session import HttpSession
from tests.exam_helper import WithTestUserTestCase


def create_publisher_login_handler(app_base_url: str) -> Callable:
    """
    Create a custom login handler for Publisher application.

    Args:
        app_base_url: Base URL of the Publisher application

    Returns:
        Callable that handles the login flow
    """
    def publisher_login_handler(session) -> HttpSession:
        # Get the frontend configuration first
        response = session.get(app_base_url)

        # Extract the frontend config from the script tag
        config_match = re.search(r'window\.frontendConfig\s*=\s*({.*?});', response.text, re.DOTALL)
        if not config_match:
            raise ValueError("Could not find frontend configuration")

        frontend_config = json.loads(config_match.group(1))

        # Get the OAuth login URL from config
        oauth_login_url = frontend_config.get('oauthLoginUrl')
        if not oauth_login_url:
            raise ValueError("Could not find OAuth login URL in frontend config")

        # Remove select_account prompt if present
        oauth_login_url_without_prompt = oauth_login_url.replace('&prompt=select_account', '')

        # Follow redirect chain
        response = session.get(oauth_login_url_without_prompt, allow_redirects=True)

        return session

    return publisher_login_handler


class BasePublisherTestCase(WithTestUserTestCase):
    _wallet_base_uri = env(
        'E2E_PUBLISHER_WALLET_BASE_URI',
        required=False,
        default='http://localhost:8081')
    _wallet_admin_client_id = env(
        'E2E_PUBLISHER_WALLET_CLIENT_ID',
        required=False,
        default='data-lake-frontend-e2e-test'
    )
    _wallet_admin_client_secret = env(
        'E2E_PUBLISHER_WALLET_CLIENT_SECRET',
        required=False,
        default='dev-secret-never-use-in-prod'
    )

    publisher_base_url = env('E2E_PUBLISHER_BASE_URL', required=False, default='http://localhost:8000')
    service_registry_base_url = env('E2E_SERVICE_REGISTRY_BASE_URL', required=False, default='http://localhost:8085')
    collection_service_base_url = env('E2E_COLLECTION_SERVICE_BASE_URL', required=False, default='http://localhost:8093')

    publisher_wallet_admin_group = env('E2E_PUBLISHER_WALLET_ADMIN_GROUP', required=False, default='data-lake-active-admins')
    publisher_wallet_test_users_group = env('E2E_PUBLISHER_WALLET_TEST_USERS_GROUP', required=False, default='data-lake-test-users')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    @classmethod
    def get_factory(cls) -> EndpointRepository:
        return cls.get_context_manager().use(cls.get_context_urls()[0], no_auth=True)

    @classmethod
    def get_context_urls(cls) -> List[str]:
        return [f'{cls.service_registry_base_url}']

    @classmethod
    def get_app_url(cls) -> str:
        return cls.publisher_base_url

    @classmethod
    def do_on_setup_class_before_auth(cls) -> None:
        super().do_on_setup_class_before_auth()

        cls._base_logger.info(f'Class {cls.__name__}: Adding test user to groups [{cls.publisher_wallet_admin_group}, {cls.publisher_wallet_test_users_group}]')
        cls._get_wallet_helper().add_test_user_to_group(cls.test_user, cls.publisher_wallet_admin_group)
        cls._get_wallet_helper().add_test_user_to_group(cls.test_user, cls.publisher_wallet_test_users_group)

        custom_handler = create_publisher_login_handler(app_base_url=cls.publisher_base_url)
        with cls._wallet_helper.log_in_with_personal_token(
            email=cls.test_user.email,
            personal_access_token=cls.test_user.personalAccessToken,
            custom_login_handler=custom_handler
        ):
            # You can use the session here for set up actions
            print("Setting up")

    @classmethod
    def do_on_teardown_class(cls) -> None:
        cls._base_logger.info(f'Class {cls.__name__}: Removing test user from groups [{cls.publisher_wallet_admin_group}, {cls.publisher_wallet_test_users_group}]')
        cls._get_wallet_helper().remove_test_user_from_group(cls.test_user, cls.publisher_wallet_admin_group)
        cls._get_wallet_helper().remove_test_user_from_group(cls.test_user, cls.publisher_wallet_test_users_group)

        custom_handler = create_publisher_login_handler(app_base_url=cls.publisher_base_url)
        with cls._wallet_helper.log_in_with_personal_token(
                email=cls.test_user.email,
                personal_access_token=cls.test_user.personalAccessToken,
                custom_login_handler=custom_handler
        ):
            # You can use the session here for clean up actions
            print("Cleaning up")

        # Delete test user and policy as last
        super().do_on_teardown_class()

    @classmethod
    def _get_collection_service_endpoints(cls) -> List[ServiceEndpoint]:
        # noinspection PyUnresolvedReferences
        factory: EndpointRepository = cls.get_factory()

        return [
            endpoint
            for endpoint in factory.all()
            if endpoint.type in EWesClient.get_supported_service_types()
        ]

    @classmethod
    def get_collection_service_client(cls, index: int = 0) -> Optional[EWesClient]:
        compatible_endpoints = cls._get_collection_service_endpoints()

        if not compatible_endpoints:
            raise RuntimeError('No ewes-service compatible endpoints for this test')

        if index >= len(compatible_endpoints):
            raise RuntimeError(f'Requested ewes-service compatible endpoint #{index} but it does not exist.')

        compatible_endpoint = compatible_endpoints[index]

        return EWesClient.make(compatible_endpoint, cls.namespace)

