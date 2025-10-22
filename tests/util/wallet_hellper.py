from base64 import b64encode
from typing import Optional, List
from urllib.parse import urljoin

from pydantic import BaseModel

from dnastack.http.session import HttpSession


class TestUser(BaseModel):
    id: str
    email: str
    personalAccessToken: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_in: int
    scope: Optional[str] = None


class Principal(BaseModel):
    type: str
    email: Optional[str] = None


class Resource(BaseModel):
    uri: str


class Statement(BaseModel):
    actions: List[str]
    principals: List[Principal]
    resources: List[Resource]


class Policy(BaseModel):
    id: str
    version: Optional[str] = None
    statements: List[Statement]
    tags: Optional[List[str]] = None


class WalletHelper:
    def __init__(self, wallet_base_uri: str, client_id: str, client_secret: str):
        self.__wallet_base_uri = wallet_base_uri
        self.__admin_client_id = client_id
        self.__admin_client_secret = client_secret
        self.__wallet_resource = f'{wallet_base_uri}/'
        self.__oauth_login_path = '/oauth/login'
        self.__select_account_prompt = '&prompt=select_account'

    @staticmethod
    def _create_http_session(suppress_error: bool = False, no_auth: bool = False) -> HttpSession:
        """Create HTTP session wrapper"""
        session = HttpSession(suppress_error=suppress_error, enable_auth=(not no_auth))
        return session

    def _basic_auth(self) -> str:
        token = b64encode(f"{self.__admin_client_id}:{self.__admin_client_secret}".encode('utf-8')).decode("ascii")
        return f'Basic {token}'

    def _bearer_auth(self) -> str:
        return f'Bearer {self.get_access_token(self.__wallet_resource)}'

    def get_access_token(self, resource: str, scope: Optional[str] = '') -> str:
        with self._create_http_session() as session:
            response = session.post(urljoin(self.__wallet_base_uri,
                                            '/oauth/token'),
                                    params={'grant_type': 'client_credentials', 'resource': resource, 'scope': scope},
                                    headers={'Authorization': self._basic_auth()})
            return TokenResponse(**response.json()).access_token

    def configure_oauth_settings(self,
                                 oauth_login_path: str = '/oauth/login',
                                 select_account_prompt: str = '&prompt=select_account') -> None:
        """
        Configure OAuth-related settings for the application.

        Args:
            oauth_login_path: The path for OAuth login endpoint
            select_account_prompt: The prompt parameter to remove from redirect URL
        """
        self.__oauth_login_path = oauth_login_path
        self.__select_account_prompt = select_account_prompt

    def log_in_with_personal_token(self,
                                   email: str,
                                   personal_access_token: str,
                                   app_base_url: Optional[str] = None,
                                   custom_login_handler: Optional[callable] = None) -> HttpSession:
        """
        Sign in using personal access token with more flexibility.

        Args:
            email: User's email
            personal_access_token: User's personal access token
            app_base_url: Optional base URL of the application
            custom_login_handler: Optional function to handle custom login flow

        Returns:
            HttpSession with authenticated session
        """
        session = self._create_http_session()

        # First authenticate with wallet
        session.get(
            urljoin(self.__wallet_base_uri, '/login/token'),
            params={'email': email, 'token': personal_access_token}
        )

        # If custom login handler is provided, use it
        if custom_login_handler:
            return custom_login_handler(session)

        # If app_base_url is provided, proceed with default OAuth flow
        if app_base_url:
            # Get the redirect URL
            response = session.get(
                urljoin(app_base_url, self.__oauth_login_path),
                allow_redirects=False
            )

            if 'Location' in response.headers:
                # Remove select account prompt if configured
                redirect_url = response.headers['Location']
                if self.__select_account_prompt:
                    redirect_url = redirect_url.replace(self.__select_account_prompt, '')

                # Follow redirect
                response = session.get(redirect_url, allow_redirects=True)

        return session

    def create_test_user(self, username: str) -> TestUser:
        with self._create_http_session() as session:
            response = session.post(urljoin(self.__wallet_base_uri, f'/test/users?username={username}'),
                                    headers={'Authorization': self._bearer_auth()})
            return TestUser(**response.json())

    def delete_test_user(self, email: str) -> None:
        with self._create_http_session() as session:
            session.delete(urljoin(self.__wallet_base_uri, f'/test/users/{email}'),
                           headers={'Authorization': self._bearer_auth()})

    def create_access_policy(self, policy: Policy) -> Policy:
        with self._create_http_session() as session:
            response = session.post(urljoin(self.__wallet_base_uri, '/policies'),
                                    json=policy.model_dump(),
                                    headers={'Authorization': self._bearer_auth()})
            created_policy = Policy(**response.json())
            created_policy.version = response.headers['ETag'].replace('\"', '')
            return created_policy

    def delete_access_policy(self, policy_id: str, policy_version: str) -> None:
        with self._create_http_session() as session:
            session.delete(urljoin(self.__wallet_base_uri, f'/policies/{policy_id}'),
                           headers={'Authorization': self._bearer_auth(), 'If-Match': policy_version})

    def add_test_user_to_group(self, test_user: TestUser, group_id: str) -> None:
        """
        Add a TestUser to a Wallet group.

        Args:
            test_user: TestUser instance
            group_id: Group ID to add the user to
        """
        self.add_user_to_group(test_user.email, group_id)

    def remove_test_user_from_group(self, test_user: TestUser, group_id: str) -> None:
        """
        Remove a TestUser from a Wallet group.

        Args:
            test_user: TestUser instance
            group_id: Group ID to add the user to
        """
        self.remove_user_from_group(test_user.email, group_id)

    def add_user_to_group(self, email: str, group_id: str) -> None:
        """
        Add a user to a Wallet group with retry on conflict.

        Args:
            email: User's email
            group_id: Group ID to add the user to
        """
        status = self._add_user_to_group_internal(email, group_id)

        # Retry once if we got a conflict (409)
        if status == 409:
            self._add_user_to_group_internal(email, group_id)

    def _add_user_to_group_internal(self, email: str, group_id: str) -> int:
        """
        Internal method to add user to group.

        Args:
            email: User's email
            group_id: Group ID to add the user to

        Returns:
            HTTP status code
        """
        operations = [
            {
                "op": "add",
                "path": "/members/-",
                "value": {"email": email}
            }
        ]

        # Get current version (ETag)
        with self._create_http_session() as session:
            response = session.get(
                urljoin(self.__wallet_base_uri, f'/principals/groups/{group_id}/members'),
                headers={'Authorization': self._bearer_auth()}
            )
            version = response.headers['ETag'].replace('"', '')

            # Add member
            response = session.json_patch(
                urljoin(self.__wallet_base_uri, f'/principals/groups/{group_id}/members'),
                json=operations,
                headers={
                    'Authorization': self._bearer_auth(),
                    'Content-Type': 'application/json-patch+json',
                    'If-Match': version
                }
            )

            return response.status_code

    def remove_user_from_group(self, email: str, group_id: str) -> None:
        """
        Remove a user from a Wallet group.

        Args:
            email: User's email
            group_id: Group ID to remove the user from
        """
        with self._create_http_session() as session:
            session.delete(
                urljoin(self.__wallet_base_uri, f'/principals/groups/{group_id}/members/{email}'),
                headers={'Authorization': self._bearer_auth()}
            )
