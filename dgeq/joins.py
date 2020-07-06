from typing import Dict, Iterable, List, Set, Type, Union

from django.db import models

from . import utils
from .exceptions import InvalidCommandError, NotARelatedFieldError
from .filter import Filter


# Field used to make a relation with another Model
FOREIGN_FIELDS = (
    models.OneToOneField, models.OneToOneRel,
    models.ForeignKey, models.ManyToOneRel,
    models.ManyToManyField, models.ManyToManyRel
)
# Fields containing a list of Foreign Keys.
MANY_FOREIGN_FIELD = (models.ManyToOneRel, models.ManyToManyField, models.ManyToManyRel)
# Fields containing only one Foreign Key
UNIQUE_FOREIGN_FIELD = (models.OneToOneRel, models.OneToOneField, models.ForeignKey)



class JoinMixin:
    """Mixin used for objects that can contains joins."""
    
    joins: Dict[str, 'JoinMixin']
    fields: Set[str]
    unique_foreign_field: Set[str]
    many_foreign_fields: Set[str]
    model: Type[models.Model]
    
    
    def __init__(self):
        self.joins = dict()
        self.fields = set()
        self.unique_foreign_field = set()
        self.many_foreign_fields = set()
    
    
    def add_field(self, field_name):
        """Add this field to an existing join."""
        field = self.model._meta.get_field(field_name)
        if isinstance(field, UNIQUE_FOREIGN_FIELD):
            self.unique_foreign_field.add(field_name)
        else:
            self.many_foreign_fields.add(field_name)
    
    
    def add_join(self, field: str, join: 'JoinMixin', model: Type[models.Model],
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
                target = utils.get_field(base_name, model, sep)
                self.joins[current] = JoinQuery(target, base_name, [field_name])
            else:
                self.joins[current].add_field(field_name)
            
            # Recursively add the join
            self.joins[current].add_join(remains, join, model, sep, base_name + sep)
        
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
    unique_foreign_field: Set[str]
    many_foreign_fields: Set[str]
    many: bool
    
    
    def __init__(self, target: utils.ForeignField, field: str, show: Iterable[str] = (),
                 hide: Iterable[str] = (), start: int = 0, limit: int = 0, sort: Iterable[str] = (),
                 filters: Iterable[Filter] = (),
                 hidden_fields: Dict[Type[models.Model], Iterable[str]] = None):
        super().__init__()
        
        self.model = target.related_model
        self.field = field
        self.start = start
        self.limit = limit
        self.sort = sort
        self.filters = filters
        self.many = isinstance(target, MANY_FOREIGN_FIELD)
        
        hidden_fields = hidden_fields or dict()
        hidden_fields = hidden_fields.get(self.model, set())
        target_model = target.related_model
        if show:
            self.fields = set(show)
        else:
            self.fields = {f.name for f in target_model._meta.get_fields()}
            self.fields -= set(hide)
        self.fields -= set(hidden_fields)
        
        # Separating unique and many related fields
        self.unique_foreign_field = set()
        self.many_foreign_fields = set()
        for field_name in [f for f in self.fields if f not in hidden_fields]:
            field = target_model._meta.get_field(field_name)  # noqa
            if isinstance(field, UNIQUE_FOREIGN_FIELD):
                self.fields.discard(field_name)
                self.unique_foreign_field.add(field_name)
            elif isinstance(field, MANY_FOREIGN_FIELD):
                self.fields.discard(field_name)
                self.many_foreign_fields.add(field_name)
    
    
    @classmethod
    def from_query_value(cls, value: str, model: Type[models.Model], case: bool,
                         arbitrary_fields: Iterable[str] = (),
                         hidden_fields: Dict[Type[models.Model], Iterable[str]] = dict()
                         ) -> 'JoinQuery':
        """Create a `JoinQuery` from a 'c:join` query string."""
        try:
            query_dict = utils.subquery_to_querydict(value)
        except ValueError as e:
            raise InvalidCommandError("c:join", str(e))
        
        # Retrieve the field used to compute the join
        if "field" not in query_dict:
            raise InvalidCommandError("c:join", "'field' argument is missing")
        second_last_model, last_field_name = utils.check_field(
            query_dict["field"], model, arbitrary_fields, hidden_fields
        )
        field = second_last_model._meta.get_field(last_field_name)
        if not isinstance(field, FOREIGN_FIELDS):
            raise NotARelatedFieldError(second_last_model, query_dict['field'])
        target = field
        target_model = target.related_model
        field_name = query_dict["field"].replace(".", "__")
        
        # Retrieve show & hide:
        show = [f for f in utils.split_list_strings(query_dict.getlist("show"), "'")]
        [utils.check_field(f, target_model, arbitrary_fields, hidden_fields) for f in show]
        hide = [f for f in utils.split_list_strings(query_dict.getlist("hide"), "'")]
        [utils.check_field(f, target_model, arbitrary_fields, hidden_fields) for f in hide]
        
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
                (f if not f.startswith("-") else f[1:]), target_model, arbitrary_fields,
                hidden_fields
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
            filters.append(Filter(k, v, case, target_model, hidden_fields))
        
        return cls(target, field_name, show, hide, start, limit, sort, filters, hidden_fields)
    
    
    def prefetch(self, queryset: models.QuerySet) -> models.QuerySet:
        """Recursively prefetch joins to speed up the database query."""
        subquery = self.model.objects.all()
        
        for f in self.filters:
            subquery = f.apply(subquery)
        
        if self.sort:
            subquery = subquery.order_by(*self.sort)
        
        subquery = subquery.select_related(
            *[f for f in self.unique_foreign_field if f not in self.joins.keys()]
        )
        subquery = subquery.prefetch_related(
            *[f for f in self.many_foreign_fields if f not in self.joins.keys()]
        )
        
        new = queryset.prefetch_related(models.Prefetch(self.field, queryset=subquery))
        
        # Recursively prefetch inner joins
        for j in self.joins.values():
            new = j.prefetch(new)
        
        return new
    
    
    def _fetch_many(self, obj: models.Model) -> List[dict]:
        field = self.field.split("__")[-1]
        subquery = getattr(obj, field).all()
        
        for f in self.filters:
            subquery = f.apply(subquery)
        
        if self.sort:
            subquery = subquery.order_by(*self.sort)
        
        if self.limit != 0:
            subquery = subquery[self.start:self.start + self.limit]
        else:
            subquery = subquery[self.start:]
        
        rows = list()
        for item in subquery:
            row = {f: getattr(item, f) for f in self.fields}
            
            for f in self.unique_foreign_field:
                if f in self.joins.keys():
                    row[f] = self.joins[f].fetch(item)
                else:
                    row[f] = getattr(item, f).pk
            
            for f in self.many_foreign_fields:
                if f in self.joins.keys():
                    row[f] = self.joins[f].fetch(item)
                else:
                    row[f] = list(map(lambda o: o.pk, getattr(item, f).all()))
            
            rows.append(row)
        return rows
    
    
    def _fetch_unique(self, obj: models.Model) -> dict:
        field = self.field.split("__")[-1]
        related = getattr(obj, field)
        
        row = {f: getattr(related, f) for f in self.fields}
        
        for f in self.unique_foreign_field:
            if f in self.joins.keys():
                row[f] = self.joins[f].fetch(related)
            else:
                row[f] = getattr(related, f).pk
        
        for f in self.many_foreign_fields:
            if f in self.joins.keys():
                row[f] = self.joins[f].fetch(related)
            else:
                row[f] = list(map(lambda o: o.pk, getattr(related, f).all()))
        
        return row
    
    
    def fetch(self, obj: models.Model) -> Union[dict, List[dict]]:
        """Recursively retrieve joined data from an object."""
        return self._fetch_many(obj) if self.many else self._fetch_unique(obj)
