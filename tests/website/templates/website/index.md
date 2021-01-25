# DGeQ

This is a demonstration website for the [DGeQ](https://github.com/qcoumes/dgeq) package. Every link below can be used
to check the resulting JSON.

If you want to try writing query yourself, the valid enpoints are :

* [`geography/continent/`](geography/continent/)

* [`geography/region/`](geography/region/)

* [`geography/country/`](geography/country/)

* [`geography/river/`](geography/river/)

* [`geography/mountain/`](geography/mountain/)

* [`geography/forest/`](geography/forest/)

* [`geography/disaster/`](geography/disaster/)

The Models used are described in the chapter below.

## Query Syntax


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


class Mountain(models.Model):
    name = models.CharField(max_length=255, unique=True)
    height = models.IntegerField()
    countries = models.ManyToManyField(Country, related_name="mountains")


class Forest(models.Model):
    name = models.CharField(max_length=255, unique=True)
    area = models.BigIntegerField()
    countries = models.ManyToManyField(Country, related_name="forests")


class Disaster(models.Model):
    event = models.CharField(max_length=255)
    date = models.DateTimeField()
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="disasters")
    source = models.TextField()
    comment = models.TextField()
```

We have `Continent` that are composed of `Region` (e.g. *Northern Africa*, *Central America* , *Western
Europe*, ...) which are in turn composed of `Country`.

We then have `River` and `Mountain` that can be in multiple countries, and `Disaster` that
can be in only one country.


## Filters

Querying on a model without providing any filter would yield only the first instance of this model,
by the ordered defined in the model's class.

Filters are created by using the standard `field=value` of query strings. The `field` portion must
correspond to a particular field of the queried model.

You can also query on a related model using a dot `.` notation. For example, considering the
following data :

```json
{
  "event":"Flood",
  "date":"2009-11-04T00:00:00Z",
  "id":1,
  "comment":"...",
  "source":"IFRC",
  "country": {
    "area":591958,
    "id":110,
    "name":"Kenya",
    "population":50221100,
    "region":3,
    "rivers":[...],
    "mountains":[...],
    "disasters":[...]
  }
}
```

In order to find all the disaster in Kenya, on would use the following query string :

* [`disaster/?country.name=Kenya`](geography/disaster/?country.name=Kenya)disaster/?country.name=Kenya)

Default settings set the depth of nested fields to 10.

* [`disaster/?country.region.continent.name=Africa`](geography/disaster/?country.region.continent.name=Africa)

If you query directly on a related model, and not on one of its field (E.G. `country` instead of
`country.name`), `DGeQ` will use it's primary key (most of the time `id`). For instance, the
following queries are the same since `id` is the primary key of `Continent` :

* [`region/?continent=1`](geography/region/?continent=1)
* [`region/?continent.id=1`](geography/region/?continent.id=1)


## Value Types

The value portion can be of different types :

|   Type   |         Example         |                     Description                      |
|:--------:|-------------------------|------------------------------------------------------|
| `string` |`?field=string`          | Plain string|
| `boolean`|`?field=1`               | Use non-negative integers (`0` is `False`, anything else is `True`)|
| `null`   | `?field=` | Do not put any value |
| `int`   | `?field=2` | Plain integer |
| `float`   | `?field=3.14` | Use dot `.` as decimal separator |
| `datetime`   | `?field=2004-12-02T22:00` | An [ISO 8601](https://en.wikipedia.org/wiki/ISO_8601) compliant string. |


&nbsp;

## Search modifier

A modifier may be used in front of the value portion of the query string to better filter the
rows. Only one modifier may be used, the second modifier character would be considered to be part
of the value.

| Modifier |           Example           |      Description       |
|:--------:|-----------------------------|------------------------|
|`<`       |[`country/?population=<500000`](geography/country/?population=<500000)|Less than.              |
|`]`       |[`country/?population=]500000`](geography/country/?population=]500000)|Less than or equal.     |
|`>`       |[`country/?population=>500000`](geography/country/?population=>500000)|Greater than.           |
|`[`       |[`country/?population=[500000`](geography/country/?population=[500000)|Greater than or equal.  |
|`!`       |[`country/?population=!500000`](geography/country/?population=!500000)|Different than.         |
|`^`       |[`country/?name=^United`](geography/country/?name=^United)      |Starts with a string.   |
|`$`       |[`country/?name=$Islands`](geography/country/?name=$Islands)     |Ends with a string.     |
|`*`       |[`country/?name=*istan`](geography/country/?name=*istan)       |Contains a string.      |
|`~`       |[`country/?name=~z`](geography/country/?name=~z)           |Do not contain a string.|

&nbsp;  
To combine search modifier, either use the comma `,` : [`country/?population=[4700000,]4800000`](geography/country/?population=[4700000,]4800000), or
create another `field=value` with the other modifier : [`country/?population=[4700000population=]4800000`](geography/country/?population=[4700000population=]4800000)

Modifiers are combined with a logical `AND`. For instance to get all the country with their name
starting with `United`, but not containing `States` :

* [`country/?name=^United,~States`](geography/country/?name=^United,~States) or [`country/?name=^United&name=~States`](geography/country/?name=^United&name=~States)



## Commands

A command is a particular query string that allow a finer control over the resulting rows. These
are provided as query string attributes but are namespaced with `c:` to distinguish them from
filters.

|    Command    |              Example             |      Description      |
|:-------------:|----------------------------------|-----------------------|
| `c:aggregate` | See [`c:aggregate`](#caggregate).| See [`c:aggregate`](#caggregate).|
| `c:annotate`  | See [`c:annotate`](#annotate).   | See [`c:annotate`](#annotate).|
| `c:case`      | [`country/?c:case=0`](geography/country/?c:case=0)               | Set whether a search should be case-sensitive (`1`) or not (`0`). Default to `1`.|
| `c:count`     | [`country/?c:count=1`](geography/country/?c:count=1)              | If set to `1`, return the number of found item in the field `count` of the response. Default is `0`.
| `c:distinct`  | [`country/?c:distinct=1`](geography/country/?c:distinct=1)           | If set to `1`, eliminate duplicate row. Duplicate row may appear when using `c:join`.|
| `c:evaluate`  | [`country/?c:evaluate=0`](geography/country/?c:evaluate=0)           | Do not retrieve any rows from the database if set to `0` (`rows` will be an empty list). This will make the request much faster and can be useful if you only want to count rows or create aggregations. Default to `1`|
| `c:hide`      | [`country/?c:hide=id,area`](geography/country/?c:hide=id,area)         | Include all field except the provided fields (comma `,` separated list). Will be ignored if `c:show` is present.|
| `c:join`      | See [`c:join`](#cjoin).          | See [`c:join`](#cjoin).|
| `c:limit`     | [`country/?c:limit=20`](geography/country/?c:limit=20)             | Limit the result to at most `X` rows, set to `0` to get the max number of row allowed (default to `10` but can be modified in the setting).|
| `c:show`      | [`country/?c:show=name,id`](geography/country/?c:show=name,id)         | Only include the provided fields (comma `,` separated list).|
| `c:sort`      | [`country/?c:sort=-area,id`](geography/country/?c:sort=-area,id)        | Sort the rows by the provided fields (comma `,` separated list). Prepend an hyphen `-` to use descending order on a specific field.|
| `c:start`     | [`country/?c:start=10`](geography/country/?c:start=10)             | Start from the `Xth` row. Use in conjunction with `c:limit` to get a precise subset of row. For instance, using `c:start=10&c:limit=10` would yield the `10th` to `20th` objects. Default to `0`|
| `c:time`      | [`country/?c:time=1`](geography/country/?c:time=1)               | Shows the time taken server-side in seconds to process your request.|

&nbsp;  
Note that the order of commands and filters within the query string does matter. Some command will
produce different result if done after a filter (such as `c:aggregate`). A lot of command
will produce an error if done after using `c:limit` and `c:start`.


## `c:aggregate`

Sometimes you will need to retrieve values that are computed by summarizing or aggregating a
collection of objects, you can use `c:aggregate` for that. The syntax is :

Aggregate are made up of key value pairs delimited by a pipe `|` : `key:value|key:value`. Keys are :

|   Key   |       Example       |     Description      |
|:-------:|---------------------|----------------------|
| `field` | `field=population`  | Name of the field used to compute the aggregation.|
| `to`    | `to=population_avg` | Name of the field where the result of the aggregation will be displayed.|
| `func`  | `func=avg`          | Function used for the aggregation.|

&nbsp;  
Valid functions are :

* `max` - Maximum value of a field
* `min` - Minimum value of a field
* `sum` - Sum of a field
* `avg` - Average of a field
* `stddev`- Standard deviation of a field
* `var` - Variance of a field
* `count` - Count the number of non-null field.
* `dcount` - Count the number of distinct non-null field.

You can declare multiple aggregate using a comma `,` or declaring multiple time the field
`c:aggregate`. Each aggregate's `to` must be unique.

For instance, if you need the maximum, minimum and average population of countries
in Asia: :

* [`country/?region.continent.name=Asia&c:limit=100&c:evaluate=0&c:aggregate=field=population|func=avg|to=population_avg,field=population|func=max|to=population_max&c:aggregate=field=population|func=min|to=population_min`](geography/country/?region.continent.name=Asia&c:limit=100&c:evaluate=0&c:aggregate=field=population|func=avg|to=population_avg,field=population|func=max|to=population_max&c:aggregate=field=population|func=min|to=population_min)

Aggregation can also be done on model related to the one being queried using dot `.` notation.
Here the average height of mountains in France as an example :

* [`country/?name=France&c:limit=100&c:evaluate=0&c:aggregate=field=mountains.height|func=avg|to=mountain_avg`](geography/country/?name=France&c:limit=100&c:aggregate=field=mountains.height|func=avg|to=mountain_avg)

## `c:annotate`

Annotations are like aggregations, but over each item of the resulting rows. For instance,
annotation allow you to get the average length of the rivers inside each country.

Annotation is declared the same way as aggregation (`key:value|key:value`) but with more keywords:

|    Key    |                         Example                         |     Description      |
|:---------:|---------------------------------------------------------|----------------------|
| `field`   | `field=population`                                      | Name of the field used to compute the annotation.|
| `to`      | `to=population_avg`                                     | Name of the field where the result of the annotation will be displayed.|
| `func`    | `func=avg`                                              | Function used for the annotation.|
| `filters` |  `filters=mountains.height=]1500'mountains.name=*Mount` | **Optional** - Allow to add an apostrophe `'` separated list of filters to select only a subset of the given field. These filters supports `search modifiers`.|

&nbsp;  
Annotations use the same functions as aggregations, and can also be done on model related to the
one being queried using dot `.` notation.

Filters must be given related to the main query model, and not the model used for the annotation.
So if you have a query on `country/` and want to annotate on `rivers` count your query must be :

* [`country/?c:annotate=field=rivers|to=rivers_count|func=count|filters=rivers.length=>2000`](geography/country/?c:annotate=field=rivers|to=rivers_count|func=count|filters=rivers.length=>2000)

and not:

* [`country/?c:annotate=field=rivers|to=rivers_count|func=count|filters=length=>2000`](geography/country/?c:annotate=field=rivers|to=rivers_count|func=count|filters=length=>2000)

note the field used in `filters`.

Field created by annotations on `to` can be used in other commands, such as `c:sort`, `c:show` and
even `c:aggregate`. They can also be used in filters, making it possible to filter on rivers
average for instance.

Let's see some examples of annotations:

* Country sorted (desc) by their longest river :  
  [`country/?c:annotate=field=rivers.length|to=river_length|func=max&c:sort=river_length&c:limit=0`](geography/country/?c:annotate=field=rivers.length|to=river_length|func=max&c:sort=river_length&c:limit=0)
* Country with at least 5 mountains taller than 2000 meters :  
  [`country/?c:annotate=field=mountains|to=mountain_count|func=count|filters=mountains.height=>2000&mountain_count=[5&c:limit=0`](geography/country/?c:annotate=field=mountains|to=mountain_count|func=count|filters=mountains.height=>2000&mountain_count=[5&c:limit=0)
* Population of each continent :  
  [`continent/?c:annotate=field=regions.countries.population|func=sum|to=population&c:show=name,population&c:limit=0`](geography/continent/?c:annotate=field=regions.countries.population|func=sum|to=population&c:show=name,population&c:limit=0)
* Average number of mountain in a country in the world:  
  [`country/?c:annotate=field=mountains|to=mountain_count|func=count&c:aggregate=field=mountain_count|func=avg|to=mountain_count_avg&c:limit=0`](geography/country/?c:annotate=field=mountains|to=mountain_count|func=count&c:aggregate=field=mountain_count|func=avg|to=mountain_count_avg&c:limit=0)


## `c:join`

The default behaviour of the API is to not resolve related models. Only their primary key will be
retrieved.

The `c:join` command allow to retrieve these models, that is
retrieving their fields instead of just their `pk` in the rows.

A join is made up of key value pairs delimited by a pipe `|` : `key:value|key:value`. Valid keys are :

|    Key    |       Example      |     Description      |
|:---------:|--------------------|----------------------|
| `field`   | `field=region`     | **Mandatory** - Name of the field containing the related model.|
| `show`    | `show=name'id`     | Only include the provided fields (multiple field names separated by an apostrophe `'`).|
| `hide`    | `hide=id'countries`| Include all field except the provided fields (multiple field names separated by an apostrophe `'`). Will be ignored if `show` is present.|

&nbsp;  
The following keys only make sense when `field` is either a `ManyToManyField`, its related field, or the related field of a `ForeignKey`

|    Key    |                 Example                |     Description      |
|-----------|----------------------------------------|----------------------|
| `start`   | `start=10`                             | Start with the `Nth` object within the join (first is `0`). Default to `0`.
| `limit`   | `limit=20`                             | Limit the number of object in the join, set to `0` to get all the objects (default to `0`).
| `sort`    | `sort=-area'id`                        | Sort the joined models by the given field (apostrophe `'` separated list)
| `filters` | `filters=rivers=[1000'mountains=<3000` | Use `filters` to add an apostrophe `'` separated list of filters. These filters supports `search modifiers`.|

&nbsp;  
Here some example :

* Join the field `regions` of the model `Continent`, hiding their countries :  
  [`continent/?c:join=field=regions|hide=countries`](geography/continent/?c:join=field=regions|hide=countries)
* Join every earthquake of Japan :  
  [`country/?name=Japan&c:join=field=disasters|filters=event=*arthquake`](geography/country/?name=Japan&c:join=field=disasters|filters=event=*arthquake)
* Join the second highest mountain of China :  
  [`country/?name=China&c:join=field=mountains|show=name|start=1|limit=1|sort=-height&c:hide=disasters,forests,rivers`](geography/country/?name=China&c:join=field=mountains|show=name|start=1|limit=1|sort=-height&c:hide=disasters,forests,rivers)

Note that you can do nested join using dot `.`. For instance to get the `Region` of a `Disaster` :

* [`disaster/?id=1&c:join=field=country.region`](geography/disaster/?id=1&c:join=field=country.region)

In this case, the field `country` will also be joined, but only its field `region` will be in the
rows. If you want to get an other field, you must also join this field on its own :

* [`disaster/?id=1&c:join=field=country,field=country.region`](geography/disaster/?id=1&c:join=field=country,field=country.region)

The order of joins does not matter, these two request give the same rows :

* [`disaster/?id=1&c:join=field=country,field=country.region`](geography/disaster/?id=1&c:join=field=country,field=country.region)
* [`disaster/?id=1&c:join=field=country.region,field=country`](geography/disaster/?id=1&c:join=field=country.region,field=country)
