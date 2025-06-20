from time import time, sleep
from typing import Dict, Any, List

from imagination import container

from dnastack.common.console import Console
from dnastack.common.environments import env
from dnastack.common.tracing import Span
from dnastack.http.authenticators.oauth2_adapter.abstract import OAuth2Adapter, AuthException
from dnastack.http.authenticators.oauth2_adapter.models import OAuth2Authentication
from dnastack.http.client_factory import HttpClientFactory


class DeviceCodeFlowAdapter(OAuth2Adapter):
    __grant_type = 'urn:ietf:params:oauth:grant-type:device_code'

    def __init__(self, auth_info: OAuth2Authentication):
        super(DeviceCodeFlowAdapter, self).__init__(auth_info)
        self.__console: Console = container.get(Console)

    @staticmethod
    def get_expected_auth_info_fields() -> List[str]:
        return [
            'client_id',
            # 'client_secret',  # It is usually defined by our service registry but it is not required.
            'device_code_endpoint',
            'grant_type',
            'resource_url',
            'token_endpoint',
        ]

    def exchange_tokens(self, trace_context: Span) -> Dict[str, Any]:
        logger = trace_context.create_span_logger(self._logger)

        session = HttpClientFactory.make()

        auth_info = self._auth_info
        grant_type = auth_info.grant_type
        login_url = auth_info.device_code_endpoint
        resource_urls = self._prepare_resource_urls_for_request(auth_info.resource_url)
        client_id = auth_info.client_id

        trace_info = dict(
            oauth='device-code',
            init_url=login_url,
            client_id=auth_info.client_id,
            grant_type=self.__grant_type,
            resource_urls=resource_urls,
            scope=auth_info.scope,
        )
        logger.debug(f'exchange_token: Authenticating with {trace_info}')

        if grant_type != self.__grant_type:
            raise AuthException(f'Invalid Grant Type (expected: {self.__grant_type})', resource_urls)

        if not login_url:
            raise AuthException("There is no device code URL specified.", resource_urls)

        device_code_params = {
            "grant_type": self.__grant_type,
            "client_id": client_id,
            "resource": self._prepare_resource_urls_for_request(resource_urls),
        }

        if auth_info.scope:
            device_code_params['scope'] = auth_info.scope

        with trace_context.new_span(metadata=trace_info) as sub_span:
            sub_logger = sub_span.create_span_logger(self._logger)
            span_headers = sub_span.create_http_headers()
            init_res = session.post(login_url,
                                           params=device_code_params,
                                           allow_redirects=False,
                                           headers=span_headers)

            sub_logger.debug(f'exchange_tokens: DC#1: {login_url}: HTTP {init_res.status_code}:\n{init_res.text}')

        device_code_json = init_res.json()

        if init_res.ok:
            logger.debug('exchange_tokens: Received the initial OK response')

            device_code = device_code_json["device_code"]
            device_verify_uri = device_code_json["verification_uri_complete"]
            poll_interval = int(device_code_json["interval"])
            expiry = time() + int(env('DEVICE_CODE_TTL', required=False) or device_code_json["expires_in"])

            logger.debug(f'exchange_tokens: Verification URI = {device_verify_uri}')
            logger.debug(f'exchange_tokens: Device Code = {device_code}')
            logger.debug(f'exchange_tokens: Device Code Expiration Time = {expiry}')
            logger.debug(f'exchange_tokens: Suggested Poll Interval = {poll_interval}')

            # user_code = device_code_json['user_code']
            self.__console.print(f"Please go to {device_verify_uri} to continue.\n", to_stderr=True)
            self._events.dispatch('blocking-response-required', dict(kind='user_verification', url=device_verify_uri))
        else:
            logger.debug('exchange_tokens: Received the ERROR response')

            if "error" in init_res.json():
                error_message = f'The device code request failed with message "{device_code_json["error"]}"'
            else:
                error_message = "The device code request failed"

            logger.error(f'exchange_tokens: Failed to initiate the device code flow ({device_code_params})')
            raise AuthException(url=login_url, msg=error_message)

        token_url = auth_info.token_endpoint

        trace_info['verify_url'] = token_url

        while time() < expiry:
            with trace_context.new_span(metadata=trace_info) as sub_span:
                sub_logger = sub_span.create_span_logger(self._logger)
                auth_token_res = session.post(
                    token_url,
                    data={
                        "grant_type": self.__grant_type,
                        "device_code": device_code,
                        "client_id": client_id,
                    },
                    headers=sub_span.create_http_headers()
                )

                sub_logger.debug(f'exchange_tokens: DC#2: {token_url}: HTTP {auth_token_res.status_code}:'
                                 f'\n{auth_token_res.text}')

                auth_token_json = auth_token_res.json()

                if auth_token_res.ok:
                    sub_logger.debug('exchange_tokens: The client is now authorized.')
                    session.close()
                    return auth_token_json
                elif "error" in auth_token_json:
                    if auth_token_json.get("error") == "authorization_pending":
                        sub_logger.debug('exchange_tokens: Pending on user authorization...')
                        sleep(poll_interval)
                        continue

                    error_msg = "Failed to retrieve a token"
                    if "error_description" in auth_token_json:
                        error_msg += f": {auth_token_json['error_description']}"

                    sub_logger.error('Exceeded the waiting time limit for the device code')
                    raise AuthException(url=token_url, msg=error_msg)
                else:
                    sub_logger.warning('Encountered an unknown state during the verification')
                    sleep(poll_interval)

        raise AuthException(url=token_url, msg="the authorize step timed out.")