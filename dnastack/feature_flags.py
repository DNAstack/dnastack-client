import sys
from typing import Callable, List, Dict

from dnastack.common.environments import flag

__FLAG_CACHE_MAP: Dict[str, bool] = {}
__DEBUG_MODE_HOOKS: List[Callable[[bool], None]] = []


def currently_in_debug_mode():
    previously_enabled = __FLAG_CACHE_MAP.get('debug_mode')
    currently_enabled = flag('DNASTACK_DEBUG', description='Enable the debug mode')

    if previously_enabled != currently_enabled:
        __FLAG_CACHE_MAP['debug_mode'] = currently_enabled
        for hook in __DEBUG_MODE_HOOKS:
            hook(currently_enabled)

    return currently_enabled


def on_debug_mode_change(hook: Callable[[bool], None]):
    __DEBUG_MODE_HOOKS.append(hook)


# For more details about environment variables, please check out dev-configuration.md.

dev_mode = flag('DNASTACK_DEV',
                description='Make all experimental/work-in-progress functionalities visible')

in_interactive_shell = sys.__stdout__ and sys.__stdout__.isatty()
cli_show_list_item_index = flag('DNASTACK_SHOW_LIST_ITEM_INDEX',
                                description='The CLI output will show the index number of items in any list output')
detailed_error = flag('DNASTACK_DETAILED_ERROR', description='Provide more details on error')
show_distributed_trace_stack_on_error = flag('DNASTACK_DISPLAY_TRACE_ON_ERROR',
                                             description='Display distributed trace on error')
