from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Dict, get_origin, get_args, Union, Type


@dataclass(repr=True)
class _Property:
    annotation: Any
    kind: Union[type, Callable, None]
    required: bool
    default: Any


class UndefinedInitializedPropertyError(RuntimeError):
    def __init__(self, cls: Type, property_name: str):
        self.__cls = cls
        self.__property_name = property_name

    def __str__(self):
        return f'{self.__cls.__module__}.{self.__cls.__name__}: "{self.__property_name}" not defined'


def simple_constructor():
    """ Provide a simple constructor by turning all annotated properties into non-static instance variables. """

    def wrapper(cls):
        property_map: Dict[str, _Property] = {}

        for p, a in cls.__annotations__.items():
            special_type = get_origin(a)
            type_args = get_args(a)
            optional = special_type is Union and type(None) in type_args
            property_map[p] = _Property(annotation=a, kind=None, required=not optional, default=None)

        for pn in dir(cls):
            if pn[0] == '_':
                continue

            pv = getattr(cls, pn)

            if callable(pv):
                continue

            if pn not in property_map:
                property_map[pn] = _Property(annotation=None, kind=None, required=False, default=pv)
            else:
                property_config = property_map[pn]
                property_config.annotation = type(pv)
                property_config.required = False
                property_config.default = pv

        cls.__processed_properties__ = property_map

        for pn in cls.__processed_properties__.keys():
            if hasattr(cls, pn):
                delattr(cls, pn)

        def cls_init(self, **kwargs):
            for property_name, property_config in cls.__processed_properties__.items():
                if property_name in kwargs:
                    property_value = kwargs[property_name]
                elif not property_config.required:
                    property_value = property_config.default
                else:
                    raise UndefinedInitializedPropertyError(type(self), property_name)

                # TODO Type check

                setattr(self, property_name, property_value)

        cls.__init__ = cls_init

        return cls

    return wrapper
