# Getting Started

## Installation

You can install `DGeQ` either through `PyPI` :

```shell
pip3 install dgeq
```

Or by downloading the sources from github and running `setup.py` :

```shell
git clone https://github.com/qcoumes/dgeq
cd dgeq
python3 setup.py install
```


## Usage

To use `DGeQ`, you need first to import `GenericQuery` then in your *view* you can create an
instance with the `Model` queried and the `GET` dictionary. You can finally call the `evaluate()`
method to get the resulting JSON.

```python
from dgeq import GenericQuery

@require_GET
def continent(request: HttpRequest):
    query = GenericQuery(models.Continent, request.GET)
    result = query.evaluate()
    return JsonResponse(result)
```

For more advanced usage, see [settings](settings.md) and [`GenericQuery`](generic_query.md).




## Result Format

The result of `GenericQuery.evaluate()` is always a dictionary. It necessarily contains
the key `status`. 

* If `status` is `True`, the query succeeded, and the result can contain other fields :

    * `rows` if [`c:evaluate`](query_syntax.md#commands) was not set to `0`.
      `rows` is a list (maybe empty) containing the queried models.
    * `time` if [`c:time`](query_syntax.md#commands) was set to `1`.
    * `count` if [`c:count`](query_syntax.md#commands) was set to `1`.
    * Any field declared in the `to` argument of [`c:aggregate`](query_syntax.md#caggregate)

* If `status` is `False`, the request failed, and the result necessarily contains these fields :

    * `code` : A unique code (`str`) corresponding to the error.
    * `message` : A human-readable message corresponding to the error.

Different fields can be added according to each specific error.
See [`exceptions`](errors.md) for more details.

Below an example of a successful and a failed request :

* `continent/?c:time=1&c:limit=2&c:hide=regions&c:count=1`

```json
{
    "status": true,
    "count": 2, 
    "rows": [
        {"name": "Africa", "id": 1},
        {"name": "Americas", "id": 2}],
    "time": 0.005199432373046875
}
```

* `continent/?notafield=3`

```json
{
  "status": false,
  "message": "Unknown field 'notafield' in table 'Continent', valid fields are ['name', 'id', 'regions']",
  "code": "UNKNOWN_FIELD",
  "valid_fields": ["name", "id", "regions"],
  "unknown": "notafield"
}
```
