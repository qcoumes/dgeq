# Helper Functions

To help your write new commands, you can use the following functions from `dgeq.utils`.

Throughout this guide, we’ll refer to the following models, which refer to the world geography :

```python
class Continent(models.Model):
    name = models.CharField(max_length=255, unique=True)


class Region(models.Model):
    name = models.CharField(max_length=255, unique=True)
    continent = models.ForeignKey(Continent, on_delete=models.CASCADE, related_name="regions")


class Country(models.Model):
    name = models.CharField(max_length=255, unique=True)
    area = models.BigIntegerField()
    population = models.BigIntegerField()
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="countries")


class River(models.Model):
    name = models.CharField(max_length=255, unique=True)
    discharge = models.IntegerField(null=True)
    length = models.IntegerField()
    countries = models.ManyToManyField(Country, related_name="rivers")
```

___

## `get_field`

* `get_field(field, model)`

Return the field named `field` of the given `Model`.

***Parameters*** :

* `field` (`str`) - Name of the field.
* `model` (`Type[models.Model]`) - Model to retrieve the field from.

```python
# Simple fields
>>> utils.get_field("name", Continent)
<django.db.models.fields.CharField: name>

# Foreign key
>>> utils.get_field("continent", Region)
<django.db.models.fields.related.ForeignKey: continent>

# M2M
>>> utils.get_field("countries", River)
<django.db.models.fields.related.ManyToManyField: countries>

# Reverse relation
>>> utils.get_field("rivers", Country)
<ManyToManyRel: django_dummy_app.river>
```


___

## `check_field`

* `check_field(field, model, censor, arbitrary_fields=(), sep=".")`

Recursively check that a field exists.

`arbitrary_fields` can be a list of string indicating arbitrary field added
by some `QuerySet` method (like `annotate()` or `prefetch_related())`.

Related fields are separated by `sep`. For instance, if a model `Region`
has a foreign key 'continent' to a model `Continent`, one could do `continent.name`
using  dot `.` as `sep`.

Additionally, return a tuple (model : `models.Model`, field : `str`)
corresponding to the last model and last field. For instance, using the
same models as above, calling `check_field(Region, "continent.name")`
would return `(Continent, "name")`.

***Parameters*** :

* `field` (`str`) - Name of the field.
* `model` (`Type[models.Model]`) - Model to retrieve the field from.
* `censor` (`Censor`) - Current censor use by the [`GenericQuery`](generic_query.md).
* `arbitrary_fields` (`Iterable[str]`) - Optional list of arbitrary fields not present by default in
  the model, e.g. fields added by annotations. 
* `sep` (`str`) - Separator used for spanning relationship lookup (default to `.`).

***Raises*** :

* `UnknownFieldError` if any of the field or foreign fields does not
exist.
* `FieldDepthError` if the depth of foreign field exceed
`DGEQ_MAX_NESTED_FIELD_DEPTH`.
* `NotAForeignFieldError` if a field used as a relation isn't a foreign
field.


```python
>>> utils.check_field("regions.countries", Continent, Censor())
# (<class 'django_dummy_app.models.Region'>, 'countries')

>>> utils.check_field("regions.countries.name", Continent, Censor())
# (<class 'django_dummy_app.models.Country'>, 'name')

>>> utils.check_field("notafield", Continent, Censor())
# dgeq.exceptions.UnknownFieldError: Unknown field 'notafield' in the table 'Continent', valid fields are ['id', 'name', 'regions']

>>> utils.check_field("name.notrelated", Continent, Censor())
# dgeq.exceptions.NotARelatedFieldError: Field 'name' in table 'Continent', is neither a foreign key nor a list of foreign key. Valid fields are ['regions']

>>> utils.check_field("regions.countries.region.continent", Continent, Censor())
# dgeq.exceptions.FieldDepthError: Field 'regions.countries.region.continent' exceed the allowed depth of related field of 4
```

___


## `subquery_to_querydict`

* `subquery_to_querydict(qs, fields_sep=None, values_sep=None)`

Create a [`QueryDict`](https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.QueryDict)
out of a subquery string.

Subquery strings are value of commands using different key/value pairs,
such as `c:annotate` or `c:join`.

***Parameters*** :

* `qs` (`str`) - subquery string.
* `fields_sep` (`str`) - field/value pairs separator, default to
  [DGEQ_SUBQUERY_SEP_FIELDS](settings.md#dgeq_subquery_sep_fields).
* `values_sep` (`str`) - values separator, default to
  [DGEQ_SUBQUERY_SEP_VALUES](settings.md#dgeq_subquery_sep_values).

***Raises*** :

* `ValueError` if no `=` is found in a key/value pair:


```python
>>> utils.subquery_to_querydict("field=rivers|filters=rivers.length=>2000'rivers.length<3000|to=rivers_count|func=count", fields_sep="|", values_sep="'")
# <QueryDict: {'field': ['rivers'], 'filters': ['rivers.length=>2000', 'rivers.length<3000'], 'to': ['rivers_count'], 'func': ['count']}>

>>> utils.subquery_to_querydict("field=rivers|torivers_count", fields_sep="|", values_sep="'")
# ValueError: A key/value pair must contains an equal '=', received 'torivers_count'
```


___

## `split_list_values`

* `split_list_values(lst, sep=',')`

Return a list of the words in each string of `lst`, using `sep` as
delimiter.

Since most commands accept multiple value in two ways :

* With a separator, e.g. `length=>5000,<6000`
* Reusing the field, e.g `length=>5000&length=<6000`

If both are combine, e.g. `length=>5000,<6000&length=!5500`, this can
result in a QueryDict like this :

* `<QueryDict: {'rivers.length': ['>5000,<6000', '!5500']}>`

This function split every element in a list of unique value.


***Parameters*** :

* `lst` (`List[str]`) A list of string.
* `sep` (`str`) delimiter.

```python
>>> utils.split_list_values(['>5000,<6000', '!5500'], ",")
# ['>5000', '<6000', '!5500']
```


___

## `split_related_field`

* `split_related_field(model, fields, arbitrary_fields=())`

Split the given `fields` of `model` into a tuple of iterables
`(fields, one_fields, many_fields)`.

* `one_fields` Contain fields that are either `ForeignKey`, `OneToOneField`
  or `OneToOneRel`.
* `many_fields` Contain fields that are either `ManyToManyField`,
  `ManyToManyRel` or `ManyToOneRel`.
* `fields` contains all other fields.

***Parameters*** :

* `model` (`Type[models.Model]`) - Model to retrieve the field from.
* `fields` (`Iterable[str]`) - Fields to be organized.
* `arbitrary_fields` (`Iterable[str]`) - Optional list of arbitrary fields not present by default in
  the model, e.g. fields added by annotations. 


___

## serialize

* `serialize(instance: models.Model, public_fields=None, private_fields=None,
  user=None, use_permissions=False)`

Serialize an `instance` the same way `dgeq.GenericQuery` would serialize
a row.

***Parameters:***

* `model` (`models.Model`) - instance to be serialized.
* `public_fields`, `private_fields`, `user`, `use_permissions` - Allow filtering which field can be
  retrieved. See [`Censor`](censor.md).
