from datetime import datetime
from typing import Dict, Iterable, Type

from django.conf import settings
from django.db import models
from django.db.models import Q, QuerySet

from . import types
from .exceptions import SearchModifierError
from .utils import check_field, import_callable


# Parsers for query string values. The whole list can be redefined with the
# `DGEQ_TYPE_PARSERS` setting. Parsers must ba a callable or a dotted path
# (E.G. `dgeq.parsers.none_parser`) to a callable which return either the parsed
# type of Ellipsis if no type were matched. If every parser return Ellipsis, the
# value will be interpreted as a string.
DEFAULT_TYPE_PARSERS = [
    types.none_parser,
    types.int_parser,
    types.float_parser,
    types.datetime_parser,
]
TYPE_PARSERS = [
    import_callable(p) for p in getattr(settings, "DGEQ_TYPE_PARSERS", DEFAULT_TYPE_PARSERS)
]

# Table giving which django's lookup function to use according to the search
# modifier and the type. New entry can be added with the `DGEQ_FILTERS_TABLE`
# setting. Default entry can be disable by setting their value to `None`.
#
# This effectively allow to add search modifier or to modify on by declaring a
# entry and disabling the old one corresponding to the same function.
#
# For strings, the value is a tuple with the first element being the lookup
# to use if the search is NOT case-sensitive.
DEFAULT_FILTERS_TABLE = {
    ('', int):         'exact',
    ('', str):         ('iexact', 'exact'),
    ('', datetime):    'exact',
    ('', type(None)):  'exact',
    
    ('!', int):        'exact',
    ('!', str):        ('iexact', 'exact'),
    ('!', datetime):   'exact',
    ('!', type(None)): 'exact',
    
    ('>', int):        'gt',
    ('>', float):      'gt',
    ('>', str):        ('gt', 'gt'),
    ('>', datetime):   'gt',
    
    ('[', int):        'gte',
    ('[', float):      'gte',
    ('[', str):        ('gte', 'gte'),
    ('[', datetime):   'gte',
    
    ('<', int):        'lt',
    ('<', float):      'lt',
    ('<', str):        ('lt', 'lt'),
    ('<', datetime):   'lt',
    
    (']', int):        'lte',
    (']', float):      'lte',
    (']', str):        ('lte', 'lte'),
    (']', datetime):   'lte',
    
    ('^', str):        ('istartswith', 'startswith'),
    ('$', str):        ('iendswith', 'endswith'),
    ('*', str):        ('icontains', 'contains'),
    ('~', str):        ('icontains', 'contains'),
}
FILTERS_TABLE = {
    **DEFAULT_FILTERS_TABLE,
    **getattr(settings, "DGEQ_FILTERS_TABLE", dict()),
}

# Compute search modifiers from FILTERS_TABLE
SEARCH_MODIFIERS = [i[0] for i in FILTERS_TABLE.keys()]

# Default behaviour is to use `queryset.filter()` when filtering. Search
# modifier in this list will use `queryset.exclude()` instead. This list can
# be changed with the setting `DGEQ_EXCLUDE_SEARCH_MODIFIER`
EXCLUDE_SEARCH_MODIFIERS = getattr(settings, 'DGEQ_EXCLUDE_SEARCH_MODIFIER', ['!', '~'])



class Filter:
    """Represent a search filter in a `GenericQuery`"""
    
    
    def __init__(self, field: str, value: str, case: bool, model: Type[models.Model],
                 arbitrary_fields: Iterable[str] = (),
                 hidden_fields: Dict[Type[models.Model], Iterable[str]] = None):
        """Create a `Filter` from field-value pair of a query string.
        
        `case` indicate whether the filter is case-sensitive (`True`) or not.
        
        `value` must include the search modifier, if any.
        """
        if hidden_fields is None:
            hidden_fields = dict()
        
        check_field(field, model, arbitrary_fields, hidden_fields)
        
        # Extract optional modifier from value, if any
        if value and value[0] in SEARCH_MODIFIERS:
            modifier, value = value[0], value[1:]
        else:
            modifier = ""
        
        self.field = field.replace(".", "__")
        self.modifier = modifier
        for parser in TYPE_PARSERS:
            if (v := parser(value)) is not ...:
                self.value = v
                break
        else:
            self.value = value
        self.case = case
    
    
    def get(self) -> Q:
        """Return a `Q` object corresponding to this `Filter`."""
        try:
            lookup = FILTERS_TABLE[(self.modifier, type(self.value))]
            if isinstance(self.value, str):
                lookup = lookup[self.case]
        except KeyError:
            raise SearchModifierError(self.modifier, self.value)
        
        if self.modifier not in EXCLUDE_SEARCH_MODIFIERS:
            q = Q(**{self.field + "__" + lookup: self.value})
        else:
            q = ~Q(**{self.field + "__" + lookup: self.value})
        
        return q
    
    
    def __eq__(self, other: 'Filter'):
        return (
            self.value == self.value
            and self.field == self.field
            and self.modifier == self.modifier
        )
    
    
    def apply(self, queryset: QuerySet) -> QuerySet:
        """Create a new `QuerySet` by applying this filter to the given
        one."""
        return queryset.filter(self.get())
