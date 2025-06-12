#!/usr/bin/env python3
import importlib
import inspect
import logging
import os
import re
from datetime import datetime
from typing import Optional, Any, List

import sys
from imagination.debug import get_logger
from pydantic import BaseModel

logger = get_logger(os.path.basename(__file__), logging.INFO)
source_root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
doc_dir = os.path.join(source_root_dir, 'docs')
api_reference_dir = os.path.join(doc_dir, 'api')
grouped_targets = {
    'dnastack.client.collections.client': [
        'CollectionServiceClient',
    ],
    'dnastack.client.collections.model': [
        'Collection',
    ],
    'dnastack.client.explorer.client': [
        'ExplorerClient',
    ],
    'dnastack.client.explorer.models': [
        'FederatedQuestion',
        'QuestionParam',
        'QuestionCollection',
    ],
    'dnastack.client.data_connect': [
        'DataConnectClient',
        'TableInfo',
        'Table',
    ],
    'dnastack.client.drs': [
        'DrsClient'
    ],
    'dnastack.client.service_registry.client': [
        'ServiceListingError',
        'ServiceRegistry',
    ],
    'dnastack.client.service_registry.factory': [
        'UnsupportedClientClassError',
        'UnregisteredServiceEndpointError',
        'ClientFactory',
    ],
    'dnastack.client.service_registry.models': [
        'ServiceType',
        'Organization',
        'Service',
    ],
    'dnastack.configuration.exceptions': [
        'ConfigurationError',
        'MissingEndpointError',
        'UnknownClientShortTypeError',
    ],
    'dnastack.configuration.manager': [
        'ConfigurationManager',
    ],
    # 'dnastack.configuration.models': [
    #     'OAuth2Authentication',
    #     'ServiceEndpoint',
    #     'Configuration',
    # ],
    'dnastack.configuration.wrapper': [
        'UnsupportedModelVersionError',
        'ConfigurationWrapper',
    ],
    'dnastack.http.session': [
        'AuthenticationError',
        'HttpError',
        'HttpSession',
    ],
    'dnastack.http.session_info': [
        'SessionInfoHandler',
        'SessionInfo',
        'UnknownSessionError',
        'BaseSessionStorage',
        'InMemorySessionStorage',
        'FileSessionStorage',
        'SessionManager',
    ],
    'dnastack.cli.helpers.client_factory': [
        'ServiceEndpointNotFound',
        'UnknownAdapterTypeError',
        'UnknownClientShortTypeError',
        'ConfigurationBasedClientFactory',
    ]
}

# Flatten targets
targets = []
for module_path in grouped_targets:
    for ref_name in grouped_targets[module_path]:
        targets.append((module_path, ref_name))
targets = sorted(targets)

# Doc header
headers = f"""
---
title: "API Reference (v3)"
weight: 1
draft: false
lastmod: {datetime.utcnow().strftime('%Y-%m-%d')}
type: docs
layout: single-col
---

This API reference is only for dnastack-client-library 3.x.

""".strip()

print(headers)

sys.path.insert(0, source_root_dir)


class ParameterDoc(BaseModel):
    name: str
    required: bool
    default: Optional[Any] = None
    annotation: Optional[str] = None
    kind: str

    def __str__(self):
        if self.kind == 'VAR_KEYWORD':
            return f'**{self.name}'
        elif self.kind == 'VAR_POSITIONAL':
            return f'*{self.name}'
        else:
            output = self.name
            if self.annotation:
                output += ': ' + self.annotation
            if self.default:
                output += '= ' + (f'"{self.default}"' if isinstance(self.default, str) else str(self.default))
            return output


class ObjectDoc(BaseModel):
    module_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    arguments: List[ParameterDoc] = list()
    callable: bool = False
    return_annotation: Optional[str] = None
    ref_type: Optional[str] = 'self'  # Reference Type: self, class, static

    def generate_markdown(self, include_module_name=True, as_class_member=False, is_class_static_member=False) -> str:
        if self.callable:
            signature = (
                    ("@staticmethod" if is_class_static_member else "")
                    + " def " + generate_signature_string(self, include_module_name, as_class_member)
            ).strip()
        else:
            signature = (
                    self.name
                    + (f': {self.return_annotation}' if self.return_annotation else '')
            )
        lines = [
            ('######' if as_class_member else '####') + f' `{signature}`',
            convert_rst_to_markdown(self.description)
        ]
        return '\n'.join(lines)

    @classmethod
    def from_callable(cls, callable_obj):
        try:
            signature = inspect.signature(callable_obj)
            return_annotation = signature.return_annotation
        except ValueError:
            return_annotation = None

        return cls(
            name=callable_obj.__name__,
            description=inspect.getdoc(callable_obj),
            callable=True,
            return_annotation=extract_fq_name_from_annotation(return_annotation) if return_annotation else None,
        )


class ClassDoc(BaseModel):
    module_name: str
    name: str
    constructor: ObjectDoc
    properties: List[ObjectDoc] = list()
    methods: List[ObjectDoc] = list()

    def generate_markdown(self) -> str:
        # language=markdown
        lines = [f'#### Class `{generate_signature_string(self.constructor)}`']
        if self.constructor.description:
            lines.append(self.constructor.description)
        if self.properties:
            lines.append('##### Properties')
            for property_doc in self.properties:
                lines.append(property_doc.generate_markdown(as_class_member=True))
        if self.methods:
            lines.append('##### Methods')
            for method_doc in self.methods:
                if not method_doc.description:
                    logger.warning(
                        f'{extract_fq_name_from(self)}: method {method_doc.name}: skipped as there is no documentation')
                    continue
                if method_doc.description and '.. deprecated:' in method_doc.description:
                    logger.warning(
                        f'{extract_fq_name_from(self)}: method {method_doc.name}: skipped as it is marked as deprecated')
                    continue
                is_object_method = method_doc.arguments and method_doc.arguments[0].name == 'self'
                method_markdown = method_doc.generate_markdown(as_class_member=True,
                                                               is_class_static_member=not is_object_method)
                lines.append(method_markdown)

        return '\n'.join(lines)


def convert_rst_to_markdown(rst: str):
    re_param = re.compile('^:param ([^:]+):\s*(.*)')
    re_return = re.compile('^:return:\s*(.*)')
    rst = rst.strip() if rst else None

    if not rst:
        return ''

    rst_lines = rst.split('\n')
    md_lines = []

    param_lines = []
    return_line = None

    for rst_line in rst_lines:
        param_match = re_param.search(rst_line)
        if param_match:
            param_name, description = param_match.groups()
            param_lines.append(f'| `{param_name}` | {description or "N/A"} |')
            continue

        return_match = re_return.search(rst_line)
        if return_match:
            return_description = return_match.group(1)
            return_line = return_description
            continue

        md_lines.append(rst_line)

    if param_lines:
        md_lines.append('\n| Parameter | Description |')
        md_lines.append('| --- | --- |')
        md_lines.extend(param_lines)

    if return_line:
        md_lines.append(f'\n| Return |\n| --- |\n| {return_line} |')

    return '\n'.join(md_lines)


def generate_object_doc(callable_obj):
    object_doc = ObjectDoc.from_callable(callable_obj)

    try:
        signature = inspect.signature(callable_obj)
        parameters = signature.parameters

        for parameter_name in parameters:
            parameter = parameters[parameter_name]
            no_default = parameter.default == parameter.empty
            parameter_doc = ParameterDoc(name=parameter.name,
                                         required=not no_default,
                                         default=None if no_default else parameter.default,
                                         annotation=extract_fq_name_from_annotation(parameter.annotation),
                                         kind=parameter.kind)
            object_doc.arguments.append(parameter_doc)
    except ValueError as e:
        logger.warning(f'Failed to inspect {callable_obj} ({e})')

    return object_doc


def generate_signature_string(obj_doc, include_module_name=True, as_class_member=False):
    callable_name = extract_fq_name_from(obj_doc, include_module_name)
    params = []
    for argument in obj_doc.arguments:
        if as_class_member and argument.name == 'self':
            continue
        params.append(str(argument))
    params_string = ', '.join(params)
    signature = f'{callable_name}({params_string})'
    if obj_doc.return_annotation and obj_doc.return_annotation != 'None':
        signature += ' -> ' + obj_doc.return_annotation
    return signature


def extract_fq_name_from(doc_obj, include_module_name=True):
    fqn = []

    if include_module_name and doc_obj.module_name:
        fqn.append(doc_obj.module_name)
    if doc_obj.name:
        fqn.append(doc_obj.name)

    return '.'.join(fqn)


def extract_fq_name_from_annotation(annotation):
    fqn = []

    # noinspection PyProtectedMember
    if annotation == inspect._empty:
        return None

    basic_representation = str(annotation)

    if basic_representation.startswith('typing.'):
        return re.sub(r'typing\.', '', basic_representation)
    else:
        if hasattr(annotation, '__module__'):
            fqn.append(annotation.__module__)
        if hasattr(annotation, '__name__'):
            fqn.append(annotation.__name__)

    return re.sub(r'^builtins\.', '', '.'.join(fqn) if fqn else basic_representation)


def extract_doc_from(ref):
    if inspect.isclass(ref):
        cls_doc = ClassDoc(module_name=getattr(ref, '__module__') if hasattr(ref, '__module__') else None,
                           name=ref.__name__,
                           constructor=generate_object_doc(ref))
        cls_doc.constructor.module_name = cls_doc.module_name

        if issubclass(ref, BaseModel):
            for p_name, p_annotation in ref.__annotations__.items():
                annotation = p_annotation.__name__ if inspect.isclass(p_annotation) else str(p_annotation)
                annotation = re.sub(r'typing\.', '', annotation)
                cls_doc.properties.append(ObjectDoc(name=f'{p_name}: {annotation}'))

        for member_name, member in inspect.getmembers(ref):
            if member_name[0] == '_':
                continue

            if callable(member):
                # noinspection PyTypeChecker
                cls_doc.methods.append(generate_object_doc(member))
            else:
                cls_doc.properties.append(ObjectDoc(name=member_name, description=inspect.getdoc(member)))

        return cls_doc
    elif inspect.ismethod(ref):
        pass


def main():
    os.makedirs(api_reference_dir, exist_ok=True)

    generated_file_paths = []
    final_doc = [headers]

    for module_path, ref_name in targets:
        ref = getattr(importlib.import_module(module_path), ref_name)
        doc = extract_doc_from(ref)

        md_string = doc.generate_markdown()
        final_doc.append(md_string)

        generated_file_path = os.path.join(api_reference_dir, f'{module_path}.{ref_name}.md')

        with open(generated_file_path, 'w') as f:
            f.write(md_string)

        logger.info(f'Generated {generated_file_path}')
        generated_file_paths.append(generated_file_path)

    with open(os.path.join(doc_dir, 'full-api-reference.md'), 'w') as f:
        f.write('\n'.join(final_doc))


if __name__ == '__main__':
    main()
