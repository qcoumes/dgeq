import re
import time
from typing import Dict, Iterable, Optional, Set, Type, Union

from django.conf import settings
from django.db import models
from django.db.models import QuerySet
from django.http import QueryDict

from . import commands
from .exceptions import DgeqError
from .joins import JoinMixin, JoinQuery
from .utils import import_callable


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



class GenericQuery(JoinMixin):
    """Main class of the `dgeq` module.
    
    To use it in a view, you need to create an instance with the corresponding
    `Model` and the requests' `QueryDict` and execute its `evaluate()` method :
    
    ```python
    q = dgeq.GenericQuery(models.Continent, request.GET)
    result = q.evaluate()
    ```
    
    You can then modify the result as needed or just return it as a
    `JsonResponse` :
    
    ```python
    q = dgeq.GenericQuery(models.Continent, request.GET)
    result = q.evaluate()
    return JsonResponse(result)
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
    hidden_fields: Dict[Type[models.Model], Set[str]]
    
    
    def __init__(self, model: Type[models.Model], query_dict: Union[QueryDict, Type[QueryDict]],
                 hidden_fields: Dict[Type[models.Model], Iterable[str]] = None):
        super().__init__()
        
        self._query_dict = query_dict
        self._step = 0
        
        self.model = model
        self.case = True
        self.fields = {f.name for f in model._meta.get_fields()}  # noqa
        self.arbitrary_fields = set()
        self.time = time.time()
        self.result = {'status': True}
        self.related = True
        self.hidden_fields = hidden_fields or dict()
        
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
            result = {
                "status":  False,
                "message": str(e),
                "code":    "UNKNOWN"
            }
        
        return result
