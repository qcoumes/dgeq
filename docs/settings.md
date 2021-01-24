# Settings

The following settings can be overridden or modified in your `settings.py` to customize
how `dgeq` works.

___

## `DGEQ_AGGREGATION_FUNCTION`

List functions available for [`c:aggregate`](query_syntax.md#caggregate)
and [`c:annotate`](query_syntax.md#cannotate). Must be a dictionary where the key
is the name used in a query string, and the value a function returning an aggregate.

For the key, you can directly use the imported aggregate, or the corresponding dotted path.

Default value is :

```python
DGEQ_AGGREGATION_FUNCTION = {
    "max":    models.Max,
    "min":    models.Min,
    "avg":    models.Avg,
    "sum":    models.Sum,
    "stddev": models.StdDev,
    "var":    models.Variance,
    "count":  models.Count,
    "dcount": "dgeq.aggregations.DistinctCount",
}
```

___

## `DGEQ_COMMANDS`

Allow the redefinition of the list of commands use by `DGeQ`. For more information about commands,
see [Commands](/commands.md).

You can directly use the imported command, or the corresponding dotted path.

Default value is :

```python
DGEQ_COMMANDS = [
    "dgeq.commands.Case",
    "dgeq.commands.Annotate",
    "dgeq.commands.Filtering",
    "dgeq.commands.Distinct",
    "dgeq.commands.Sort",
    "dgeq.commands.Subset",
    "dgeq.commands.Join",
    "dgeq.commands.Show",
    "dgeq.commands.Aggregate",
    "dgeq.commands.Count",
    "dgeq.commands.Time",
    "dgeq.commands.Evaluate",
]
```

___

## `DGEQ_DEFAULT_LIMIT`

Default limit on row count when [`c:limit`](query_syntax.md#commands) is not provided. Set to 0 to
return every row. Should not be higher than [`DGEQ_MAX_LIMIT`](#dgeq_default_limit).

Default value is `10`.

___

## `DGEQ_EXCLUDE_SEARCH_MODIFIER`

Default behaviour is to use `queryset.filter()` when filtering. Search modifier in this list will
use `queryset.exclude()` instead.

Default value is :

```python
DGEQ_EXCLUDE_SEARCH_MODIFIER = ['!', '~']
```

___

## `DGEQ_FILTERS_TABLE`

`DGeQ` use a table to find which Django's lookup function to use according to the search modifier
and the type of the value.

The table is defined as such :

```python
DGEQ_FILTERS_TABLE = {
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
```

For strings, the value is a tuple with the first element being the lookup to use if the search is
NOT case-sensitive.

This table can be [updated](https://docs.python.org/3/library/stdtypes.html#dict.update)
with the `DGEQ_FILTERS_TABLE` setting.

To add a filter, declare a new key/value pair :

```python
DGEQ_FILTERS_TABLE = {
    ('|', list): 'in'
}
```

To remove one of the default filter, set it to `None`:

```python
DGEQ_FILTERS_TABLE = {
    ('!', int): None
}
```

For some operation, you may want to take a look
at [`DGEQ_EXCLUDE_SEARCH_MODIFIER`](#dgeq_exclude_search_modifier) above.

___

## `DGEQ_MAX_LIMIT`

Maximum number of row returned in a response (set to '0' to allow any limit). The request will fail
if a higher number is given to [`c:limit`](query_syntax.md#commands)

Default value is `200`.

___

## `DGEQ_MAX_NESTED_FIELD_DEPTH`

Max depth of nested field, default value is `10`.

___

## `DGEQ_PRIVATE_FIELDS`

Dictionary mapping django's model to a list of fields that will be marked as hidden. Hidden fields
will never appear in the resulting row, and trying to interact with them (filtering, joins,
aggregation...) will produce the same error as if the field did not exist.

This setting is global, for a finer control in views, use the
`public_fields`, `private_fields` and `use_permissions` argument of `GenericQuery`.

For the key, you can directly use the imported model, or the corresponding dotted path.

Default value is :

```python
DGEQ_PRIVATE_FIELDS = {}
```

See [`Censor`](censor.md) for more information.

___

## `DGEQ_PUBLIC_FIELDS`

Dictionary mapping django's model to a list of fields that will be marked as public. Every other
fields of the model not marked as public will be considered hidden. Hidden fields will never appear
in the resulting row, and trying to interact with them (filtering, joins, aggregation...) will
produce the same error as if the field did not exist.

This setting is global, for a finer control in views, use the
`public_fields`, `private_fields` and `use_permissions` argument of `GenericQuery`.

For the key, you can directly use the imported model, or the corresponding dotted path.

Default value is :

```python
DGEQ_PUBLIC_FIELDS = {
    "django.contrib.auth.models.User": ["id", "username"]
}
```

See [`Censor`](censor.md) for more information.

___

## `DGEQ_SUBQUERY_SEP_FIELDS`

Character used in subquery for some commands (like [`c:annotate`](query_syntax.md#cannotate)
or [`c:join`](query_syntax.md#cjoin)) to delimit a field/value pairs. For instance
in `continent/?c:join=field=regions|hide=countries`, this is the pipe `|`
character.

Default to pipe `|`

___

## `DGEQ_SUBQUERY_SEP_VALUES`

Character used in subquery for some commands (like [`c:annotate`](query_syntax.md#cannotate)
or [`c:join`](query_syntax.md#cjoin)) to delimit different values of a same fields. For instance
in `region/?c:join=field=countries|show=name'population`, this is the apostrophe `'` character.

Default to apostrophe `'`

___

## `DGEQ_TYPE_PARSERS`

Take a list of function used to parse the value of a *field/value* pair in a query string.

Parsers must ba a callable or a dotted path (E.G. `dgeq.parsers.none_parser`)
to a callable which return either the parsed type, or `Ellipsis` if no type were matched. If every
parser returned `Ellipsis`, the value will be interpreted as a string.

Note that the order does matter : the first value different from `Ellipsis`
will be used. So for instance, if you set `float_parser` before `int_parser`, all `int`
will be parsed as `float` (since any `int` is a valid `float`).

You can directly use the imported parser, or the corresponding dotted path.

Default value is :

```python
DGEQ_TYPE_PARSERS = [
    "dgeq.types.none_parser",
    "dgeq.types.int_parser",
    "dgeq.types.float_parser",
    "dgeq.types.datetime_parser",
]
```
