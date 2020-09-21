import logging
import re
import time
from typing import Any, Dict, List, Type, Union

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.db import models
from django.http import QueryDict

from . import commands, utils
from .censor import Censor
from .exceptions import DgeqError
from .joins import JoinMixin


logger = logging.getLogger(__file__)

# List of commands used to construct the queryset. They are all called in the
# given order when calling the method `prepare()` and `evaluate()` of
# `GenericQuery`. This list can be changed with the setting `DGEQ_COMMANDS`.
DEFAULT_PRE_COMMANDS: List[commands.Command] = [
    commands.Case(),
    commands.Annotate(),
    commands.Filtering(),
    commands.Distinct(),
    commands.Sort(),
    commands.Subset(),
    commands.Join(),
    commands.Show(),
    commands.Aggregate(),
    commands.Evaluate(),
]
DGEQ_PRE_COMMANDS: List[commands.Command] = [
    utils.import_callable(p) for p in getattr(settings, "DGEQ_PRE_COMMANDS", DEFAULT_PRE_COMMANDS)
]

DEFAULT_POST_COMMANDS: List[commands.Command] = [
    commands.Count(),
    commands.Time(),
]
DGEQ_POST_COMMANDS: List[commands.Command] = [
    utils.import_callable(p) for p in getattr(settings, "DGEQ_POST_COMMANDS", DEFAULT_POST_COMMANDS)
]

QueryDictType = Union[QueryDict, Type[QueryDict]]



class GenericQuery(JoinMixin):
    """Main class of the `dgeq` module.
    
    `public_fields` and `private_fields` allow the definition of *private* and
    *public* field specific model. For each model, only the field defined in
    public, or not defined in private, will be present in the resulting rows.
    If both private and public field are defined for a same model, only the
    public definition will be used.
    One can also decide to use django's permission implementation. Dgeq will
    check for the `view_[model]` permission for each related field.
    Note that permission can be used in conjunction with private and public
    field.
    If the user manually try to access a private field (or is missing a
    permission), an error will be raised as if the field didn't exists.
    
    To use it in a view, you need to create an instance with the corresponding
    `Model` and the requests' `QueryDict` and execute its `evaluate()` method :
    
    ```python
    q = dgeq.GenericQuery(request.user, models.Continent, request.GET)
    result = q.evaluate()
    ```
    
    You can then modify the result as needed or just return it as a
    `JsonResponse` :
    
    ```python
    q = dgeq.GenericQuery(request.user, models.Continent, request.GET)
    result = q.evaluate()
    return JsonResponse(result)
    ```
    
    If you want to hide the `password` and `email` of `User` :
    
    ```python
    private = {User : ['password', 'email']}
    q = dgeq.GenericQuery(
        request.user, models.Continent, request.GET, private_fields=private
    )
    ```
    
    If you want to hide everything but the `username` of `User` :
    
    ```python
    public = {User : ['username']}
    q = dgeq.GenericQuery(
        request.user, models.Continent, request.GET, public_fields=public
    )
    ```
    
    """
    
    result: Dict[str, Any]
    
    
    def __init__(self, model: Type[models.Model], query_dict: QueryDictType,
                 public_fields: utils.FieldMapping = None,
                 private_fields: utils.FieldMapping = None,
                 user: Union[User, AnonymousUser] = None, use_permissions: bool = False):
        if use_permissions and user is None:
            raise ValueError("user should be provided if use_permissions is set to True")
        
        super().__init__()
        
        self._query_dict_list = list(query_dict.lists())
        self._time = time.time()
        
        self.model = model
        self.censor = Censor(public_fields, private_fields, user, use_permissions)
        self.fields = {
            f.get_accessor_name() if utils.is_reverse(f) else f.name
            for f in model._meta.get_fields()
        }  # noqa
        self.arbitrary_fields = set()
        self.queryset = self.model.objects.all()
        self.result = {'status': True}
        self.case = True
        self.evaluated = True
        self.sliced = False
    
    
    def _evaluate(self) -> List[Dict[str, Any]]:
        fields = set(self.fields)
        fields |= set(self.arbitrary_fields)
        fields = self.censor.censor(self.model, fields)
        
        fields, one_fields, many_fields = utils.split_related_field(
            self.model, fields, self.arbitrary_fields
        )
        queryset = self.queryset.select_related(
            *[f for f in one_fields if f not in self.joins.keys()]
        )
        queryset = queryset.prefetch_related(
            *[f for f in many_fields if f not in self.joins.keys()]
        )
        
        rows = list()
        for item in queryset:
            rows.append(utils.serialize_row(item, fields, one_fields, many_fields, self.joins))
        
        return rows
    
    
    def evaluate(self):
        """Execute commands in `DGEQ_PRE_COMMANDS` on each field matching the
        command's regex, then evaluate the queryset (adding the rows to
        `self.result` before executing command in DGEQ_POST_COMMANDS.
        
        Return `self.result`.
        """
        try:
            for field, lst in self._query_dict_list:
                matching_commands = (c for c in DGEQ_PRE_COMMANDS if re.match(c.regex, field))
                for command in matching_commands:
                    command(self, field, lst)
            
            if self.evaluated:
                self.result['rows'] = self._evaluate()
            
            for field, lst in self._query_dict_list:
                matching_commands = (c for c in DGEQ_POST_COMMANDS if re.match(c.regex, field))
                for command in matching_commands:
                    command(self, field, lst)
            
            result = self.result
        
        except DgeqError as e:
            result = {
                "status":  False,
                "message": str(e),
                "code":    e.code,
                **{a: getattr(e, a) for a in e.details}
            }
        
        except Exception as e:  # pragma: no cover
            logger.warning("Unknown error in dgeq:", exc_info=True)
            result = {
                "status":  False,
                "message": str(e),
                "code":    "UNKNOWN"
            }
        
        return result
