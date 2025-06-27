
from dnastack.common.environments import env, flag
from tests.cli.auth_utils import handle_device_code_flow
from tests.cli.base import DeprecatedPublisherCliTestCase
from tests.exam_helper import publisher_client_id, publisher_client_secret, token_endpoint


class TestAuthentication(DeprecatedPublisherCliTestCase):
    test_resource_id = 'test-data-connect'
    test_resource_url = env('E2E_DATA_CONNECT_URL', default=DeprecatedPublisherCliTestCase._explorer_base_url)

    @staticmethod
    def reuse_session() -> bool:
        return False

    @staticmethod
    def automatically_authenticate() -> bool:
        return False

    def setUp(self) -> None:
        super().setUp()
        self._add_endpoint(self.test_resource_id, 'data_connect', self.test_resource_url)

    def test_client_credentials_flow(self):
        if not flag('E2E_CLIENT_CREDENTIAL_AUTH_TEST_ENABLED'):
            self.skipTest('The test is disabled but the feature is available for development.')

        self._configure_endpoint(
            self.test_resource_id,
            {
                'authentication.client_id': publisher_client_id,
                'authentication.client_secret': publisher_client_secret,
                'authentication.grant_type': 'client_credentials',
                'authentication.resource_url': self.test_resource_url,
                'authentication.token_endpoint': token_endpoint,
            }
        )

        result = self.invoke('auth', 'login')
        self.assertEqual(0, result.exit_code, 'Logging into all endpoints should also work.')

        auth_state = self._get_auth_state_for(self.test_resource_id)
        self.assertEqual(auth_state['status'], 'ready', 'The authenticator should be ready to use.')
        self.assertEqual(auth_state['auth_info']['resource_url'], self.test_resource_url,
                         'The resource URL should be the same as the test resource URL.')

        result = self.invoke('auth', 'revoke', '--force')
        self.assertEqual(0, result.exit_code, 'Revoking all sessions should also work.')

        auth_state = self._get_auth_state_for(self.test_resource_id)
        self.assertEqual(auth_state['status'], 'uninitialized', 'The authenticator should be NOT ready to use.')
        self.assertEqual(auth_state['auth_info']['resource_url'], self.test_resource_url,
                         'The resource URL should be the same as the test resource URL.')

        result = self.invoke('auth', 'login', '--endpoint-id', self.test_resource_id)
        self.assertEqual(0, result.exit_code, 'The login command with a single endpoint should also work.')

        auth_state = self._get_auth_state_for(self.test_resource_id)
        self.assertEqual(auth_state['status'], 'ready', 'The authenticator should be ready to use.')
        self.assertEqual(auth_state['auth_info']['resource_url'], self.test_resource_url,
                         'The resource URL should be the same as the test resource URL.')

        result = self.invoke('auth', 'revoke', '--force', '--endpoint-id', self.test_resource_id)
        self.assertEqual(0, result.exit_code, 'Revoking one session related to the test resource should also work.')

        auth_state = self._get_auth_state_for(self.test_resource_id)
        self.assertEqual(auth_state['status'], 'uninitialized', 'The authenticator should be NOT ready to use.')
        self.assertEqual(auth_state['auth_info']['resource_url'], self.test_resource_url,
                         'The resource URL should be the same as the test resource URL.')

    def _get_auth_state_for(self, endpoint_id: str):
        result = self.simple_invoke('auth', 'status')
        for state in result:
            self.assert_not_empty(state['endpoints'], 'There should be at least one endpoints.')

        try:
            return [state for state in result if endpoint_id in state['endpoints']][0]
        except (KeyError, IndexError):
            raise RuntimeError('Unable to get the state of the authenticator for the test resource')

    def test_device_code_flow(self):
        self.prepare_for_device_code_flow(env('E2E_PUBLISHER_AUTH_DEVICE_CODE_TEST_EMAIL'),
                                          env('E2E_PUBLISHER_AUTH_DEVICE_CODE_TEST_TOKEN'))

        self.invoke('use', self._explorer_hostname, '--no-auth')

        auth_cmd = ['python', '-m', 'dnastack', 'auth', 'login']
        handle_device_code_flow(auth_cmd, self._states['email'], self._states['token'])

    def test_login_does_not_attempt_token_exchange(self):
        """
        Regression test for issue where 'dnastack auth login' was attempting token exchange
        and failing with "No cloud provider detected" error.
        This test ensures that login command skips token exchange authentication methods unless explicitly requested.
        """
        token_exchange_endpoint_id = 'test-token-exchange'
        token_exchange_url = env('E2E_TOKEN_EXCHANGE_URL', default='https://api.dnastack.com')
        self._add_endpoint(token_exchange_endpoint_id, 'data_connect', token_exchange_url)
        self._configure_endpoint(
            token_exchange_endpoint_id,
            {
                'authentication.client_id': 'token-exchange-client',
                'authentication.client_secret': 'token-exchange-secret',
                'authentication.grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
                'authentication.resource_url': token_exchange_url,
                'authentication.token_endpoint': token_endpoint,
            }
        )
        result = self.invoke('auth', 'status', '--output', 'json')
        self.assertEqual(0, result.exit_code, 'Auth status should work')
        
        result = self.invoke('auth', 'login')
        self.assertNotIn('AuthException', result.output,
                         'Token exchange error should not appear during login')
        self.assertNotIn('TokenExchangeAdapter', result.output,
                         'Token exchange adapter should not be invoked during login')
