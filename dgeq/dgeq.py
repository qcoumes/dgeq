import logging
import re
import time
from typing import Dict, Optional, Set, Type, Union

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.db import models
from django.db.models import QuerySet
from django.http import QueryDict

from . import commands
from .exceptions import DgeqError
from .joins import JoinMixin, JoinQuery
from .censor import Censor
from .utils import FieldMapping, import_callable


logger = logging.getLogger(__file__)

# List of commands used to construct the queryset. They are all called in the
# given order when calling the method `prepare()` and `evaluate()` of
# `GenericQuery`. This list can be changed with the setting `DGEQ_COMMANDS`.
DEFAULT_COMMANDS = [
    commands.Case(),
    commands.Related(),
    commands.ComputeAnnotation(),
    commands.Annotate(early=True),
    commands.Filtering(),
    commands.Annotate(early=False),
    commands.Sort(),
    commands.Subset(),
    commands.Join(),
    commands.Show(),
    commands.Aggregate(),
    commands.Count(),
    commands.Evaluate(),
    commands.Time(),
]
DGEQ_COMMANDS = [
    import_callable(p) for p in getattr(settings, "DGEQ_COMMANDS", DEFAULT_COMMANDS)
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
    arbitrary_fields: Set[str]
    case: bool
    fields: Set[str]
    model: Type[models.Model]
    queryset: QuerySet
    result: dict
    time: float
    joins: Dict[str, JoinQuery]
    related: bool
    private_fields: Dict[Type[models.Model], Set[str]]
    
    
    def __init__(self, user: Union[User, AnonymousUser], model: Type[models.Model],
                 query_dict: QueryDictType, public_fields: FieldMapping = None,
                 private_fields: FieldMapping = None, use_permissions: bool = False):
        super().__init__()
        
        self._query_dict = query_dict
        self._step = 0
        
        self.model = model
        self.censor = Censor(user, public_fields, private_fields, use_permissions)
        self.case = True
        self.fields = {f.name for f in model._meta.get_fields()}  # noqa
        self.arbitrary_fields = set()
        self.time = time.time()
        self.result = {'status': True}
        self.related = True
        self.private_fields = private_fields or dict()
        self.queryset = self.model.objects.all()
    
    
    def step(self, n_step: Optional[int] = 1) -> None:
        """Allow to execute only one (or more) command at a time.
        
        You can optionally specify the number of step to be executed (default
        to 1), use `None` to execute all remaining the steps."""
        if n_step is None:
            n_step = len(DGEQ_COMMANDS) - self._step
        
        for command in DGEQ_COMMANDS[self._step:self._step + n_step]:
            # Build the QueryDict with keys matching the command's regex
            querydict = QueryDict(mutable=True)
            if command.regex is not None:
                for k, v in self._query_dict.lists():
                    if re.match(command.regex, k):
                        querydict.setlist(k, v)
            command(self, querydict)
            self._step += 1
    
    
    def evaluate(self):
        """Execute all the commands and return the result.
        
        If some commands had already been executed through `step()`, execute all
        the remaining command before returning the result."""
        try:
            self.step(n_step=None)
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
