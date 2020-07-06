import datetime
from typing import Union
from dateutil.parser import isoparse

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
