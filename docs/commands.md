#      

## Commands

Commands are the core of `DGeQ`, they allow you to change the behavior of `GenericQuery` by
modifying its attributes and the underlying `QuerySet`.

The list of `GenericQuery`'s attributes can be found [here](generic_query.md#attributes).

For each field/value pairs of the *query string*, the field part will be tested against the regex of
each command. The matching command will be called in the same order as defined
in [`DGEQ_COMMANDS`](settings.md#dgeq_commands).

`Commands` will be evaluated in the same order as written in the *query string*. A same `Command`
can be called multiple time, but will be called once for every matching field.

For instance, if we use the following *query string* :

* `country/?c:show=population&c:time=1&c:hide=id&c:show=area,name`

We have a call to `c:show`, followed by a call to `c:time`, `c:hide` and again `c:show`. Knowing
that the `dgeq.commands.Show` command's regex is `"^c:(show)|(hide)$"`, the following commands will
be called in that order with these arguments :

* `Show(query, 'c:show', ['population', 'area,name'])`
* `Limit(query, 'c:time', ['1'])`
* `Show(query, 'c:hide', ['id'])`

As you can see, `c:show` has been called only once with every value the first time it was
encountered.

## Custom Commands

A command is a `Callable` taking 3 arguments :

* The `GenericQuery`.
* The field that matched the `Callable`'s regex.
* The list of values associated with that field (extracted from
  the [`QueryDict`](https://docs.djangoproject.com/en/dev/ref/request-response/#django.http.QueryDict))

As mentioned multiple time, the `Callable` must have a `regex` attribute to test the field against.
So your two main solutions are either :

```python
def mycommand(query: 'GenericQuery', field: str, values: List[str]):
    ...



mycommand.regex = r"[REGEX]"
```

or

```python
# You can inherit from dgeq.commands.Command to ensure your __call__ argument are correct
class MyCommand(Command):
    
    regex = r"[REGEX]"
    
    def __call__(self, query: 'GenericQuery', field: str, values: List[str]):
        ...
```

In your command, you can interact with `query`'s attributes, especially `query.queryset`, using
the values from the *query string*.

Once your custom commands is written, add it to the list of commands in [`DGEQ_COMMANDS`](settings.md#dgeq_commands). 
