#

## Native Types

When `DGeQ` receive a value, it goes through the parsers defined in
[`DGEQ_TYPE_PARSERS`](settings.md#dgeq_type_parsers) and use the first value returned that is
not `Ellipsis`. If every parser returned `Ellipsis`, the value is interpreted as a `str`.

`DGeQ` will natively detect the types : `int`, `float`, `string`, `boolean` (through `int`), `date`
and `None`, using the following parsers:

```python
DGEQ_TYPE_PARSERS = [
    "dgeq.types.none_parser",
    "dgeq.types.int_parser",
    "dgeq.types.float_parser",
    "dgeq.types.datetime_parser",
]
```

Note that the order does matter : the first value different from `Ellipsis`
will be used. So for instance, if you set `float_parser` before `int_parser`, all `int`
will be parsed as `float` (since any `int` is a valid `float`).

## Adding a Custom Type

If you want `DGeQ` to be able to parse other types, you only need to declare a function parsing
a value to the corresponding type, or returning `Ellipisis` (`...`) if it didn't match, then insert
that function into [`DGEQ_TYPE_PARSERS`](settings.md#dgeq_type_parsers).

For instance, one could write a Complex Number like this:

```python
def complex_parser(value: str):
    """Try to parse the given value as a complex."""
    try:
        return complex(value)
    except ValueError:
        return ...
```

and insert it after `int_parser` and `float_parser` so that it doesn't conflict with them
(since an `int` and a `float` are both a valid complex) :

```python
DGEQ_TYPE_PARSERS = [
    "dgeq.types.none_parser",
    "dgeq.types.int_parser",
    "dgeq.types.float_parser",
    complex_parser,
    "dgeq.types.datetime_parser",
]
```
