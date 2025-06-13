from typing import List, Optional, Any, Dict, Iterator, Tuple

import click
from click import Group
from imagination import container

from dnastack.cli.commands.auth.event_handlers import handle_revoke_begin, handle_revoke_end, handle_auth_begin, \
    handle_auth_end, \
    handle_no_refresh_token, handle_refresh_skipped
from dnastack.cli.core.command import formatted_command
from dnastack.cli.core.command_spec import ArgumentSpec, RESOURCE_OUTPUT_ARG, CONTEXT_ARG, SINGLE_ENDPOINT_ID_ARG
from dnastack.cli.helpers.iterator_printer import show_iterator
from dnastack.cli.helpers.printer import echo_header, echo_list
from dnastack.common.auth_manager import AuthManager, ExtendedAuthState
from dnastack.common.logger import get_logger
from dnastack.configuration.manager import ConfigurationManager
from dnastack.configuration.wrapper import ConfigurationWrapper
from dnastack.http.authenticators.oauth2_adapter.token_exchange import TokenExchangeAdapter
from dnastack.http.authenticators.oauth2_adapter.models import OAuth2Authentication
from dnastack.common.tracing import Span
from dnastack.http.session_info import SessionManager, SessionInfo, SessionInfoHandler
from time import time


def get_client_credentials_from_service_registry(context_name: Optional[str] = None) -> Tuple[str, str]:
    """
    Retrieve OAuth2 client credentials from service registry configuration.
    Falls back to default explorer credentials if not available.
    """
    config_manager: ConfigurationManager = container.get(ConfigurationManager)
    wrapper = ConfigurationWrapper(config_manager.load(), context_name)
    context = wrapper.current_context

    if context and context.endpoints:
        # Look for OAuth2 endpoints with client credentials
        for endpoint in context.endpoints:
            for auth in endpoint.get_authentications():
                if auth.get('type') == 'oauth2' and auth.get('client_id'):
                    return auth['client_id'], auth.get('client_secret', '')

    # Fallback to explorer credentials
    return 'dnastack-client', 'dev-secret-never-use-in-prod'


def create_token_exchange_session(auth_info: OAuth2Authentication, 
                                token_response: Dict[str, Any]) -> SessionInfo:
    """
    Create a session info for token exchange with complete re-authentication support.
    """
    created_time = int(time())
    expiry_time = created_time + token_response['expires_in']
    handler_auth_info = auth_info.dict()

    return SessionInfo(
        model_version=4,
        config_hash=auth_info.get_content_hash(),
        access_token=token_response['access_token'],
        refresh_token=token_response.get('refresh_token'),  # Usually None for token exchange
        scope=token_response.get('scope'),
        token_type=token_response['token_type'],
        issued_at=created_time,
        valid_until=expiry_time,
        handler=SessionInfoHandler(auth_info=handler_auth_info)
    )


def init_auth_commands(group: Group):
    @formatted_command(
        group=group,
        name='login',
        specs=[
            ArgumentSpec(
                name='force_refresh',
                arg_names=['-force-refresh'],
                help='If set, this command will only refresh any existing session(s).',
            ),
            ArgumentSpec(
                name='revoke_existing',
                arg_names=['-revoke-existing'],
                help='If set, the existing session(s) will be force-revoked before the authentication.',
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ],
    )
    def login(context: Optional[str],
              endpoint_id: Optional[str] = None,
              force_refresh: bool = False,
              revoke_existing: bool = False):
        """
        Log in to ALL service endpoints or ONE specific service endpoint.
    
        If the endpoint ID is not specified, it will initiate the auth process for all endpoints.
        """
        handler = AuthCommandHandler(context_name=context)
        handler.initiate_authentications(endpoint_ids=[endpoint_id] if endpoint_id else [],
                                         force_refresh=force_refresh,
                                         revoke_existing=revoke_existing)
    
    
    @formatted_command(
        group=group,
        name='status',
        specs=[
            RESOURCE_OUTPUT_ARG,
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def status(context: Optional[str],
               endpoint_id: Optional[str] = None,
               output: Optional[str] = None):
        """ Check the status of all authenticators. """
        handler = AuthCommandHandler(context_name=context)
        show_iterator(output or RESOURCE_OUTPUT_ARG.default, handler.get_states([endpoint_id] if endpoint_id else None))
    
    
    @formatted_command(
        group=group,
        name='revoke',
        specs=[
            ArgumentSpec(
                name='force',
                arg_names=['-force', '-f'],
                help='Force the auth revocation without prompting the user for confirmation',
            ),
            CONTEXT_ARG,
            SINGLE_ENDPOINT_ID_ARG,
        ]
    )
    def revoke(context: Optional[str],
               endpoint_id: Optional[str] = None,
               force: bool = False):
        """
        Revoke the authorization to one to many endpoints.
    
        If the endpoint ID is not specified, it will revoke all authorizations.
        """
        handler = AuthCommandHandler(context_name=context)
        handler.revoke([endpoint_id] if endpoint_id else [], force)
    
    
    @formatted_command(
        group=group,
        name='token-exchange',
        hidden=True,
        specs=[
            ArgumentSpec(
                name='subject_token',
                arg_names=['--subject-token'],
                help='ID token to exchange (if not provided, will fetch from cloud environment)',
            ),
            ArgumentSpec(
                name='resource',
                arg_names=['--resource'],
                help='Resource URL for the token exchange',
                required=True,
            ),
            ArgumentSpec(
                name='token_endpoint',
                arg_names=['--token-endpoint'],
                help='Token endpoint URL',
                required=True,
            ),
            ArgumentSpec(
                name='audience',
                arg_names=['--audience'],
                help='Audience for GCP ID token (defaults to resource URL)',
            ),
            ArgumentSpec(
                name='scope',
                arg_names=['--scope'],
                help='OAuth2 scope for the token exchange',
            ),
            CONTEXT_ARG,
        ]
    )
    def token_exchange(resource: str,
                       token_endpoint: str,
                       subject_token: Optional[str] = None,
                       audience: Optional[str] = None,
                       scope: Optional[str] = None,
                       context: Optional[str] = None):
        """
        Perform token exchange flow using ID token.
        Sessions created by this command support automatic re-authentication
        when access tokens expire in cloud environments.
        """
        client_id, client_secret = get_client_credentials_from_service_registry(context)
        
        auth_info = OAuth2Authentication(
            grant_type='urn:ietf:params:oauth:grant-type:token-exchange',
            token_endpoint=token_endpoint,
            resource_url=resource,
            subject_token=subject_token,
            audience=audience or resource,
            client_id=client_id,
            client_secret=client_secret,
            scope=scope,
            type='oauth2'
        )
        adapter = TokenExchangeAdapter(auth_info)
        trace_context = Span(origin='token-exchange-cli')
        click.echo(f"Performing token exchange...")
        click.echo(f"Token endpoint: {token_endpoint}")
        click.echo(f"Resource: {resource}")
        click.echo(f"Client ID: {client_id}")
        
        if subject_token:
            click.echo("Using provided subject token")
        else:
            click.echo("Fetching ID token from cloud environment...")

        try:
            result = adapter.exchange_tokens(trace_context)
            session_info = create_token_exchange_session(auth_info, result)
            session_manager: SessionManager = container.get(SessionManager)
            session_id = auth_info.get_content_hash()
            session_manager.save(session_id, session_info)

            click.echo("\nToken exchange successful!")
            click.echo(f"Access token: {result.get('access_token', 'N/A')[:50]}...")
            click.echo(f"Token type: {result.get('token_type', 'N/A')}")
            click.echo(f"Expires in: {result.get('expires_in', 'N/A')} seconds")
            click.echo(f"Session saved with ID: {session_id[:8]}...")
                
        except Exception as e:
            click.echo(f"❌ Token exchange failed: {e}", err=True)
            raise click.ClickException(str(e))
    
    
class AuthCommandHandler:
    def __init__(self, context_name: Optional[str] = None):
        self._logger = get_logger(type(self).__name__)
        self._session_manager: SessionManager = container.get(SessionManager)
        self._config_manager: ConfigurationManager = container.get(ConfigurationManager)
        self._context_name = context_name
        self._auth_manager = AuthManager(
            context=ConfigurationWrapper(self._config_manager.load(), self._context_name).current_context)

    def revoke(self, endpoint_ids: List[str], no_confirmation: bool):
        # NOTE: This is currently designed exclusively to work with OAuth2 config.
        #       Need to rework (on the output) to support other types of authenticators.

        if not no_confirmation and not endpoint_ids:
            echo_header('WARNING: You are about to revoke the access to all endpoints.', bg='yellow', fg='white')

        auth_manager = self._auth_manager
        auth_manager.events.on('revoke-begin', handle_revoke_begin)
        auth_manager.events.on('revoke-end', handle_revoke_end)

        affected_endpoint_ids: List[str] = auth_manager.revoke(
            endpoint_ids,
            confirmation_operation=(
                None
                if no_confirmation
                else lambda: click.confirm('Do you want to proceed?')
            )
        )

        echo_header('Summary')

        if affected_endpoint_ids:
            echo_list('The client is no longer authenticated to the follow endpoints:',
                      affected_endpoint_ids)
        else:
            click.echo('No changes')

        print()

    def get_states(self, endpoint_ids: List[str] = None) -> Iterator[ExtendedAuthState]:
        return self._auth_manager.get_states(endpoint_ids)

    def _remove_none_entry_from(self, d: Dict[str, Any]) -> Dict[str, Any]:
        return {
            k: v
            for k, v in d.items()
            if v is not None
        }

    def initiate_authentications(self,
                                 endpoint_ids: List[str] = None,
                                 force_refresh: bool = False,
                                 revoke_existing: bool = False,
                                 context_name: Optional[str] = None):
        # NOTE: This is currently designed exclusively to work with OAuth2 config.
        #       Need to rework (on the output) to support other types of authenticators.

        auth_manager = self._auth_manager
        auth_manager.events.on('auth-begin', handle_auth_begin)
        auth_manager.events.on('auth-end', handle_auth_end)
        auth_manager.events.on('no-refresh-token', handle_no_refresh_token)
        auth_manager.events.on('refresh-skipped', handle_refresh_skipped)

        auth_manager.initiate_authentications(endpoint_ids, force_refresh, revoke_existing)
