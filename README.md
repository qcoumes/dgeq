# DGeQ

[![PyPI Version](https://badge.fury.io/py/dgeq.svg)](https://badge.fury.io/py/dgeq)
[![Python 3.6+](https://img.shields.io/badge/Python-3.6+-brightgreen.svg)](#)
[![Django 2.0+, 3.0+](https://img.shields.io/badge/Django-2.0+,%203.0+-brightgreen.svg)](#)
[![License MIT](https://img.shields.io/badge/license-MIT-brightgreen.svg)](https://github.com/qcoumes/dgeq/blob/master/LICENSE)
[![Python package](https://github.com/qcoumes/dgeq/workflows/Python%20package/badge.svg)](https://github.com/qcoumes/dgeq/actions/)
[![Documentation Status](https://readthedocs.org/projects/dgeq/badge/?version=master)](https://dgeq.readthedocs.io/?badge=master)
[![codecov](https://codecov.io/gh/qcoumes/dgeq/branch/master/graph/badge.svg)](https://codecov.io/gh/qcoumes/dgeq)
[![CodeFactor](https://www.codefactor.io/repository/github/qcoumes/dgeq/badge)](https://www.codefactor.io/repository/github/qcoumes/dgeq)

DGeQ (**D**jango **Ge**neric **Q**uery) is a package that allows the construction of complex `GET`
query on any `Model`. It implements a [*query string* syntax](docs/query_syntax.md) allowing filtering,
join, annotation, aggregation and more.

Even though this package is primarily intended for the creation of public API, allowing to set
new endpoints with only few lines of code, it could also be used to communicate with other services
or a front-end framework.

The documentation can be found on [readthedocs](https://dgeq.readthedocs.io/en/latest/).

## Features

* You can choose which field of which `Model` can be queried.

* Natively support the follow types : `int`, `float`, `string`, `boolean`, `date` and `None`

* Natively support most of Django's lookup function : `(i)exact`, `(i)contains`, `(i)startswith`
  , `(i)endswith`, `gt(e)` and `lt(e)`.

* Supports spanning relationship lookup.

* Support commands such as Joins, Aggregations and Annotations.

* The syntax allows choosing which field the result should contain, avoiding over-fetching.

* Highly customizable : Allow the creation of new type, lookup function and commands. Parts of the
  *query string* syntax can also be customized.

You can find more about the syntax, and the possibility it offers [here](docs/query_syntax.md).

## Requirements

* `python >= 3.6.0`
* `django >= 2.0.0`
* `dateutil >= 2.8.0`


## Test it Online!

You can test `DGeQ` there if you want : [https://dgeq.qcoumes.com/](https://dgeq.qcoumes.com/).

## Quick Example

Let's show what `DGeQ` can do using the following models:

```python
# models.py

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

```python
# views.py

@require_GET
def continent(request: HttpRequest):
    q = dgeq.GenericQuery(models.Continent, request.GET)
    return JsonResponse(q.evaluate())

@require_GET
def region(request: HttpRequest):
    q = dgeq.GenericQuery(models.Region, request.GET)
    return JsonResponse(q.evaluate())

@require_GET
def country(request: HttpRequest):
    q = dgeq.GenericQuery(models.Country, request.GET)
    return JsonResponse(q.evaluate())

@require_GET
def river(request: HttpRequest):
    q = dgeq.GenericQuery(models.River, request.GET)
    return JsonResponse(q.evaluate())
```

In the following examples, the used URL pattern is `[model]/?[query]`. For instance, if we want to
query the continent `Africa` : `continent/?name=Africa`.

* Name of all the rivers in China : `river/?countries.name=China&c:show=name`

```json
{
  "status": true,
    "rows":[
        { "name":"Wu" },
        { "name":"Huai River" },
        { "name":"Yellow River" },
        { "name":"Red (Asia)" },
        { "name":"Ghaghara" },
        { "name":"Salween" },
        { "name":"Indus" },
        { "name":"Amur" },
        { "name":"Ob" },
        { "name":"Irrawaddy River" }
    ]
}
```

* Name, population and area of country in Asia finishing with `stan`, sorted by area :  
  `country/?region.continent.name=Asia&name=$stan&c:hide=id,region,rivers&c:sort=area`

```json
{
  "status":true,
  "rows":[
    {
      "area":142600,
      "population":8880300,
      "name":"Tajikistan"
    },
    {
      "area":199949,
      "population":6189700,
      "name":"Kyrgyzstan"
    },
    {
      "area":448969,
      "population":31959800,
      "name":"Uzbekistan"
    },
    {
      "area":488100,
      "population":5757700,
      "name":"Turkmenistan"
    },
    {
      "area":652864,
      "population":36296100,
      "name":"Afghanistan"
    },
    {
      "area":796095,
      "population":207906200,
      "name":"Pakistan"
    },
    {
      "area":2724902,
      "population":18080000,
      "name":"Kazakhstan"
    }
  ]
}
```

* Join the two lengthiest rivers of France :  
  `country/?name=France&c:join=field=rivers|limit=2|sort=-length|hide=countries`

```json
{
  "status": true,
  "rows": [
    {
      "name": "France",
      "area": 551500,
      "population": 64842500,
      "id": 75,
      "region": 20,
      "rivers": [
        {"name": "Rhine", "discharge": 2330, "length": 1233, "id": 43},
        {"name": "Loire", "discharge": 840, "length": 1012, "id": 22}
      ]
    }
  ]
}
```

* Sum and Avg of the length of every river in Europe :  
  `river/?countries.region.continent.name=Europe&c:aggregate=field=length|to=sum_length|func=sum,field=length|to=avg_length|func=avg&c:evaluate=0`

```json
{
  "status": true,
  "sum_length": 145943,
  "avg_length": 1871.0641025641025
}
```
