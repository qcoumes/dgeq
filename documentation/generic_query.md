# 

## `GenericQuery`

```python
class GenericQuery(model, query_dict, public_fields=None, private_fields=None,
                   user=None, use_permissions=False)

```

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
* `public_fields`, `private_fields`, `user`, `use_permissions` - Allow to filter which field can be
  retrieved. See [`Censor`](censor.md).
