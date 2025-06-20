import logging

from dnastack.common.environments import env
from dnastack.common.logger import default_logging_level, get_log_level

__DEBUG_LOG_ACTIVATION_NOTIFIED = False


def get_authenticator_log_level():
    global __DEBUG_LOG_ACTIVATION_NOTIFIED

    authenticator_log_level_name = env(
        "DNASTACK_AUTH_LOG_LEVEL",
        description="The log level for the authenticator. This overrides DNASTACK_LOG_LEVEL or the default log level.",
        required=False,
        default=None,
    )

    authenticator_log_level = (
        get_log_level(authenticator_log_level_name) if authenticator_log_level_name else default_logging_level
    )

    if authenticator_log_level == logging.DEBUG and not __DEBUG_LOG_ACTIVATION_NOTIFIED:
        logging.warning(
            "🚨 WARNING: The log level of the authenticator is set to DEBUG. At this level, it may display "
            "highly sensitive information, such as an access token, a refresh token, a JWT. You can set "
            'the environment variable "DNASTACK_AUTH_LOG_LEVEL" to "INFO", "WARNING", or "ERROR".'
        )

        __DEBUG_LOG_ACTIVATION_NOTIFIED = True
