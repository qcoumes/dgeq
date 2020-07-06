import operator
from collections import abc
from functools import reduce
from typing import Any, Callable, Dict, Iterable, List, Tuple, Type, Union

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.http import QueryDict
from django.utils.module_loading import import_string

from .exceptions import (FieldDepthError, MAX_FOREIGN_FIELD_DEPTH, NotARelatedFieldError,
                         UnknownFieldError)


# Separators use in subquery for some commands (like `c:annotate` or `c:join`)
# `SUBQUERY_SEP_FIELDS` is used to separate field/value(s) pairs
# `SUBQUERY_SEP_VALUES` is used to separate values in a same field
SUBQUERY_SEP_FIELDS = getattr(settings, 'DGEQ_SUBQUERY_SEP_FIELDS', '|')
SUBQUERY_SEP_VALUES = getattr(settings, 'DGEQ_SUBQUERY_SEP_VALUES', "'")

# Type corresponding to the Union of each field used for relations
ForeignField = Union[
    models.OneToOneField, models.OneToOneRel,
    models.ForeignKey, models.ManyToOneRel,
    models.ManyToManyField, models.ManyToManyRel
]

# Type corresponding to a Callable or a dotted path to a Callable with its
# optional arguments
ImportableCallable = Union[
    Callable,  # Function or instance of a class declaring __call__
    str,  # Dotted path to a function, or class with no argument
    Tuple[str],  # Dotted path to a class with no argument in a tuple
    Tuple[str, Iterable[Any]],  # Dotted path to a class with args
    Tuple[str, Dict[str, Any]],  # Dotted path to a class with kwargs
    Tuple[str, Iterable[Any], Dict[str, Any]],  # Dotted path to a class with args and kwargs
]



def _check_field(fields: List[str], current_model: Type[models.Model],
                 arbitrary_fields: Iterable[str] = (),
                 hidden_fields: Dict[Type[models.Model], Iterable[str]] = ()
                 ) -> Tuple[models.Model, str]:
    """Recursively check fields.
    
    Wrapped by `check_field()`, see `check_field()` docstring for more
    information."""
    token, subfields = fields[0], fields[1:]
    
    if current_model in hidden_fields and token in hidden_fields[current_model]:
        raise UnknownFieldError(current_model, token)
    
    try:
        # Will raise FieldDoesNotExists if `token` does not correspond to a
        # field in `current_model` or an arbitrary field
        for a in arbitrary_fields:
            if token == a:
                # Value is not really important as long as it does not contain
                # a `remote_field` member.
                field = None
                break
        else:
            field = current_model._meta.get_field(token)  # noqa
        
        # If there's at least one subfield, change `current_model`
        # to the next one, checking if the field correspond to a remote field
        if subfields:
            if getattr(field, "remote_field", None) is None:
                raise NotARelatedFieldError(current_model, token)
            current_model = field.remote_field.model
    except FieldDoesNotExist:
        raise UnknownFieldError(current_model, token)
    
    # Recursively check subfields, if any
    if subfields:
        return _check_field(subfields, current_model, hidden_fields=hidden_fields)
    
    return current_model, token



def check_field(field: str, model: Type[models.Model], arbitrary_fields: Iterable[str] = (),
                hidden_fields: Dict[Type[models.Model], Iterable[str]] = (), sep="."
                ) -> Tuple[models.Model, str]:
    """Recursively check that a field exists foreign field.
    
    `arbitrary_fields` can be a list of string indicating arbitrary field added
    by some `QuerySet` method (like `annotate()` or `prefetch_related()`.
    
    Foreign field are separated by `sep`. For instance, if a model `Book`
    has a foreign key 'library' to a model `Library` which in turn has a foreign
    key `owner` to a model `Person`, one could do `library.owner.name` using
    dot `.` as `sep`.
    
    Additionally return a tuple (model : `models.Model`, field : `str`)
    corresponding to the last model and last field. For instance, using the
    same models as above, calling `check_field(Book, "library.owner.name")`
    would return `(Person, "name")`.
    
    Raise
        * `UnknownFieldError` if any of the field or foreign fields does not
           exists.
        * `FieldDepthError` if the depth of foreign field exceed
           `MAX_FOREIGN_FIELD_DEPTH`.
        * `NotAForeignFieldError` if a field used as a relation isn't a foreign
           field.
    """
    field_list = field.split(sep)
    max_depth = getattr(
        settings, "MAX_FOREIGN_FIELD_DEPTH", MAX_FOREIGN_FIELD_DEPTH
    )
    if len(field_list) >= max_depth:
        raise FieldDepthError(field)
    
    return _check_field(field_list, model, arbitrary_fields, hidden_fields)



def get_field(field: str, model: Type[models.Model], sep=".") -> Union[models.Field, ForeignField]:
    """Return the instance of `models.Field` corresponding to `field` inside
    `model`.
    
    Field can traverse relation using `sep`. For instance, if a model `Book`
    has a foreign key 'library' to a model `Library` which in turn has a foreign
    key `owner` to a model `Person`, one could do `library.owner.name` using
    dot `.` as `sep`.
    
    May raise the same exceptions as `check_field()`.
    """
    second_last_model, last_field_name = check_field(field, model, sep=sep)
    return second_last_model._meta.get_field(last_field_name)



def import_callable(o: ImportableCallable) -> Callable:
    """Take a dotted path to a `Callable`, and return the corresponding
    object.
    
    If `o` is already a function or an instance of a class declaring
    `__class__`, it is return as is.
    
    If `o` is a `str`, it must be a dotted path to a funtion or a class
    declaring `__call__()` and a constructor with no argument. The function or
    an instance of the class will be returned.
    
    If `o` is an `Iterable`, its first element must be a dotted path to a
    class declaring `__call__()`:
    
    * If its length is 2, its second element must be either an `Iterable` or a
    `Mapping` containing respectively the arguments or the keyworded arguments
    that will be given to the class's constructors.
    
    * If its length is greater than 2, the second element must be an `Iterable`
    and the third element a `Mapping` containing respectively the arguments and
    the keyworded arguments that will be given to the class's constructors.
    
    >>> import_callable(len)
    <built-in function len>
    >>> import_callable("functools.reduce")
    <built-in function reduce>
    >>> class Dummy:
    ...     def __init__(self, *args, **kwargs):
    ...             self.args, self.kwargs = args, kwargs
    ...     def __call__(self):
    ...             print(self.args, self.kwargs)
    >>> import_callable("__main__.Dummy")()
    () {}
    >>> import_callable(("__main__.Dummy",))()
    () {}
    >>> import_callable(("__main__.Dummy", ("foo", "bar")))()
    ('foo', 'bar') {}
    >>> import_callable(("__main__.Dummy", {"foo": "bar"}))()
    () {'foo': 'bar'}
    >>> import_callable(("__main__.Dummy", ("foo", "bar"), {"foo": "bar"}))()
    ('foo', 'bar') {'foo': 'bar'}
    """
    if callable(o):
        if isinstance(o, type):
            raise ValueError("Given callable cannot be a class")
        return o
    
    if isinstance(o, str):
        imported = import_string(o)
        if not callable(imported):
            raise ValueError("Given path does not point to a callable")
        
        if not isinstance(imported, type):  # Is not a class
            return imported
        
        args = tuple()
        kwargs = dict()
    
    elif isinstance(o, abc.Iterable):
        o = list(o)
        args = tuple()
        kwargs = dict()
        imported = import_string(o[0])
        if not isinstance(imported, type):
            raise ValueError("First element of given iterable does not point to a class")
        
        if len(o) == 2:
            if isinstance(o[1], abc.Mapping):
                args = tuple()
                kwargs = o[1]
            elif isinstance(o[1], abc.Iterable):
                args = o[1]
                kwargs = dict()
            else:
                raise ValueError(
                    "Second element of given iterable must be either an iterable or a mapping if "
                    "its length is 2"
                )
        
        elif len(o) == 3:
            if not isinstance(o[1], abc.Iterable):
                raise ValueError(
                    "Second element of given iterable must be an iterable if its length is greater "
                    "than 2"
                )
            if not isinstance(o[2], abc.Mapping):
                raise ValueError(
                    "Second element of given iterable must be a mapping if its length is greater "
                    "than 2"
                )
            args = o[1]
            kwargs = o[2]
    
    else:
        raise ValueError("Given element is neither a Callable, a str nor an iterable")
    
    imported = imported(*args, **kwargs)
    if not callable(imported):
        raise ValueError("Given class does not declare __call__")
    
    return imported



def subquery_to_querydict(qs: str, fields_sep: str = SUBQUERY_SEP_FIELDS,
                          values_sep: str = SUBQUERY_SEP_VALUES) -> QueryDict:
    """Create a `QueryDict` out of a subquery string.
    
    Subquery strings are value of commands using different key/value pairs,
    such as `c:annotate` or `c:join`.
    
    `fields_sep` is used to separate field/value pairs.
    `values_sep` is used to separate values in a field.
    
    Raise `ValueError` if no `=` is found in a key/value pair:
    
    >>> subquery_to_querydict("field1=value^field_value_without_equal", "^")
    Traceback (most recent call last):
        ...
    ValueError: A key/value pair must contains an equal '=', received
    'field_value_without_equal'
    """
    query_dict = QueryDict(mutable=True)
    
    for kwarg in qs.split(fields_sep):
        kwarg = kwarg.split("=", 1)
        if len(kwarg) < 2:
            raise ValueError(f"A key/value pair must contains an equal '=', received '{kwarg[0]}'")
        
        k, values = kwarg
        for v in values.split(values_sep):
            query_dict.appendlist(k, v)
    
    return query_dict



def split_list_strings(lst: Iterable[str], sep: str) -> List[str]:
    """Return a list of the words in each string of `lst`, using `sep` as
    delimiter.
    
    >>> split_list_strings(["one,two", "three", "four,five,six"], ",")
    ['one', 'two', 'three', 'four', 'five', 'six']
    """
    return reduce(operator.add, (i.split(sep) for i in lst)) if lst else []
