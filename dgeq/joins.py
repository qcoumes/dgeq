import operator
from functools import reduce
from typing import Any, Dict, Iterable, List, Optional, Set, Type, Union

from django.db import models

from . import utils
from .censor import Censor
from .exceptions import InvalidCommandError, NotARelatedFieldError
from .filter import Filter



class JoinMixin:
    """Mixin used for objects that can contains joins."""
    
    joins: Dict[str, 'JoinMixin']
    fields: Set[str]
    _one_fields: Set[str]
    _many_fields: Set[str]
    model: Type[models.Model]
    
    
    def __init__(self):
        self.joins = dict()
        self.fields = set()
        self._one_fields = set()
        self._many_fields = set()
    
    
    def add_field(self, field_name):
        """Add this field to an existing join."""
        field = utils.get_field(field_name, self.model)
        if utils.is_one(field):
            self._one_fields.add(field_name)
        else:
            self._many_fields.add(field_name)
    
    
    def add_join(self, field: str, join: 'JoinMixin', model: Type[models.Model], censor: Censor,
                 sep="__", field_start: str = ""):
        """Add a `Join` to this query.
        
        If the `Join` is made up of several relation, recursively create the
        intermediary ones.
        
        `field_start` is only used internally by the function."""
        # Contains a relation
        if field.count(sep):
            current, remains = field.split(sep, 1)
            base_name = field_start + current
            field_name = remains.split(sep, 1)[0]
            
            # Create the intermediary `Join` if needed, only add the new field
            # otherwise
            if current not in self.joins:
                target = utils.get_field_recursive(base_name, model, censor, sep)
                self.joins[current] = JoinQuery(target, base_name, censor, False, [field_name])
            else:
                self.joins[current].add_field(field_name)
            
            # Recursively add the join
            self.joins[current].add_join(remains, join, model, censor, sep, base_name + sep)
        
        else:
            self.joins[field] = join
    
    
    def prefetch(self, queryset: models.QuerySet) -> models.QuerySet:
        raise NotImplementedError()
    
    
    def fetch(self, obj: models.Model) -> Union[dict, List[dict]]:
        raise NotImplementedError()



class JoinQuery(JoinMixin):
    """Represent a join in a `GenericQuery`.
    
    `JoinQuery` recursively contains other `JoinQuery`."""
    
    
    def __init__(self, target: utils.ForeignField, field: str, censor: Censor,
                 distinct: bool = False, show: Iterable[str] = (),
                 hide: Iterable[str] = (), sort: Iterable[str] = (), filters: Iterable[Filter] = (),
                 start: int = 0, limit: int = 0, ):
        super().__init__()
        
        self.model = target.related_model
        self.field = field
        self.start = start
        self.limit = limit
        self.sort = sort
        self.filters = filters
        self.distinct = distinct
        self.many = utils.is_many(target)
        target_model = target.related_model
        if show:
            fields = set(show)
        else:
            fields = {
                f.get_accessor_name() if utils.is_reverse(f) else f.name
                for f in target_model._meta.get_fields()  # noqa
            }
            fields -= set(hide)
        fields = censor.censor(self.model, fields)
        
        self.fields = fields
        # Separating unique and many related fields
        self._one_fields = set()
        self._many_fields = set()
        for field_name in list(self.fields):
            field = utils.get_field(field_name, self.model)
            if utils.is_one(field):
                self.fields.discard(field_name)
                self._one_fields.add(field_name)
            elif utils.is_many(field):
                self.fields.discard(field_name)
                self._many_fields.add(field_name)
    
    
    @classmethod
    def from_query_value(cls, value: str, model: Type[models.Model], case: bool, censor: Censor,
                         arbitrary_fields: Iterable[str] = ()) -> 'JoinQuery':
        """Create a `JoinQuery` from a 'c:join` query string."""
        try:
            query_dict = utils.subquery_to_querydict(value)
        except ValueError as e:
            raise InvalidCommandError("c:join", str(e))
        
        # Retrieve the field used to compute the join
        if "field" not in query_dict:
            raise InvalidCommandError("c:join", "'field' argument is missing")
        second_last_model, last_field_name = utils.check_field(
            query_dict["field"], model, censor, arbitrary_fields
        )
        field = utils.get_field(last_field_name, second_last_model)
        if not field.is_relation:
            raise NotARelatedFieldError(second_last_model, query_dict['field'], censor)
        target = field
        target_model = target.related_model
        field_name = query_dict["field"].replace(".", "__")
        
        # Retrieve show & hide:
        show = [f for f in utils.split_list_values(query_dict.getlist("show"), "'")]
        [utils.check_field(f, target_model, censor, arbitrary_fields) for f in show]
        hide = [f for f in utils.split_list_values(query_dict.getlist("hide"), "'")]
        [utils.check_field(f, target_model, censor, arbitrary_fields) for f in hide]
        
        # Retrieve start & limit:
        start = query_dict.get("start", "0")
        if not start.isdigit():
            raise InvalidCommandError(
                "c:join", f"'start' value must be a non-negative integers (received '{start}')"
            )
        limit = query_dict.get("limit", "0")
        if not limit.isdigit():
            raise InvalidCommandError(
                "c:join", f"'start' value must be a non-negative integers (received '{limit}')"
            )
        start, limit = int(start), int(limit)
        
        # Retrieve sort
        sort = utils.split_list_values(query_dict.getlist("sort"), "'")
        for f in sort:
            utils.check_field(
                (f if not f.startswith("-") else f[1:]), target_model, censor, arbitrary_fields
            )
        
        # Retrieve distinct
        distinct = query_dict.get("distinct", "0")
        if distinct.isdigit():
            distinct = bool(int(distinct[0]))
        else:
            raise InvalidCommandError(
                "c:join", f"'distinct' value must be either 0 or 1 (received '{distinct}')'"
            )
        
        # Retrieve filters
        filters = list()
        for f in utils.split_list_values(query_dict.getlist("filters"), "'"):
            kwarg = f.split('=', 1)
            if len(kwarg) < 2:
                raise InvalidCommandError(
                    "c:join", f"Filters must contains an equal '=', received '{kwarg[0]}'"
                )
            k, v = kwarg
            utils.check_field(k, target_model, censor, arbitrary_fields)
            filters.append(Filter(k, v, case))
        
        return cls(target, field_name, censor, distinct, show, hide, sort, filters, start, limit)
    
    
    def prefetch(self, queryset: models.QuerySet) -> models.QuerySet:
        """Recursively prefetch joins to speed up the database query."""
        subquery = self.model.objects.all()
        
        if self.filters:
            q = reduce(operator.and_, [f.get() for f in self.filters])
            subquery = subquery.filter(q)
        
        if self.sort:
            subquery = subquery.order_by(*self.sort)
        
        subquery = subquery.select_related(
            *[f for f in self._one_fields if f not in self.joins.keys()]
        )
        subquery = subquery.prefetch_related(
            *[f for f in self._many_fields if f not in self.joins.keys()]
        )
        
        new = queryset.prefetch_related(models.Prefetch(self.field, queryset=subquery))
        
        # Recursively prefetch inner joins
        for j in self.joins.values():
            new = j.prefetch(new)
        
        return new
    
    
    def _fetch_many(self, obj: models.Model) -> List[dict]:
        field = self.field.split("__")[-1]
        subquery = getattr(obj, field).all()
        
        if self.filters:
            q = reduce(operator.and_, [f.get() for f in self.filters])
            subquery = subquery.filter(q)
        
        if self.sort:
            subquery = subquery.order_by(*self.sort)
        
        if self.distinct:
            subquery = subquery.distinct()
        
        if self.limit != 0:
            subquery = subquery[self.start:self.start + self.limit]
        else:
            subquery = subquery[self.start:]
        
        rows = list()
        
        for item in subquery:
            row = utils.serialize_row(
                item, self.fields, self._one_fields, self._many_fields, self.joins
            )
            rows.append(row)
        return rows
    
    
    def _fetch_unique(self, obj: models.Model) -> Optional[Dict[str, Any]]:
        field = self.field.split("__")[-1]
        related = getattr(obj, field)
        
        row = {f: getattr(related, f) for f in self.fields}
        
        for f in self._one_fields:
            if f in self.joins.keys():
                row[f] = self.joins[f].fetch(related)
            else:
                row[f] = getattr(related, f)
                row[f] = None if row[f] is None else row[f].pk
        
        for f in self._many_fields:
            if f in self.joins.keys():
                row[f] = self.joins[f].fetch(related)
            else:
                row[f] = list(map(lambda o: o.pk, getattr(related, f).all()))
        
        return row
    
    
    def fetch(self, obj: models.Model) -> Union[Optional[Dict[str, Any]], List[dict]]:
        """Recursively retrieve joined data from an object."""
        return self._fetch_many(obj) if self.many else self._fetch_unique(obj)
