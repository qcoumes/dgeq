# `Censor`

```python
class Censor(public=None, private=None, user=None, use_permissions=False)
```

Created from the arguments given to [`GenericQuery`](generic_query.md).

Allow to completely hide specific fields of specific models in the
resulting rows.

Hidden fields will never appear in the resulting rows, and trying to
interact with them (filtering, joins, aggregation...) will produce the same
error as if the field did not exist.

Censor instance take two dictionary mapping `Model` to a list of
public / private fields.

A field will be censored if:

* `model` has defined public fields and `field` is not in the list.
* `model` has defined private fields and `field` is in the list.
* `field` is a related field, `self.use_permissions` is `True`, and the
  given `user` does not have the `view` permission on the related model.

Public and private fields can also be defined project-wide in `settings.py`
using [`DGEQ_PUBLIC_FIELDS`](settings.md#dgeq_public_fields) and
[`DGEQ_PRIVATE_FIELDS`](settings.md#dgeq_private_fields).

If `model` has been defined in both this instance of `Censor` (through
`public` and `private` arguments) and in the corresponding settings, the
definition in the arguments prevails.

If `model` has both explicitly defined public and private fields, private
fields are ignored.

If `use_permissions` is set to `True`, `user` must be given else
`ValueError` will be raised.

***Parameters***:

* `public` (`Dict[Type[models.Model], Iterable[str]]`) - A `dict` mapping a
  `Model` to a list of its public fields.
* `private` (`Dict[Type[models.Model], Iterable[str]]`) - A `dict` mapping a
  `Model` to a list of its private fields.
* `user` (`User`) - User used to check permissions.
* `use_permission` (`bool`) - Whether the `view` permission of related
  `Model` will be checked.
