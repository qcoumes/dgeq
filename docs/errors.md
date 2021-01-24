# Errors

When an error occurs while evaluating a *query string*, a failed result is returned.

The `status` is set to `False` and the result necessarily contains these fields :

* `code` : A unique code (`str`) corresponding to the error.
* `message` : A human-readable message corresponding to the error.

Different fields can be added according to each specific error.

## INVALID_SEARCH_MODIFIER

Occurs when using a wrong combination of search modifier and value.

Contains the following field:

* `code` : `INVALID_SEARCH_MODIFIER`
* `message`: *Search modifier '[MODIFIER]' cannot be used on type '[TYPE]' (type was extrapolated
  from value '[VALUE]')*
* `modifier`: `[MODIFIER]`
* `value`: `[VALUE]`
* `type`: `[TYPE]`

Example:

* `country/?population=*1.2`

```json
{
  "status": false,
  "message": "Search modifier '*' cannot be used on type 'float' (type was extrapolated from value '1.2')",
  "code": "INVALID_SEARCH_MODIFIER",
  "modifier": "*",
  "value": 1.2,
  "type": "float"
}
```

## UNKNOWN_FIELD

Occurs when an unknown field is used inside a `Filter` or in any command. May also occurs when
trying to access a private field.

Contains the following field:

* `code` : `INVALID_SEARCH_MODIFIER`
* `message`: *Unknown field '[UNKNOWN_FIELD]' in the table '[TABLE]', valid fields
  are [VALID_FIELDS]*
* `valid_fields`: `[VALID_FIELDS]`
* `unknown`: `[UNKNOWN_FIELD]`
* `table`: `[TABLE]`

Example :

* `continent/?notafield=3`

```json
{
  "status": false,
  "message": "Unknown field 'notafield' in table 'Continent', valid fields are ['name', 'id', 'regions']",
  "code": "UNKNOWN_FIELD",
  "valid_fields": [
    "name",
    "id",
    "regions"
  ],
  "unknown": "notafield"
}
```

## NOT_A_RELATED_FIELD

Occurs when trying to use a field that is not a related field for
operation spanning relationships.


Contains the following field:

* `code` : `NOT_A_RELATED_FIELD`
* `message`: *Field '[FIELD]' in table '[TABLE]', is neither a foreign key nor "
  a list of foreign key. Valid fields are [RELATED_FIELDS]*
* `related_fields`: `[RELATED_FIELDS]`
* `field`: `[FIELD]`
* `table`: `[TABLE]`

Example :

* `continent/?name.something!=2`

```json
{
  "status": false,
  "message": "Field 'name' in table 'Continent', is neither a foreign key nor a list of foreign key. Valid fields are ['regions']",
  "code": "NOT_A_RELATED_FIELD",
  "table": "Continent",
  "field": "name",
  "related_fields": ["regions"]
}
```

## FIELD_DEPTH_ERROR


Occurs if a lookup spanning relationships exceed
`DGEQ_MAX_NESTED_FIELD_DEPTH` number of relation.


Contains the following field:

* `code` : `FIELD_DEPTH_ERROR`
* `message`: *Field '[FIELD]' exceed the allowed depth of related field of [MAX_DEPTH]*
* `max_depth`: `[MAX_DEPTH]`
* `field`: `[FIELD]`

Example :

* `continent/?regions.continent.regions.continent.name=Asia`

```json
{
  "status": false,
  "message": "Field 'regions.continent.regions.continent.name' exceed the allowed depth of related field of 4",
  "code": "FIELD_DEPTH_ERROR",
  "field": "regions.continent.regions.continent.name",
  "max_depth": 4
}
```

## INVALID_COMMAND_ERROR

Occurs when a command is misused or its value is invalid.

Contains the following field:

* `code` : `INVALID_COMMAND_ERROR`
* `message`: *Invalid command '[COMMAND]': [COMMAND_SPECIFIC_MESSAGE]*
* `commands`: `[COMMAND]`

Example :

* `country/?c:start=2&c:sort=name`

```json
{
  "status": false,
  "message": "Invalid command 'c:sort': cannot be used after 'c:start' or 'c:limit'",
  "code": "INVALID_COMMAND_ERROR",
  "command": "c:sort"
}
```

## UNKNOWN

Used when an unknown problem occurred.

* `code` : `UNKNOWN`
* `message`: *[ERROR_SPECIFIC_MESSAGE]*
* `commands`: `[COMMAND]`

Example :

> Would not be unknown if I had any :).
