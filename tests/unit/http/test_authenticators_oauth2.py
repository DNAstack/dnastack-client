from time import time
from unittest import TestCase
from unittest.mock import Mock

import jwt
from requests import Response, Session

from dnastack import ServiceEndpoint
from dnastack.http.authenticators.abstract import ReauthenticationRequired
from dnastack.http.authenticators.oauth2 import OAuth2Authenticator
from dnastack.http.authenticators.oauth2_adapter.factory import OAuth2AdapterFactory
from dnastack.http.client_factory import HttpClientFactory
from dnastack.http.session_info import SessionManager, SessionInfo, SessionInfoHandler


class UnitTest(TestCase):
    def test_handle_non_existing_session(self):
        """ Automatically reset the token when the refresh token expires (#186428698) """

        # Set up the test authenticator.
        endpoint = ServiceEndpoint(url='https://dc.faux.dnastack.com')
        mock_auth_info = dict(grant_type='classified', resource_url=endpoint.url)
        session_manager = Mock(spec=SessionManager)
        adapter_factory = Mock(spec=OAuth2AdapterFactory)

        authenticator = OAuth2Authenticator(endpoint=endpoint,
                                            auth_info=mock_auth_info,
                                            session_manager=session_manager,
                                            adapter_factory=adapter_factory)

        # Set up the test.
        session_manager.restore = Mock(return_value=None)

        # Trigger the action.
        with self.assertRaises(ReauthenticationRequired):
            _ = authenticator.refresh()

    def test_handle_expired_refresh_token_with_token_endpoint(self):
        """
        Automatically reset the token when Wallet reports that the refresh token
        expires WITH the token endpoint defined (#186428698)
        """

        # Set up the test authenticator.
        endpoint = ServiceEndpoint(url='https://dc.faux.dnastack.com')
        mock_auth_info = dict(grant_type='classified',
                              resource_url=endpoint.url,
                              token_endpoint='https://auth.faux.dnastack.com/oauth/token')
        session_manager = Mock(spec=SessionManager)
        adapter_factory = Mock(spec=OAuth2AdapterFactory)
        mock_http_session = Mock(spec=Session)
        http_client_factory = Mock(spec=HttpClientFactory)
        http_client_factory.make = Mock(return_value=mock_http_session)

        authenticator = OAuth2Authenticator(endpoint=endpoint,
                                            auth_info=mock_auth_info,
                                            session_manager=session_manager,
                                            adapter_factory=adapter_factory,
                                            http_client_factory=http_client_factory)

        # Set up the test.
        issued_at = time() - 120
        valid_until = time() - 60
        refresh_token = jwt.encode(dict(iap=issued_at, exp=valid_until), 'fantasy')
        existing_session_info = SessionInfo(
            refresh_token=refresh_token,
            token_type='mock',
            issued_at=issued_at,
            valid_until=valid_until,
            handler=SessionInfoHandler(auth_info=mock_auth_info),
        )
        session_manager.restore = Mock(return_value=existing_session_info)

        # Trigger the action.
        with self.assertRaisesRegex(ReauthenticationRequired, r'Refresh token expired'):
                token_endpoint_response = Mock(Response)
                token_endpoint_response.ok = False
                token_endpoint_response.status_code = 400
                token_endpoint_response.headers = {'X-B3-Traceid': 'faux-trace-id'}
                token_endpoint_response.json.return_value = dict(
                    error_description='JWT expired at 2023-10-15T17:13:22Z. Current time: 2023-11-07T20:00:38Z, '
                                      'a difference of 1997236935 milliseconds.  Allowed clock skew: 0 milliseconds.'
                )

                mock_http_session.post.return_value = token_endpoint_response

                _ = authenticator.refresh()

    def test_handle_expired_refresh_token_without_token_endpoint(self):
        """
        Automatically reset the token when Wallet reports that the refresh token
        expires WITHOUT the token endpoint defined (#186428698)
        """

        # Set up the test authenticator.
        endpoint = ServiceEndpoint(url='https://dc.faux.dnastack.com')
        mock_auth_info = dict(grant_type='classified', resource_url=endpoint.url)
        session_manager = Mock(spec=SessionManager)
        adapter_factory = Mock(spec=OAuth2AdapterFactory)
        mock_http_session = Mock(spec=Session)
        http_client_factory = Mock(spec=HttpClientFactory)
        http_client_factory.make = Mock(return_value=mock_http_session)

        authenticator = OAuth2Authenticator(endpoint=endpoint,
                                            auth_info=mock_auth_info,
                                            session_manager=session_manager,
                                            adapter_factory=adapter_factory,
                                            http_client_factory=http_client_factory)

        # Set up the test.
        issued_at = time() - 120
        valid_until = time() - 60
        refresh_token = jwt.encode(dict(iap=issued_at, exp=valid_until), 'fantasy')
        existing_session_info = SessionInfo(
            refresh_token=refresh_token,
            token_type='mock',
            issued_at=issued_at,
            valid_until=valid_until,
            handler=SessionInfoHandler(auth_info=mock_auth_info),
        )
        session_manager.restore = Mock(return_value=existing_session_info)

        # Trigger the action.
        with self.assertRaisesRegex(ReauthenticationRequired, r'Re-authentication required as the client cannot request for a new token without the token endpoint defined.'):
            token_endpoint_response = Mock(Response)
            token_endpoint_response.ok = False
            token_endpoint_response.status_code = 400
            token_endpoint_response.headers = {'X-B3-Traceid': 'faux-trace-id'}
            token_endpoint_response.json.return_value = dict(
                error_description='JWT expired at 2023-10-15T17:13:22Z. Current time: 2023-11-07T20:00:38Z, '
                                  'a difference of 1997236935 milliseconds.  Allowed clock skew: 0 milliseconds.'
            )

            mock_http_session.post.return_value = token_endpoint_response

            _ = authenticator.refresh()
