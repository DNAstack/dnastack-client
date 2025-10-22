import json
import sys
import traceback
from enum import Enum
from io import UnsupportedOperation
from typing import List, Dict, Union, Tuple

# from dnastack.cli.workbench.utils import UnableToDecodeFileError, UnableToDecodeJSONDataError
from dnastack.common.logger import get_logger
from dnastack.feature_flags import currently_in_debug_mode

logger = get_logger('json_argument_parser')

try:
    from httpie.cli.argtypes import KeyValueArgType
    from httpie.cli.constants import (
        SEPARATOR_GROUP_NESTED_JSON_ITEMS,
        SEPARATOR_DATA_EMBED_FILE_CONTENTS,
        SEPARATOR_DATA_EMBED_RAW_JSON_FILE,
        SEPARATOR_DATA_RAW_JSON
    )
    from httpie.cli.nested_json import interpret_nested_json
except UnsupportedOperation:
    # NOTE This is just to bypass the error raised by Colab's Jupyter Notebook.
    # FIXME Fix the issue where ncurses raises io.UnsupportedOperation.
    if currently_in_debug_mode():
        logger.warning("Could start importing httpie modules but failed to finish it.")
        traceback.print_exc()
        logger.warning(
            "This module will be imported but there will be no guarantee that the dependant code will work normally.")

JSONType = Union[str, bool, int, list, dict]
LIST_SEPARATOR = ","


class ArgumentType(str, Enum):
    JSON_LITERAL_PARAM_TYPE = "JSON_LITERAL"
    FILE = "FILE"
    KV_PARAM_TYPE = "KEY_VALUE"
    STDIN_PARAM_TYPE = "STDIN"
    STRING_PARAM_TYPE = "STRING_PARAM"
    UNKNOWN_PARAM_TYPE = "UNKNOWN"


class FileOrValue:

    def __init__(self, raw_value: str):
        self._raw_value = raw_value
        self._argument_type = get_argument_type(raw_value)

    @property
    def raw_value(self):
        return self._raw_value

    @property
    def argument_type(self):
        return self._argument_type

    def value(self) -> str:
        loaded_value = self.raw_value
        if self.argument_type == ArgumentType.STDIN_PARAM_TYPE:
            loaded_value = read_stdin(self.raw_value)
        elif self.argument_type == ArgumentType.FILE:
            loaded_value = read_file_content(self.raw_value)
        return loaded_value


class JsonLike(FileOrValue):
    def parsed_value(self) -> JSONType:
        value = super().value()
        if self.argument_type == ArgumentType.KV_PARAM_TYPE:
            return parse_kv_arguments(split_arguments_list(value))
        else:
            return json.loads(value)

    def extract_arguments_list(self) -> Tuple[List[str], List[str], List[str], List[str]]:
        # ordered as lists of param ids, kv pairs, json literals, files
        params_ids = []
        kv_pairs = []
        json_literals = []
        files = []
        value = self.raw_value
        separated_arguments = split_arguments_list(value)
        for arg in separated_arguments:
            arg_type = get_argument_type(arg)
            if arg_type == ArgumentType.STRING_PARAM_TYPE:
                params_ids.append(arg)
            if arg_type == ArgumentType.KV_PARAM_TYPE:
                kv_pairs.append(arg)
            if arg_type == ArgumentType.JSON_LITERAL_PARAM_TYPE:
                json_literals.append(arg)
            if arg_type == ArgumentType.FILE:
                files.append(arg)
            if arg_type == ArgumentType.UNKNOWN_PARAM_TYPE:
                raise ValueError(f"Cannot recognize parameter: {arg}")
        return params_ids, kv_pairs, json_literals, files


def merge(base, override_dict, path=None):
    """
    merges b into a
    """
    if path is None:
        path = []
    for key in override_dict:
        if key in base:
            if isinstance(base[key], dict) and isinstance(override_dict[key], dict):
                merge(base[key], override_dict[key], path + [str(key)])
            elif base[key] == override_dict[key]:
                pass  # same leaf value
            else:
                # o
                base[key] = override_dict[key]
        else:
            base[key] = override_dict[key]
    return base


def split_arguments_list(args_list: str) -> List[str]:
    args_list = args_list.replace("\\,", "%2C")
    return [arg.replace("\\,", ",").replace("%2C", ",")
            for arg in args_list.split(LIST_SEPARATOR)]


def is_json_object_or_array_string(string: str) -> bool:
    try:
        json_val = json.loads(string)
        return isinstance(json_val, list) or isinstance(json_val, dict)
    except ValueError:
        return False


def read_file_content(argument: str) -> str:
    # Handle file with "@" prefix
    argument = argument.replace("@", "", 1)
    with open(argument) as argument_fp:
        return argument_fp.read()


def read_stdin(argument: str) -> str:
    # Handle stdin with "-"
    if argument == "-":
        if not sys.stdin.isatty():  # Check if there's data in stdin
            return sys.stdin.read()
        raise ValueError("No input provided via stdin")

def get_argument_type(argument: str) -> str:
    if not argument:
        return ArgumentType.UNKNOWN_PARAM_TYPE
    if argument.startswith("-"):
        return ArgumentType.STDIN_PARAM_TYPE
    if argument.startswith("@"):
        return ArgumentType.FILE
    if is_json_object_or_array_string(argument):
        return ArgumentType.JSON_LITERAL_PARAM_TYPE
    if "=" in argument:
        return ArgumentType.KV_PARAM_TYPE
    return ArgumentType.STRING_PARAM_TYPE


def parse_kv_arguments(arguments: List[str]) -> Union[List[JSONType], Dict[str, JSONType]]:
    arg_types = KeyValueArgType(*SEPARATOR_GROUP_NESTED_JSON_ITEMS)
    kv_pairs = []
    for argument in arguments:
        arg_type = arg_types(argument)
        if arg_type.sep == SEPARATOR_DATA_EMBED_FILE_CONTENTS:
            with open(arg_type.value) as arg_fp:
                arg_type.value = arg_fp.read()
        elif arg_type.sep == SEPARATOR_DATA_EMBED_RAW_JSON_FILE:
            with open(arg_type.value) as arg_fp:
                arg_type.value = json.load(arg_fp)
        elif arg_type.sep == SEPARATOR_DATA_RAW_JSON:
            arg_type.value = json.loads(arg_type.value)
        kv_pairs.append((arg_type.key, arg_type.value))
    nested_json = interpret_nested_json(kv_pairs)
    # If the value being specified was a root list, we want to extract the list
    if len(nested_json.keys()) == 1 and '' in nested_json.keys():
        nested_json = nested_json['']
    return nested_json


def parse_and_merge_arguments(arguments: List[JsonLike]) -> Dict[str, JSONType]:
    arguments_results = {}
    kv_arguments = []
    for argument in arguments:
        if argument.argument_type == ArgumentType.KV_PARAM_TYPE:
            kv_arguments.extend(split_arguments_list(argument.value()))
        elif argument.argument_type == ArgumentType.UNKNOWN_PARAM_TYPE:
            raise ValueError(f"Cannot merge non json value from argument: {argument}")
        else:
            parsed = argument.parsed_value()
            merge(arguments_results, parsed)
    kv_arguments_result = parse_kv_arguments(kv_arguments)
    if kv_arguments_result:
        merge(arguments_results, kv_arguments_result)
    return arguments_results


def merge_param_json_data(kv_pairs_list: List[str], json_literals_list: List[str],
                          files_list: List[str]) -> Dict[str, JSONType]:
    param_presets = {}

    # in this ordering the JSON content of the file will be overwritten by any keys with the same values
    if files_list:
        for file_path in files_list:
            try:
                file_data = read_file_content(file_path)
                file_json = json.loads(file_data)
                merge(param_presets, file_json)
            except Exception as e:
                raise ValueError(f"Failed to parse and merge the JSON file {file_path}. {e}")

    if json_literals_list:
        for json_literal in json_literals_list:
            try:
                json_literal_data = json.loads(json_literal)
                merge(param_presets, json_literal_data)
            except Exception as e:
                raise ValueError(f"Failed to parse and merge the JSON literal {json_literal}. {e}")

    if kv_pairs_list:
        try:
            kv_params = parse_kv_arguments(kv_pairs_list)
            merge(param_presets, kv_params)
        except Exception as e:
            raise ValueError(f"Failed to parse and merge the key value pairs {kv_pairs_list}. "
                             f"Ensure they are each separated with a comma. {e}")

    return param_presets
