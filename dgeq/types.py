import datetime
from typing import Union

from dateutil.parser import isoparse
from django.conf import settings

from .utils import import_callable


Nothing = type(Ellipsis)



def datetime_parser(value: str) -> Union[Nothing, datetime.datetime]:
    """Try to parse the given value as a ISO 8601's datetime."""
    try:
        return isoparse(value)
    except ValueError:
        return ...



def int_parser(value: str) -> Union[Nothing, int]:
    """Try to parse the given value as an integer."""
    try:
        return int(value)
    except ValueError:
        return ...



def float_parser(value: str) -> Union[Nothing, float]:
    """Try to parse the given value as a float."""
    try:
        return float(value)
    except ValueError:
        return ...



def none_parser(value: str) -> Union[Nothing, None]:
    """Try to parse the given value as a float."""
    return None if value == "" else ...


# Parsers for query string values. Parsers must ba a callable or a dotted path
# (E.G. `dgeq.parsers.none_parser`) to a callable which return either the parsed
# type of Ellipsis if no type were matched. If every parser return Ellipsis, the
# value will be interpreted as a string.
DGEQ_TYPE_PARSERS = [
    import_callable(p) for p in getattr(settings, "DGEQ_TYPE_PARSERS", [
        none_parser,
        int_parser,
        float_parser,
        datetime_parser,
    ])
]
