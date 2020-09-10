import operator
from functools import reduce
from typing import Dict, Iterable, List, Set, Type, Union

from django.db import models

from . import utils
from .censor import Censor
from .exceptions import InvalidCommandError, NotARelatedFieldError
from .filter import Filter



class JoinMixin:
    """Mixin used for objects that can contains joins."""
    
    joins: Dict[str, 'JoinMixin']
    fields: Set[str]
    one_fields: Set[str]
    many_fields: Set[str]
    model: Type[models.Model]
    
    
    def __init__(self):
        self.joins = dict()
        self.fields = set()
        self.one_fields = set()
        self.many_fields = set()
    
    
    def add_field(self, field_name):
        """Add this field to an existing join."""
        field = self.model._meta.get_field(field_name)
        if isinstance(field, utils.UNIQUE_FOREIGN_FIELD):
            self.one_fields.add(field_name)
        else:
            self.many_fields.add(field_name)
    
    
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
                target = utils.get_field(base_name, model, censor, sep)
                self.joins[current] = JoinQuery(target, base_name, censor, [field_name])
            else:
                self.joins[current].add_field(field_name)
            
            # Recursively add the join
            self.joins[current].add_join(remains, join, model, censor, sep, base_name + sep)
        
        else:
            self.joins[field] = join
    
    
    def fetch(self, obj: models.Model) -> Union[dict, List[dict]]:
        raise NotImplementedError(f"Class using {self.__class__.__name__} must implement `fetch()`")



class JoinQuery(JoinMixin):
    """Represent a join in a `GenericQuery`.
    
    `JoinQuery` recursively contains other `JoinQuery`."""
    
    start: int
    limit: int = 0
    sort: Iterable[str]
    filters: Iterable[Filter]
    model: Type[models.Model]
    joins: Dict[str, 'JoinQuery']
    fields: Set[str]
    one_fields: Set[str]
    many_fields: Set[str]
    many: bool
    
    
    def __init__(self, target: utils.ForeignField, field: str, censor: Censor,
                 show: Iterable[str] = (), hide: Iterable[str] = (), sort: Iterable[str] = (),
                 filters: Iterable[Filter] = (), start: int = 0, limit: int = 0, ):
        super().__init__()
        
        self.model = target.related_model
        self.field = field
        self.start = start
        self.limit = limit
        self.sort = sort
        self.filters = filters
        self.many = isinstance(target, utils.MANY_FOREIGN_FIELD)
        
        target_model = target.related_model
        if show:
            fields = set(show)
        else:
            fields = {f.name for f in target_model._meta.get_fields()}  # noqa
            fields -= set(hide)
        fields = censor.censor(self.model, fields)
        
        self.fields = fields
        # Separating unique and many related fields
        self.one_fields = set()
        self.many_fields = set()
        for field_name in list(self.fields):
            field = target_model._meta.get_field(field_name)  # noqa
            if isinstance(field, utils.UNIQUE_FOREIGN_FIELD):
                self.fields.discard(field_name)
                self.one_fields.add(field_name)
            elif isinstance(field, utils.MANY_FOREIGN_FIELD):
                self.fields.discard(field_name)
                self.many_fields.add(field_name)
    
    
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
        field = second_last_model._meta.get_field(last_field_name)
        if getattr(field, "remote_field", None) is None:
            raise NotARelatedFieldError(second_last_model, query_dict['field'], censor)
        target = field
        target_model = target.related_model
        field_name = query_dict["field"].replace(".", "__")
        
        # Retrieve show & hide:
        show = [f for f in utils.split_list_strings(query_dict.getlist("show"), "'")]
        [utils.check_field(f, target_model, censor, arbitrary_fields) for f in show]
        hide = [f for f in utils.split_list_strings(query_dict.getlist("hide"), "'")]
        [utils.check_field(f, target_model, censor, arbitrary_fields) for f in hide]
        
        # Retrieve start & limit:
        if not (start := query_dict.get("start", "0")).isdigit():
            raise InvalidCommandError(
                "c:join", f"'start' value must be a non-negative integers (received '{start}')"
            )
        if not (limit := query_dict.get("limit", "0")).isdigit():
            raise InvalidCommandError(
                "c:join", f"'start' value must be a non-negative integers (received '{limit}')"
            )
        start, limit = int(start), int(limit)
        
        # Retrieve sort
        sort = utils.split_list_strings(query_dict.getlist("sort"), "'")
        for f in sort:
            utils.check_field(
                (f if not f.startswith("-") else f[1:]), target_model, censor, arbitrary_fields
            )
        
        # Retrieve filters
        filters = list()
        for f in query_dict.getlist("filters"):
            kwarg = f.split('=', 1)
            if len(kwarg) < 2:
                raise InvalidCommandError(
                    "c:join", f"Filters must contains an equal '=', received '{kwarg[0]}'"
                )
            k, v = kwarg
            utils.check_field(k, target_model, censor, arbitrary_fields)
            filters.append(Filter(k, v, case))
        
        return cls(target, field_name, censor, show, hide, sort, filters, start, limit)
    
    
    def prefetch(self, queryset: models.QuerySet) -> models.QuerySet:
        """Recursively prefetch joins to speed up the database query."""
        subquery = self.model.objects.all()

        if self.filters:
            q = reduce(operator.and_, [f.get() for f in self.filters])
            subquery = subquery.filter(q)
        
        if self.sort:
            subquery = subquery.order_by(*self.sort)
        
        subquery = subquery.select_related(
            *[f for f in self.one_fields if f not in self.joins.keys()]
        )
        subquery = subquery.prefetch_related(
            *[f for f in self.many_fields if f not in self.joins.keys()]
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
        
        if self.limit != 0:
            subquery = subquery[self.start:self.start + self.limit]
        else:
            subquery = subquery[self.start:]
        
        rows = list()
        for item in subquery:
            row = utils.serialize_row(
                item, self.fields, self.one_fields, self.many_fields, self.joins
            )
            rows.append(row)
        
        return rows
    
    
    def _fetch_unique(self, obj: models.Model) -> dict:
        field = self.field.split("__")[-1]
        related = getattr(obj, field)
        
        row = {f: getattr(related, f) for f in self.fields}
        
        for f in self.one_fields:
            if f in self.joins.keys():
                row[f] = self.joins[f].fetch(related)
            else:
                row[f] = getattr(related, f).pk
        
        for f in self.many_fields:
            if f in self.joins.keys():
                row[f] = self.joins[f].fetch(related)
            else:
                row[f] = list(map(lambda o: o.pk, getattr(related, f).all()))
        
        return row
    
    
    def fetch(self, obj: models.Model) -> Union[dict, List[dict]]:
        """Recursively retrieve joined data from an object."""
        return self._fetch_many(obj) if self.many else self._fetch_unique(obj)
