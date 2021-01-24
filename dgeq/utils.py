import operator
from collections import abc
from functools import reduce
from typing import Any, Callable, Dict, Iterable, List, Set, Tuple, Type, Union

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Field
from django.http import QueryDict
from django.utils.module_loading import import_string

from . import constants
from .censor import Censor
from .exceptions import FieldDepthError, NotARelatedFieldError, UnknownFieldError


# Type corresponding to the Union of each field used for relations
ForeignField = Union[
    models.OneToOneField, models.OneToOneRel,
    models.ForeignKey, models.ManyToOneRel,
    models.ManyToManyField, models.ManyToManyRel
]

# Type mapping a Model to a subset of its field
FieldMapping = Dict[Type[models.Model], Iterable[str]]

# Fields containing a list of Foreign Keys.
MANY_FOREIGN_FIELD = (models.ManyToOneRel, models.ManyToManyField, models.ManyToManyRel)
# Fields containing only one Foreign Key
UNIQUE_FOREIGN_FIELD = (models.OneToOneRel, models.OneToOneField, models.ForeignKey)

Nothing = type(Ellipsis)

# Typing of a command
CommandType = Callable[['GenericQuery', str, List[str]], None]

# Typing of a type parser
TypeParser = Callable[[str], Union[Nothing, float]]

# Type corresponding to a Callable or a dotted path to a Callable with its
# optional arguments
ImportableCallable = Union[
    CommandType,
    TypeParser,
    Callable,
    str,  # Dotted path to a function, or class with no argument
    Tuple[str],  # Dotted path to a class with no argument in a tuple
    Tuple[str, Iterable[Any]],  # Dotted path to a class with args
    Tuple[str, Dict[str, Any]],  # Dotted path to a class with kwargs
    Tuple[str, Iterable[Any], Dict[str, Any]],  # Dotted path to a class with args and kwargs
]




def import_class(o: Union[type, str]) -> type:
    """Take a dotted path to a class, and return the corresponding class.
    
    If `o` is already a class, it is returned as is."""
    if callable(o):
        if not isinstance(o, type):
            raise ValueError(f"Given object is not a class ('{o}')")
        return o
    
    imported = import_string(o)
    if not callable(imported) or not isinstance(imported, type):
        raise ValueError(f"Given path does not point to a class ('{o}')")
    
    return imported



def import_callable(o: ImportableCallable) -> Callable:
    """Take a dotted path to a `Callable`, and return the corresponding
    object.
    
    If `o` is already a function or an instance of a class declaring
    `__class__`, it is returned as is.
    
    If `o` is a `str`, it must be a dotted path to a function or a class
    declaring `__call__()` and a constructor with no argument. The function or
    an instance of the class will be returned.
    
    If `o` is an `Iterable`, its first element must be a dotted path to a
    class declaring `__call__()`:
    
    * If its length is 2, its second element must be either an `Iterable` or a
    `Mapping` containing respectively the arguments or the keyworded arguments
    that will be given to the class's constructors.
    
    * If its length is greater than 2, the second element must be an `Iterable`
    and the third element a `Mapping` containing respectively the arguments and
    the keyworded arguments that will be given to the class's constructors."""
    if callable(o):
        if isinstance(o, type):
            raise ValueError(f"Given callable cannot be a class ('{o}')")
        return o
    
    if isinstance(o, str):
        imported = import_string(o)
        if not callable(imported):
            raise ValueError(f"Given path does not point to a callable ('{o}')")
        
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
            raise ValueError(
                f"First element of given iterable does not point to a class ('{o[0]}')"
            )
        
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



def get_field(field: str, model: Type[models.Model]) -> models.Field:
    """Return the field named `field` of the given `Model`.
    
    Also work on reverse fields. The default name used by reverse fields
    (`[model]_set`) does not correspond to the actual name of the field when
    using `[model]._meta.get_field()`.
    
    Parameters :
        * `field` (`str`) - Name of the field.
        * `model` (`Type[models.Model]`) - Model to retrieve the field from.
    
    """
    return model._meta.get_field(field if not field.endswith("_set") else field[:-4])



def _check_field(fields: List[str], current_model: Type[models.Model], censor: Censor,
                 arbitrary_fields: Iterable[str] = ()) -> Tuple[Type[models.Model], str]:
    """Recursively check fields.
    
    Wrapped by `check_field()`, see `check_field()` docstring for more
    information."""
    token, subfields = fields[0], fields[1:]
    
    if censor.is_private(current_model, token):
        raise UnknownFieldError(current_model, token, censor)
    
    try:
        # Will raise FieldDoesNotExists if `token` does not correspond to a
        # field in `current_model` or an arbitrary field
        for a in arbitrary_fields:
            if token == a:
                # Set relation for the subfield check below
                field = Field()
                field.is_relation = False
                break
        else:
            field = get_field(token, current_model)
        
        # If there's at least one subfield, change `current_model`
        # to the next one, checking if the field correspond to a relation
        if subfields:
            if not field.is_relation:
                raise NotARelatedFieldError(current_model, token, censor)
            current_model = field.remote_field.model
    except FieldDoesNotExist:
        raise UnknownFieldError(current_model, token, censor)
    
    # Recursively check subfields, if any
    if subfields:
        return _check_field(subfields, current_model, censor)
    
    return current_model, token



def check_field(field: str, model: Type[models.Model], censor: Censor,
                arbitrary_fields: Iterable[str] = (), sep=".") -> Tuple[Type[models.Model], str]:
    """Recursively check that a field exists.
    
    `arbitrary_fields` can be a list of string indicating arbitrary field added
    by some `QuerySet` method (like `annotate()` or `prefetch_related()`.
    
    Related fields are separated by `sep`. For instance, if a model `Region`
    has a foreign key 'continent' to a model `Continent`, one could do
    `continent.name` using  dot `.` as `sep`.
    
    Additionally, return a tuple (model : `models.Model`, field : `str`)
    corresponding to the last model and last field. For instance, using the
    same models as above, calling `check_field(Region, "continent.name")`
    would return `(Continent, "name")`.
    
    Parameters :
        * `field` (`str`) - Name of the field.
        * `model` (`Type[models.Model]`) - Model to retrieve the field from.
        * `censor` (`Censor`) - Current censor use by the
          [`GenericQuery`](generic_query.md).
        * `arbitrary_fields` (`Iterable[str]`) - Optional list of arbitrary
          fields not present by default in the model, e.g. fields added by
          annotations.
        * `sep` (`str`) - Separator used for spanning relationship
          lookup (default to `.`).
    
    Raises :
        * `UnknownFieldError` if any of the field or foreign fields does not
        exists.
        * `FieldDepthError` if the depth of foreign field exceed
        `DGEQ_MAX_NESTED_FIELD_DEPTH`.
        * `NotAForeignFieldError` if a field used as a relation isn't a foreign
        field.
    """
    from .constants import DGEQ_MAX_NESTED_FIELD_DEPTH
    
    field_list = field.split(sep)
    max_depth = getattr(settings, "DGEQ_MAX_NESTED_FIELD_DEPTH", DGEQ_MAX_NESTED_FIELD_DEPTH)
    if len(field_list) >= max_depth:
        raise FieldDepthError(field)
    
    return _check_field(field_list, model, censor, arbitrary_fields)



def get_field_recursive(field: str, model: Type[models.Model], censor: Censor,
                        sep=".") -> Union[models.Field, ForeignField]:
    """Return the instance of `models.Field` corresponding to `field` inside
    `model`.
    
    Field can traverse relation using `sep`. For instance, if a model `Book`
    has a foreign key 'library' to a model `Library` which in turn has a foreign
    key `owner` to a model `Person`, one could do `library.owner.name` using
    dot `.` as `sep`.
    
    May raise the same exceptions as `check_field()`.
    """
    second_last_model, last_field_name = check_field(field, model, censor, sep=sep)
    return get_field(last_field_name, second_last_model)



def subquery_to_querydict(qs: str, fields_sep: str = None,
                          values_sep: str = None) -> QueryDict:
    """Create a `QueryDict` out of a subquery string.

    Subquery strings are value of commands using different key/value pairs,
    such as `c:annotate` or `c:join`.
    
    Parameters :
        * `qs` (`str`) - subquery string.
        * `fields_sep` (`str`) - field/value pairs separator, default to
          [DGEQ_SUBQUERY_SEP_FIELDS](settings.md#dgeq_subquery_sep_fields).
        * `values_sep` (`str`) - values separator, default to
          [DGEQ_SUBQUERY_SEP_VALUES](settings.md#dgeq_subquery_sep_values).
    
    Raises :
        * `ValueError` if no `=` is found in a key/value pair:
    """
    if fields_sep is None:
        fields_sep = constants.DGEQ_SUBQUERY_SEP_FIELDS
    if values_sep is None:
        values_sep = constants.DGEQ_SUBQUERY_SEP_VALUES
    
    query_dict = QueryDict(mutable=True)
    
    for kwarg in qs.split(fields_sep):
        kwarg = kwarg.split("=", 1)
        if len(kwarg) < 2:
            raise ValueError(f"A key/value pair must contains an equal '=', received '{kwarg[0]}'")
        
        k, values = kwarg
        for v in values.split(values_sep):
            query_dict.appendlist(k, v)
    
    return query_dict



def split_list_values(lst: Iterable[str], sep: str = ',') -> List[str]:
    """Return a list of the words in each string of `lst`, using `sep` as
    delimiter.
    
    Since most commands accept multiple value in two way :
    
    * With a separator, e.g. `length=>5000,<6000`
    * Reusing the field, e.g. `length=>5000&length=<6000`
    
    If both are combine, e.g. `length=>5000,<6000&length=!5500`, this can
    result in a QueryDict like this :
    
    * `<QueryDict: {'rivers.length': ['>5000,<6000', '!5500']}>`
    
    This function split every element in a list of unique value :
    
    ```python
    >>> utils.split_list_values(['>5000,<6000', '!5500'], ",")
    ['>5000', '<6000', '!5500']
    ```
    """
    return reduce(operator.add, (i.split(sep) for i in lst)) if lst else []



def is_reverse(field: models.Field) -> bool:
    """Return `True` if `field` is a reverse relation, `False` otherwise."""
    return field.auto_created and field.is_relation



def is_many(field: models.Field) -> bool:
    """Return `True` if `field` is a relation to multiple instance,
    `False` otherwise."""
    return type(field) in MANY_FOREIGN_FIELD



def is_one(field: models.Field) -> bool:
    """Return `True` if `field` is a relation to a unique instance,
    `False` otherwise."""
    return type(field) in UNIQUE_FOREIGN_FIELD



def split_related_field(model: Type[models.Model], fields: Iterable[str],
                        arbitrary_fields: Iterable[str] = ()
                        ) -> Tuple[Set[str], Set[str], Set[str]]:
    """Split the given `fields` of `model` into a tuple of iterables
    `(fields, one_fields, many_fields)`.

    * `one_fields` contains fields that are either `ForeignKey`, `OneToOneField`
      or `OneToOneRel`.
    * `many_fields` contains fields that are either `ManyToManyField`,
      `ManyToManyRel` or `ManyToOneRel`.
    * `fields` contains all other fields.

    Parameters :
        * `model` (`Type[models.Model]`) - Model to retrieve the field from.
        * `fields` (`str`) - Fields to be organized.
        * `arbitrary_fields` (`Iterable[str]`) - Optional list of arbitrary
          fields not present by default in the model, e.g. fields added by
          annotations.
    """
    set_fields = set()
    one_fields = set()
    many_fields = set()
    
    for field_name in fields:
        if field_name in arbitrary_fields:
            set_fields.add(field_name)
            continue
        
        field = get_field(field_name, model)
        if is_one(field):
            one_fields.add(field_name)
        elif is_many(field):
            many_fields.add(field_name)
        else:
            set_fields.add(field_name)
    
    return set_fields, one_fields, many_fields



def serialize_row(instance: models.Model, fields: Iterable[str] = (),
                  one_fields: Iterable[str] = (), many_fields: Iterable[str] = (),
                  joins: Dict = None) -> Dict[str, Any]:
    """Serialize an `instance` of `models.Model` according to the given fields
    and joins.
    
    See `split_related_field()` for the different field definition."""
    if joins is None:
        joins = dict()
    
    row = {f: getattr(instance, f) for f in fields}
    for f in one_fields:
        if f in joins.keys():
            row[f] = joins[f].fetch(instance)
        else:
            row[f] = getattr(instance, f)
            row[f] = None if row[f] is None else row[f].pk
    
    for f in many_fields:
        if f in joins.keys():
            row[f] = joins[f].fetch(instance)
        else:
            row[f] = list(map(lambda o: o.pk, getattr(instance, f).all()))
    return row



def serialize(instance: models.Model, public_fields: FieldMapping = None,
              private_fields: FieldMapping = None, user: [User, AnonymousUser] = None,
              use_permissions: bool = False) -> Dict[str, Any]:
    """Serialize an `instance` the same way `dgeq.GenericQuery` would serialize
    a row.
    
    Parameters :
        * `model` (`Type[models.Model]`) - Queried `Model`.
        * `public_fields`, `private_fields`, `user`, `use_permissions` - Allow
          filtering which field can be retrieved. See [`Censor`](censor.md).
    """
    if use_permissions and user is None:
        raise ValueError("user should be provided if use_permissions is set to True")
    
    model = instance.__class__
    include_hidden = getattr(settings, "DGEQ_INCLUDE_HIDDEN", False)
    fields = {
        f.get_accessor_name() if is_reverse(f) else f.name
        for f in model._meta.get_fields(include_hidden=include_hidden)
    }
    fields = Censor(public_fields, private_fields, user, use_permissions).censor(model, fields)
    fields, one_fields, many_fields = split_related_field(model, fields)
    
    row = {f: getattr(instance, f) for f in fields}
    for f in one_fields:
        row[f] = getattr(instance, f)
        row[f] = None if row[f] is None else row[f].pk
    for f in many_fields:
        row[f] = list(map(lambda o: o.pk, getattr(instance, f).all()))
    
    return row
