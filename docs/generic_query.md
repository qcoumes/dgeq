#

## `GenericQuery`

* `class GenericQuery(model, query_dict, public_fields=None, private_fields=None, user=None, use_permissions=False)`

Main class of the `dgeq` module.

To use it in a view, you need to create an instance with the corresponding
`Model` and the `request`'s `QueryDict`, then execute its `evaluate()` method :

```python
q = dgeq.GenericQuery(request.user, models.Continent, request.GET)
result = q.evaluate()
```

You can then modify the result as needed or just return it as a
`JsonResponse` :

```python
q = dgeq.GenericQuery(request.user, models.Continent, request.GET)
result = q.evaluate()
return JsonResponse(result)
```

***Parameters:***

* `model` (`Type[models.Model]`) - Queried `Model`.
* `query_dict` (`QueryDict`) - Request's `GET` Querydict.
* `public_fields`, `private_fields`, `user`, `use_permissions` - Allow filtering which field can be
  retrieved. See [`Censor`](censor.md).

## Attributes

`GenericQuery` interact with [`Commands`](commands.md) mainly through its attributes.

Below is table of the  attributes used by native commands that you can interact with in your
own [custom commands](commands.md#custom-commands) :


|       Name       |         Type         |         Description        |
|:----------------:|:--------------------:|:---------------------------|
|`model`           |`Type[models.Model]`  |Model queried.              |
|`censor`          |[`Censor`](censor.md) |Censor used to hide fields. |
|`fields`          |`Set[str]`            |Set of fields that will be present in the resulting rows. [`c:hide`](query_syntax.md#commands), [`c:show`](query_syntax.md#commands)  and [`Censor`](censor.md) interact with this attribute.|
|`arbitrary_fields`|`Set[str]`            |Set of arbitrary fields added to the result. Fields are appended to this set by [`c:annotate`](query_syntax.md#cannotate). `arbitrary_fields` is then used by most commands interacting with the `Model` fields (e.g. [filters](query_syntax.md#filters), [`c:show`](query_syntax.md#commands), [`c:sort`](query_syntax.md#commands), [`c:aggregate`](query_syntax.md#caggregate), ...).|
|`queryset`        |`QuerySet`            |The actual underlying `QuerySet`. Most commands interact directly with the `Queryset`|
|`case`            |`bool`                |Indicate whether lookup should use their case-sensitive (`True`) version or not (`False`). Only modified by [`c:case`](query_syntax.md#commands), but used by other commands. Default to `True`.|
|`evaluated`       |`bool`                |Indicate whether the resulting rows should be included in the result (`True`) or not (`False`). Only modified by [`c:evaluated`](query_syntax.md#commands). Default to `True`|
|`sliced`          |`bool`                |Indicate whether the queryset has already been slice (through [`c:start`](query_syntax.md#commands) and [`c:limit`](query_syntax.md#commands)). Use for `QuerySet` methods raising an exception when called after slicing. Default to `False`|
|`limit_set`       |`bool`                |Indicate whether a limit has been set through [`c:limit`](query_syntax.md#commands) (`True`), or if the [`DGEQ_DEFAULT_LIMIT`](settings.md#dgeq_default_limit) setting should be used (`False`). Default to `False`|
|`time`            |`bool`                |Indicate whether the time taken to compute the result must be included in said result (`True`) or not (`False`). Only modified by [`c:time`](query_syntax.md#commands). Default to `False`|
|`joins`           |`Dict[str, JoinMixin]`|Joins stored by [`c:join`](query_syntax.md#cjoin) used when evaluating the resulting rows.|

&nbsp;
