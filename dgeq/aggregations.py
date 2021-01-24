from functools import reduce
from typing import Iterable, Tuple, Type

from django.conf import settings
from django.db import models
from django.db.models import QuerySet

from . import utils
from .censor import Censor
from .utils import import_class
from .exceptions import InvalidCommandError, UnknownFieldError
from .filter import Filter



class DistinctCount(models.Count):
    """Wrap `models.Count(distinct=True)`."""
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, distinct=True, **kwargs)


# Function used in aggregation and annotation.
DGEQ_AGGREGATION_FUNCTION = {
    k: import_class(a) for k, a in getattr(settings, "DGEQ_AGGREGATION_FUNCTION", {
        "max":    models.Max,
        "min":    models.Min,
        "avg":    models.Avg,
        "sum":    models.Sum,
        "stddev": models.StdDev,
        "var":    models.Variance,
        "count":  models.Count,
        "dcount": "dgeq.aggregations.DistinctCount",
    }.items())
}



class Aggregation:
    """Represents an aggregation.
    
    Fields:
        * `field` (`str`) - Field used to compute the aggregation.
        * `to` (`str`) - Name of the field where the result of the aggregation
                will be stored.
        * `func` (`Type[models.Aggregate]`) - Function used for the aggregation.
    """
    
    
    def __init__(self, field: str, to: str, func: Type[models.Aggregate]):
        self.field = field
        self.to = to
        self.func = func
    
    
    @classmethod
    def from_query_value(cls, value: str, model: Type[models.Model], censor: Censor,
                         arbitrary_fields: Iterable[str] = ()) -> 'Aggregation':
        """Create an `Aggregation` from a 'c:aggregate` query string."""
        try:
            query_dict = utils.subquery_to_querydict(value)
        except ValueError as e:
            raise InvalidCommandError("c:aggregate", str(e))
        
        # Retrieve the field used to compute the aggregation
        if "field" not in query_dict:
            raise InvalidCommandError("c:aggregate", "'field' argument is missing")
        utils.check_field(query_dict["field"], model, censor, arbitrary_fields)
        field = query_dict["field"].replace(".", "__")
        
        # Retrieve the function used to compute the aggregation
        if "func" not in query_dict:
            raise InvalidCommandError("c:aggregate", "'func' argument is missing")
        if query_dict["func"] not in DGEQ_AGGREGATION_FUNCTION:
            raise InvalidCommandError(
                "c:aggregate",
                f"Unknown function '{query_dict['func']}', valid functions are : "
                f"{list(DGEQ_AGGREGATION_FUNCTION.keys())}"
            )
        func = DGEQ_AGGREGATION_FUNCTION[query_dict["func"]]
        
        # Retrieve the field where to put the computed aggregation
        if "to" not in query_dict:
            raise InvalidCommandError("c:aggregate", "'to' argument is missing")
        if not query_dict["to"].isidentifier():
            raise InvalidCommandError(
                "c:aggregate",
                f"'to' value isn't a valid identifier ('{query_dict['to']}'). Valid identifiers "
                f"can use uppercase and lowercase letters 'A' through 'Z', the underscore "
                f"'_' and (except for the first character) the digits '0' through '9'."
            )
        try:
            # Use check_fields to check that a field DOES NOT exists by
            # expecting the exception it raises.
            utils.check_field(query_dict["to"], model, censor, arbitrary_fields)
            raise InvalidCommandError(
                "c:aggregate", f"'to' value ('{query_dict['to']}') is a already used by a field"
            )
        except UnknownFieldError:
            pass
        to = query_dict["to"]
        
        return cls(field, to, func)
    
    
    def get(self) -> Tuple[str, models.Aggregate]:
        """Return a tuple (keyword, aggregation).
        
        Can be used to create kwargs for a call to `queryset.aggregate()` :
        ```python
        kwargs = dict([a.get() for a in aggregations])
        queryset.aggregate(**kwargs)
        ```
        """
        return self.to, self.func(self.field)



class Annotation:
    """Represents an annotation.
    
    Fields:
        * `field` (`str`) - Field used to compute the annotation.
        * `to` (`str`) - Name of the field where the result of the annotation
                will be stored.
        * `func` (`Type[models.Aggregate]`) - Function used for the annotation.
        * `filters` (``) - Filters use for the annotation.
        * `early` (`bool`) - Whether the annotation will be applied before
            (`True`) or after (`False`) the filtering of the main query. See [1]
            for more information. Default is False.
            
    [1] https://docs.djangoproject.com/en/3.1/topics/db/aggregation/#order-of-annotate-and-filter-clauses
    """  # noqa
    
    
    def __init__(self, field: str, to: str, func: Type[models.Aggregate],
                 filters: Iterable[Filter] = (), early: bool = False):
        self.field = field
        self.to = to
        self.func = func
        self.filters = filters
        self.early = early
    
    
    @classmethod
    def from_query_value(cls, value: str, model: Type[models.Model], case: bool, censor: Censor,
                         arbitrary_fields: Iterable[str] = ()) -> 'Annotation':
        """Create an `Annotation` from a 'c:annotate` query string."""
        try:
            query_dict = utils.subquery_to_querydict(value)
        except ValueError as e:
            raise InvalidCommandError("c:annotate", str(e))
        
        # Retrieve the field used to compute the annotation
        if "field" not in query_dict:
            raise InvalidCommandError("c:annotate", "'field' argument is missing")
        utils.check_field(query_dict["field"], model, censor, arbitrary_fields)
        field = query_dict["field"].replace(".", "__")
        
        # Retrieve the function used to compute the annotation
        if "func" not in query_dict:
            raise InvalidCommandError("c:annotate", "'func' argument is missing")
        if query_dict["func"] not in DGEQ_AGGREGATION_FUNCTION:
            raise InvalidCommandError(
                "c:annotate",
                f"Unknown function '{query_dict['func']}', valid functions are : "
                f"{list(DGEQ_AGGREGATION_FUNCTION.keys())}"
            )
        func = DGEQ_AGGREGATION_FUNCTION[query_dict["func"]]
        
        # Retrieve the field where to put the computed annotation
        if "to" not in query_dict:
            raise InvalidCommandError("c:annotate", "'to' argument is missing")
        if not query_dict["to"].isidentifier():
            raise InvalidCommandError(
                "c:annotate",
                f"'to' value isn't a valid identifier ('{query_dict['to']}'). Valid identifiers "
                f"can use uppercase and lowercase letters 'A' through 'Z', the underscore "
                f"'_' and (except for the first character) the digits '0' through '9'."
            )
        try:
            # Use check_fields to check that a field DOES NOT exists by
            # expecting the exception it raises.
            utils.check_field(query_dict["to"], model, censor, arbitrary_fields)
            raise InvalidCommandError(
                "c:annotate", f"'to' value ('{query_dict['to']}') is a already used by a field"
            )
        except UnknownFieldError:
            pass
        to = query_dict["to"]
        
        # Retrieve optional filters used for the annotation
        filters = list()
        for f in utils.split_list_values(query_dict.getlist("filters"), "'"):
            kwarg = f.split('=', 1)
            if len(kwarg) < 2:
                raise InvalidCommandError(
                    "c:annotate", f"Filters must contains an equal '=', received '{kwarg[0]}'"
                )
            k, v = kwarg
            filters.append(Filter(k, v, case))
        
        # Check if this annotation must be delayed
        early = query_dict.get("early", "0")
        if early not in ["0", "1"]:
            raise InvalidCommandError("c:annotate", "'early' argument must be '0' or '1'")
        early = bool(int(early))
        
        return cls(field, to, func, filters, early)
    
    
    def apply(self, queryset: QuerySet) -> QuerySet:
        """Return a new `QuerySet` with this `Annotation` applied."""
        if self.filters:
            kwargs = {
                self.to: self.func(
                    self.field, filter=reduce(lambda i, j: i & j, (f.get() for f in self.filters))
                )
            }
        else:
            kwargs = {self.to: self.func(self.field)}
        
        return queryset.annotate(**kwargs)
