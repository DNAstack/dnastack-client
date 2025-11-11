from unittest import TestCase

from dnastack import ServiceEndpoint
from dnastack.http.authenticators.factory import HttpAuthenticatorFactory


class TestHttpAuthenticatorFactory(TestCase):
    def test_filter_unsupported_grant_types(self):
        """
        Test that HttpAuthenticatorFactory filters out authentication methods
        with unsupported grant types like 'authorization_code'
        """
        # Create endpoints with different grant types
        device_code_endpoint = ServiceEndpoint(
            url='https://dc.faux.dnastack.com',
            authentication={
                'type': 'oauth2',
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                'client_id': 'device-client',
                'device_code_endpoint': 'https://auth.faux.dnastack.com/oauth/device/code',
                'token_endpoint': 'https://auth.faux.dnastack.com/oauth/token',
                'resource_url': 'https://dc.faux.dnastack.com'
            }
        )

        authorization_code_endpoint = ServiceEndpoint(
            url='https://workbench.faux.dnastack.com',
            authentication={
                'type': 'oauth2',
                'grant_type': 'authorization_code',
                'client_id': 'workbench-client',
                'token_endpoint': 'https://auth.faux.dnastack.com/oauth/token',
                'resource_url': 'https://workbench.faux.dnastack.com'
            }
        )

        client_credentials_endpoint = ServiceEndpoint(
            url='https://api.faux.dnastack.com',
            authentication={
                'type': 'oauth2',
                'grant_type': 'client_credentials',
                'client_id': 'api-client',
                'client_secret': 'secret123',
                'token_endpoint': 'https://auth.faux.dnastack.com/oauth/token',
                'resource_url': 'https://api.faux.dnastack.com'
            }
        )

        # Create authenticators - should only include device_code and client_credentials
        authenticators = HttpAuthenticatorFactory.create_multiple_from(
            endpoints=[
                device_code_endpoint,
                authorization_code_endpoint,
                client_credentials_endpoint
            ]
        )

        # Verify that only 2 authenticators were created (device_code and client_credentials)
        # The authorization_code endpoint should have been filtered out
        self.assertEqual(len(authenticators), 2,
                        "Should only create authenticators for supported grant types")

        # Verify the authenticators are for the correct endpoints
        auth_resource_urls = {auth._auth_info['resource_url'] for auth in authenticators}
        self.assertIn('https://dc.faux.dnastack.com', auth_resource_urls,
                     "Should include device_code endpoint")
        self.assertIn('https://api.faux.dnastack.com', auth_resource_urls,
                     "Should include client_credentials endpoint")
        self.assertNotIn('https://workbench.faux.dnastack.com', auth_resource_urls,
                        "Should NOT include authorization_code endpoint")

    def test_filter_all_supported_grant_types_pass_through(self):
        """
        Test that all supported grant types (device_code, client_credentials, token_exchange)
        are correctly passed through and not filtered
        """
        device_code_endpoint = ServiceEndpoint(
            url='https://dc.faux.dnastack.com',
            authentication={
                'type': 'oauth2',
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
                'client_id': 'device-client',
                'device_code_endpoint': 'https://auth.faux.dnastack.com/oauth/device/code',
                'token_endpoint': 'https://auth.faux.dnastack.com/oauth/token',
                'resource_url': 'https://dc.faux.dnastack.com'
            }
        )

        client_credentials_endpoint = ServiceEndpoint(
            url='https://api.faux.dnastack.com',
            authentication={
                'type': 'oauth2',
                'grant_type': 'client_credentials',
                'client_id': 'api-client',
                'client_secret': 'secret123',
                'token_endpoint': 'https://auth.faux.dnastack.com/oauth/token',
                'resource_url': 'https://api.faux.dnastack.com'
            }
        )

        token_exchange_endpoint = ServiceEndpoint(
            url='https://exchange.faux.dnastack.com',
            authentication={
                'type': 'oauth2',
                'grant_type': 'urn:ietf:params:oauth:grant-type:token-exchange',
                'client_id': 'exchange-client',
                'token_endpoint': 'https://auth.faux.dnastack.com/oauth/token',
                'resource_url': 'https://exchange.faux.dnastack.com'
            }
        )

        # Create authenticators - should include all 3
        authenticators = HttpAuthenticatorFactory.create_multiple_from(
            endpoints=[
                device_code_endpoint,
                client_credentials_endpoint,
                token_exchange_endpoint
            ]
        )

        # Verify all 3 authenticators were created
        self.assertEqual(len(authenticators), 3,
                        "Should create authenticators for all supported grant types")

        # Verify the authenticators are for the correct endpoints
        auth_resource_urls = {auth._auth_info['resource_url'] for auth in authenticators}
        self.assertIn('https://dc.faux.dnastack.com', auth_resource_urls)
        self.assertIn('https://api.faux.dnastack.com', auth_resource_urls)
        self.assertIn('https://exchange.faux.dnastack.com', auth_resource_urls)