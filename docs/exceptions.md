#

## Exceptions

Exception allows the creation of an error result when a request failed.

The result is built like this:

```python
except DgeqError as e:
    result = {
        "status":  False,
        "message": str(e),
        "code":    e.code,
        **{a: getattr(e, a) for a in e.details}
    }

except Exception as:
    logger.warning("Unknown error in dgeq:", exc_info=True)
    result = {
        "status":  False,
        "message": "An unknown error occurred, please contact the administrator.",
        "code":    "UNKNOWN"
}
```

An exception inheriting `DgeqError` will build a comprehensive result with as many details as
possible, while any other exception will result in a vague *"An unknown error occurred, please
contact the administrator."*. The message stay vague and does not use the exception's message to
avoid the disclosure of sensitive information. The exception will be logged as a warning to help
administrator find the problem.

## Custom Exceptions

To define a custom exception, simply inherit `DgeqError`, define a `code` attribute, and define
the `__str__()` method.

You can also add arbitrary fields to the result by adding them as attributes of the exception and
creating a `details` attribute listing each of the one you want added to the result.

For a practical example, below is the definition of `SearchModifierError`:

```python
class SearchModifierError(DgeqError):
    """Raised when using a wrong combination of search modifier and value."""
    
    code = "INVALID_SEARCH_MODIFIER"
    details = ['modifier', 'value', 'type']
    
    
    def __init__(self, modifier: str, value: Any):
        self.modifier = modifier
        self.value = value
        self.type = type(value).__name__
    
    
    def __str__(self):
        return (
            f"Search modifier '{self.modifier}' cannot be used on type "
            f"'{type(self.value).__name__}' "
            f"(type was extrapolated from value '{self.value}')"
        )
```

To stay consistent with current `code`, only use upper-case letters, digits and underscore. `code`
must stay unique between exceptions. Currently, used code are:

* `INVALID_SEARCH_MODIFIER`
* `UNKNOWN_FIELD`
* `NOT_A_RELATED_FIELD`
* `FIELD_DEPTH_ERROR`
* `INVALID_COMMAND_ERROR`
* `UNKNOWN`

See [errors](errors.md) for more details about the existing exceptions.
