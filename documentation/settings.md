# Settings

Some settings can be modified in your `settings.py` to customize how `dgeq` works.


## `DGEQ_TYPE_PARSERS`

Take a list of function used to parse the value of a *field/value* pair in a
query string.

Parsers must ba a callable or a dotted path (E.G. `dgeq.parsers.none_parser`)
to a callable which return either the parsed type, or `Ellipsis` if no type
were matched. If every parser returned `Ellipsis`, the value will be interpreted
as a string.

You can directly use the imported parser or the corresponding dotted path.

Default value is :

```python
DGEQ_TYPE_PARSERS = [
    "dgeq.types.none_parser",
    "dgeq.types.int_parser",
    "dgeq.types.float_parser",
    "dgeq.types.datetime_parser",
]
```


## `DGEQ_FILTERS_TABLE`

Table giving which django's lookup function to use according to the search
modifier and the type of the value. 

This table can be [updated](https://docs.python.org/3/library/stdtypes.html#dict.update)
 with the `DGEQ_FILTERS_TABLE` setting.

To add a filter, declare a new key/value pair :

```python
DGEQ_FILTERS_TABLE = {
    ('|', list): 'in'
}
```

To remove a filter, set it to `None` : 

```python
DGEQ_FILTERS_TABLE = {
    ('', int): None,
}
```

For strings, the value is a tuple with the first element being the lookup
to use if the search is NOT case-sensitive.

For some operation, you may want to take a look at `DGEQ_EXCLUDE_SEARCH_MODIFIER` below.

Default value is :

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

## `DGEQ_EXCLUDE_SEARCH_MODIFIER`

Default behaviour is to use `queryset.filter()` when filtering. Search
modifier in this list will use `queryset.exclude()` instead.

Default value is :

```python
DGEQ_EXCLUDE_SEARCH_MODIFIER = ['!', '~']
```

## `DGEQ_MAX_NESTED_FIELD_DEPTH`

Max depth of nested field, default value is `10`.

## `DGEQ_COMMANDS`

Allow the redefinition of the list of commands use by `dgeq`. For more information
about commands, see [Commands](/commands.md).

You can directly use the imported command or the corresponding dotted path.

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

## `DGEQ_DEFAULT_LIMIT`

Default limit on row count when 'c:limit' is not provided. Set to 0 to return
every row. Should not be higher than `DGEQ_MAX_LIMIT`.

Default value is `10`.

## `DGEQ_MAX_LIMIT`

Maximum number of row returned in a response (set to '0' to allow any limit).
The request will fail if an higher number is given to 'c:limit'

Default value is `200`.

## `DGEQ_PRIVATE_FIELDS`

Dictionary mapping django's model to a list field that will be marked as hidden.
Hidden field will never appear in the resulting row, and trying to interact with
them (filtering, joins, aggregation...) will produce the same error as if the
field did not exists.

This setting is global, for a more finer control in views, use the
`public_fields`, `private_fields` and `use_permissions` argument of `GenericQuery`.

For the key, you can directly use the imported model or the corresponding dotted path.

Default value is :

```python
DGEQ_PRIVATE_FIELDS = {
    "django.contrib.auth.models.User": ["password"]
}
```

## `DGEQ_SUBQUERY_SEP_FIELDS`

Character used in subquery for some commands (like `c:annotate` or `c:join`) to
delimit field/value pairs. For instance in `continent/?c:join=field=regions|hide=countries`,
this is the pipe `|` character.

Default to pipe `|`

## `DGEQ_SUBQUERY_SEP_FIELDS`

Character used in subquery for some commands (like `c:annotate` or `c:join`) to
delimit different values of a same fields.
For instance in `region/?c:join=field=countries|show=name'population`,
this is the apostrophe `'` character.

Default to apostrophe `'`


## `DGEQ_AGGREGATION_FUNCTION`

List function available to `Aggregation` and `Annotation`. Must be a dictionary
where the key is the name that can be used in a query string, and the value
a function returning an aggregate.

For the key, you can directly use the imported aggregate or the corresponding dotted path.

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
