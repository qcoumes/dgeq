from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

from django.conf import settings
from django.db.models import Q

from . import utils
from .aggregations import Aggregation, Annotation
from .exceptions import InvalidCommandError
from .filter import Filter
from .joins import JoinQuery


if TYPE_CHECKING:
    from .dgeq import GenericQuery


class Command(ABC):
    """Interface for commands."""
    regex = None
    
    
    @abstractmethod
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]) -> None:
        pass



class Annotate(Command):
    """Annotations are made up of key value pairs delimited by a pipe `|`:
    `key:value|key:value`. Valid keys are :
    
    * `field` (`field=population`) - Name of the field used for to compute the
        annotation.
    * `to` (`to=population_avg`) - Name of the field where the result of the
        annotation will be displayed.|
    * `func` (`func=avg`) - Function to use for the annotation. Value must be
        key of `DGEQ_DGEQ_AGGREGATION_FUNCTION` dictionary.
    * `filters` (`filters=mountains.height=]1500'mountains.name=*Mount`) - Allow
        to add an apostrophe `'` separated list of filters. These filters
        support search modifiers.
    * `delayed` (`delayed=1`) - Whether the annotation will be applied before
        (`0`) or after (`1`) the filtering of the main query. Default is `0`.|
    
    You can declare multiple annotation using a comma `,` or with multiple
    declaration of `c:annotate`. Each annotation's `to` must be unique.
    
    Filters must be given related to the main query model, and not the model
    used for the annotation. So if you have a query on `country/` and want to
    annotate on `rivers` count your query must be :
    
    * `country/?c:annotate=field=rivers|to=rivers_count|func=count|filters=rivers.length=>2000`
    
    and not:
    
    * `country/?c:annotate=field=rivers|to=rivers_count|func=count|filters=length=>2000`
    
    *note the field used in `filters`*.
    
    Field created by annotations on `to` can be used in other commands, such as
    `Sort`, `Show` and even `Aggregate`. They can also be used in filters,
    making it possible to filter on rivers average length for instance.
    
    Created annotation will be appended to `query.annotations`.
    
    Also append the field use by annotation to `query.arbitrary_fields`. See
    `Annotate` for more information."""  # noqa
    
    regex = "^c:annotate$"
    
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        annotations = utils.split_list_values(values)
        
        query.annotations = list()
        
        for a in annotations:
            a = Annotation.from_query_value(
                a, query.model, query.case, query.censor, query.arbitrary_fields
            )
            query.arbitrary_fields.add(a.to)
            query.queryset = a.apply(query.queryset)



class Aggregate(Command):
    """Create aggregations by parsing query's `c:aggregate` value.
    
    Aggregations are made up of key value pairs delimited by a pipe `|`:
    `key:value|key:value`. Valid keys are :

    * `field` (`field=population`) - Name of the field used for to compute the
        aggregation.
    * `to` (`to=population_avg`) - Name of the field where the result of the
        aggregation will be displayed.|
    * `func` (`func=avg`) - Function to use for the aggregation. Value must be
        key of `DGEQ_DGEQ_AGGREGATION_FUNCTION` dictionary.
    
    You can declare multiple aggregation using a comma `,` or with multiple
    declaration of `c:aggregate`. Each aggregation's `to` must be unique."""
    
    regex = "^c:aggregate$"
    
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        aggregations = utils.split_list_values(values)
        aggregations = [
            Aggregation.from_query_value(
                a, query.model, query.censor, query.arbitrary_fields
            ).get()
            for a in aggregations
        ]
        
        query.result = {
            **query.result,
            **query.queryset.aggregate(**dict(aggregations)),
        }



class Case(Command):
    """Modify filters' case-sensitiveness by looking at query's `c:case` value.
    
    A value of 1 mean the filters are case-sensitive, 0 mean case-insensitive,
    default to 1 if `c:case` is absent."""
    
    regex = "^c:case$"
    
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        if not values[-1].isdigit():
            raise InvalidCommandError(
                'c:case', f"value must be either 0 or 1 (received '{values[-1]}')"
            )
        query.case = bool(int(values[-1]))



class Count(Command):
    """Add the number of object in the database matching the query.
    
    Count will be added in the key `count` in the result if `c:count` value is
    1, default to 0 if `c:count` is absent."""
    
    regex = "^c:count$"
    
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        if not values[-1].isdigit():
            raise InvalidCommandError(
                "c:count", f"value must be either 0 or 1 (received '{values[-1]}')"
            )
        
        if int(values[-1]):
            query.result['count'] = query.queryset.count()



class Distinct(Command):
    """Eliminate duplicate from the resulting rows.
    
    By default, a query will not eliminate duplicate rows. In practice, this is
    rarely a problem, because simple queries don’t introduce the possibility of
    duplicate result rows. However, if your query spans multiple tables, it’s
    possible to get duplicate results when a query is evaluated."""
    
    regex = "^c:distinct$"
    
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        if query.sliced:
            raise InvalidCommandError(
                "c:distinct", "cannot be used after 'c:start' or 'c:limit'"
            )
        
        if not values[-1].isdigit():
            raise InvalidCommandError(
                f'c:distinct$', f"value must be either 0 or 1 (received '{values[-1]}')"
            )
        if int(values[-1]):
            query.queryset = query.queryset.distinct()



class Evaluate(Command):
    """Evaluate the query, putting the result in the `rows` key of the result.
    
    Rows will not be computed if `c:evaluated` value is 0, default to 1 if
    `c:evaluate` is absent."""
    
    regex = "^c:evaluate$"
    
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        if not values[-1].isdigit():
            raise InvalidCommandError(
                f'c:evaluate', f"value must be either 0 or 1 (received '{values[-1]}')"
            )
        query.evaluated = int(values[-1])



class Filtering(Command):
    """Apply filters on the query by looking at every query's field not starting
    with `c:`.
    
    Filters are created by using the standard `field=value` of query strings.
    The `field` portion must correspond to a particular field of the queried
    model.
    
    You can also query on related model using a dot `.` notation. For instance,
    in order to find all the disaster in Kenya, on would use the following pair
    string :`country.name=Kenya`. Related field can be nested up to
    `DGEQ_MAX_NESTED_FIELD_DEPTH`.
    
    If you query directly on a related model, and not on one of its field
    (E.G. `country` instead of `country.name`), `dgeq` will use it's primary key
    (most of the time `id`).
    
    The value portion can be of different types :

    * `int` (`?field=2`) - Plain integer.
    * `float` (`?field=3.14`) - Use dot `.` as decimal separator.
    * `string` (`?field=string`) - Plain string.
    * `boolean` (`?field=1`) - Use non-negative integers (`0` is `False`,
            anything else is `True`).
    * `date` (`?field=2004-12-02T22:00`) - An ISO 8601 [1] compliant string.
    * `null` (`?field=`) - Do not put any value.
    
    A modifier may be used in front of the value portion of the query string to
    better filter the rows. Only one modifier may be used, the second modifier
    character would be considered to be part of the value.
    
    * `<` (`country/?population=<500000`) - Less than.
    * `[` (`country/?population=]500000`) - Less than or equal.
    * `>` (`country/?population=>500000`) - Greater than.
    * `]` (`country/?population=[500000`) - Greater than or equal.
    * `!` (`country/?population=!500000`) - Different than.
    * `^` (`country/?name=^United`) - Starts with a string.
    * `$` (`country/?name=$Islands`) - Ends with a string.
    * `*` (`country/?name=*istan`) - Contains a string.
    * `~` (`country/?name=~z`) - Do not contain a string.
    
    To combine search modifier, either use the comma `,` :
    `country/?population=[500000,]500000`, or create another `field=value`
    with the other modifier : `country/?population=[500000&population=]500000`
    
    Modifiers are combined with a logical `AND`. For instance to get all the
    country with their name starting with `United`, but that does not contains
    `States` :
    
    * `country/?name=^United,~States` or `country/?name=^United&name=~States`

    [1] https://en.wikipedia.org/wiki/ISO_8601
    """
    
    regex = r"^(?!c:).*$"
    
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        if query.sliced:
            raise InvalidCommandError(
                field, "You cannot filter on fields after 'c:start' or 'c:limit'"
            )
        
        values = utils.split_list_values(values)
        filters = Q()
        for v in values:
            utils.check_field(field, query.model, query.censor, query.arbitrary_fields)
            filters &= Filter(field, v, query.case).get()
        
        query.queryset = query.queryset.filter(filters)



class Join(Command):
    """Allow to retrieve data of related models instead of only their PK.
    
     Joins are declared with the `c:join` field and is made up of key value
     pairs delimited by a pipe `|` : `key:value|key:value`. Valid keys are :

    * `field` (`field=region`) - Name of the field containing the related model.
    * `show` (`show=name'id`) - Only include the provided fields (multiple field
            names separated by an apostrophe `'`).
    * `hide` (`hide=id'countries`) - Include all field except the provided
            fields (multiple field names separated by an apostrophe `'`).
            Will be ignored if `show` is present.
    
    The following keys only make sense when `field` is either a
    `ManyToManyField`, its related field, or the related field of a
    `ForeignKey` :
    
    * `start` (`start=10`) - Start with the `Nth` object within the join (first
            is `0`). Default to `0`.
    * `limit` (`limit=20`) - Limit the number of object in the join, set to `0`
            to get all the objects (default to `0`).
    * `sort` (`sort=-area'id`) Sort the joined models by the given field
            (apostrophe `'` separated list)
    * `filters` (`filters=rivers=[1000'mountains=<3000`) Use `filters` to add an
            apostrophe `'` separated list of filters. These filters supports
            search modifiers.
    """
    
    regex = "^c:join$"
    
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        joins = utils.split_list_values(values)
        
        # Create joins in the query
        query_joins = dict()
        for j in joins:
            j = JoinQuery.from_query_value(
                j, query.model, query.case, query.censor, query.arbitrary_fields,
            )
            query_joins[j.field] = j
        
        # Sort join by their number of related model so that no useless
        # intermediary joins are created
        sorted_query_join = sorted(
            query_joins.items(), key=lambda i: i[0].count("__")
        )
        
        for f, j in sorted_query_join:
            query.add_join(f, j, query.model, query.censor)
        
        # Prefetch joins
        for j in query.joins.values():
            query.queryset = j.prefetch(query.queryset)



class Show(Command):
    """Allow to choose which field to include or remove.
    
    By default, every field of the queried model are included in the result. Use
    the `c:show` field to declare a comma separated
    """
    
    regex = "^c:((show)|(hide))$"
    
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        # Reset fields so that previous hide or show does not affect this one
        query.fields = {
            f.get_accessor_name() if utils.is_reverse(f) else f.name
            for f in query.model._meta.get_fields()
        }
        
        fields = utils.split_list_values(values)
        for f in fields:
            utils.check_field(f, query.model, query.censor, query.arbitrary_fields)

        if field == "c:show":
            query.fields = set(fields)
        else:
            query.fields |= set(query.arbitrary_fields)
            query.fields -= set(fields)



class Sort(Command):
    """Sort the resulting rows by the provided fields in `c:sort` field.
    
    Value must be a comma separated list of field. Prepend an hyphen `-` to use
    descending order on a specific field (E.G.: "-name").
    
    Sorting can be done on related field by using dot `.` notation.
    """
    
    regex = "^c:sort$"
    
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        if query.sliced:
            raise InvalidCommandError(
                "c:sort", "cannot be used after 'c:start' or 'c:limit'"
            )
        
        fields = utils.split_list_values(values)
        
        for f in fields:
            utils.check_field(
                f if not f.startswith("-") else f[1:], query.model, query.censor,
                query.arbitrary_fields
            )
        
        query.queryset = query.queryset.order_by(*[f.replace(".", "__") for f in fields])



class Subset(Command):
    """Allow to retrieve only a subset of the result with the `c:start` and
    `c:limit` commands.
    
    Use `c:start=N` to include the results from the Nth row (first row is 0),
    default to 0.
    Use `c:limit=N` to include up to N rows. To include every row, set N to 0.
    Default to `DGEQ_DEFAULT_LIMIT`.
    """
    
    regex = "^c:((start)|(limit))$"
    
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        from .constants import DGEQ_MAX_LIMIT
        
        if field == "c:start":
            if not values[-1].isdigit():
                raise InvalidCommandError(
                    f'c:start', f"value must be a non-negative integers (received '{values[-1]}')")
            start = int(values[-1])
            query.queryset = query.queryset[start:]
            query.sliced = True
        
        else:
            if not values[-1].isdigit():
                raise InvalidCommandError(
                    f'c:limit', f"value must be a non-negative integers (received '{values[-1]}')"
                )
            limit = int(values[-1])
            if limit > settings.DGEQ_MAX_LIMIT:
                raise InvalidCommandError(
                    f'c:limit',
                    f"value cannot be higher than '{DGEQ_MAX_LIMIT}' (received '{limit}')"
                )
            elif limit == 0:
                limit = settings.DGEQ_MAX_LIMIT
            
            query.queryset = query.queryset[:limit]
            query.sliced = True
            query.limit_set = True



class Time(Command):
    """Add the time taken by the server to compute your query.
    
    Time will be added in the key `time` in the result if `c:time` value is
    1, default to 0 if `c:time` is absent."""
    
    regex = "^c:time$"
    
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        if not values[-1].isdigit():
            raise InvalidCommandError(
                f'c:time', f"value must be either 0 or 1 (received '{values[-1]}')"
            )
        query.time = int(values[-1])


# Commands used when evaluating the query
DGEQ_COMMANDS = [
    utils.import_callable(p) for p in getattr(settings, "DGEQ_COMMANDS", [
        Case(),
        Annotate(),
        Filtering(),
        Distinct(),
        Sort(),
        Subset(),
        Join(),
        Show(),
        Aggregate(),
        Count(),
        Time(),
        Evaluate(),
    ])
]
