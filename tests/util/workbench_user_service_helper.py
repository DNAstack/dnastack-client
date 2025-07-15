from urllib.parse import urljoin

from dnastack.client.workbench.workbench_user_service.models import WorkbenchUser
from dnastack.common.environments import env
from dnastack.http.session import HttpSession
from tests.util.wallet_hellper import WalletHelper


class WorkbenchUserServiceHelper:
    _wallet_base_uri = env('E2E_WORKBENCH_WALLET_BASE_URI', required=False, default='http://localhost:8081')
    _wallet_admin_client_id = env('E2E_WORKBENCH_WALLET_CLIENT_ID', required=False, default='workbench-frontend-e2e-test')
    _wallet_admin_client_secret = env('E2E_WORKBENCH_WALLET_CLIENT_SECRET', required=False,
                                      default='dev-secret-never-use-in-prod')
    _wallet_helper = WalletHelper(_wallet_base_uri, _wallet_admin_client_id, _wallet_admin_client_secret)

    _workbench_user_service_base_uri = env('E2E_WORKBENCH_USER_SERVICE_BASE_URL', required=False,
                                           default='http://localhost:9193')
    _workbench_user_service_scope = "users"

    @staticmethod
    def _create_http_session(suppress_error: bool = False, no_auth: bool = False) -> HttpSession:
        """Create HTTP session wrapper"""
        session = HttpSession(suppress_error=suppress_error, enable_auth=(not no_auth))
        return session

    def register_user(self, email: str) -> WorkbenchUser:
        access_token = self._wallet_helper.get_access_token(f'{self._workbench_user_service_base_uri}/',
                                                            self._workbench_user_service_scope)
        data = {
            'email': (None, email)
        }
        with self._create_http_session() as session:
            response = session.post(urljoin(self._workbench_user_service_base_uri,
                                            'users'),
                                    data=data,
                                    headers={
                                        'Authorization': f'Bearer {access_token}',
                                        'Content-Type': 'application/x-www-form-urlencoded'
                                    })
            return WorkbenchUser(**response.json())
