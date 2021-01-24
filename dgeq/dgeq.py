import logging
import re
import time
from typing import Any, Dict, List, TYPE_CHECKING, Type, Union

from django.db import connection, models
from django.http import QueryDict

from . import utils
from .censor import Censor
from .commands import DGEQ_COMMANDS
from .constants import DGEQ_DEFAULT_LIMIT
from .exceptions import DgeqError
from .joins import JoinMixin


logger = logging.getLogger(__file__)

QueryDictType = Union[QueryDict, Type[QueryDict]]

if TYPE_CHECKING:
    from django.contrib.auth.models import AnonymousUser, User



class GenericQuery(JoinMixin):
    """Main class of the `dgeq` module.

    To use it in a view, you need to create an instance with the corresponding
    `Model` and the `request`'s `QueryDict`, then execute its `evaluate()`
    method :
    
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
    
    Parameters:
    
    * `model` (`Type[models.Model]`) - Queried `Model`.
    * `query_dict` (`QueryDict`) - Request's `GET` Querydict.
    * `public_fields`, `private_fields`, `user`, `use_permissions` - Allow to
      filter which field can be retrieved. See [`Censor`](censor.md).
    """
    
    result: Dict[str, Any]
    
    
    def __init__(self, model: Type[models.Model], query_dict: QueryDictType,
                 public_fields: utils.FieldMapping = None,
                 private_fields: utils.FieldMapping = None,
                 user: Union['User', 'AnonymousUser'] = None, use_permissions: bool = False):
        if use_permissions and user is None:
            raise ValueError("user should be provided if use_permissions is set to True")
        
        super().__init__()
        
        self._query_dict_list = list(query_dict.lists())
        
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
        self.limit_set = False
        self.time = False
    
    
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
        
        # Use the default limit if no limit has been given to 'c:limit'
        if DGEQ_DEFAULT_LIMIT and not self.limit_set:
            queryset = queryset[:DGEQ_DEFAULT_LIMIT]
        
        rows = list()
        for item in queryset:
            rows.append(utils.serialize_row(item, fields, one_fields, many_fields, self.joins))
        
        return rows
    
    
    def evaluate(self):
        """Evaluate the query and return a result.
        
        Execute commands in `DGEQ_COMMANDS` on each field/value of the query
        when the field match the command's regex. This function then compute the
        resulting rows."""
        start_time = time.time()
        start_query = len(connection.queries)
        
        try:
            for field, lst in self._query_dict_list:
                matching_commands = (c for c in DGEQ_COMMANDS if re.match(c.regex, field))
                for command in matching_commands:
                    command(self, field, lst)
            
            if self.evaluated:
                self.result['rows'] = self._evaluate()
            
            if self.time:
                self.result["time"] = time.time() - start_time
            
            result = self.result
        
        except DgeqError as e:
            result = {
                "status":  False,
                "message": str(e),
                "code":    e.code,
                **{a: getattr(e, a) for a in e.details}
            }
        
        except Exception:  # pragma: no cover
            logger.warning("Unknown error in dgeq:", exc_info=True)
            result = {
                "status":  False,
                "message": "An unknown error occurred, please contact the administrator.",
                "code":    "UNKNOWN"
            }
        
        logging.debug(
            f"The computation of this query string took {time.time() - start_time} seconds and "
            f"made {len(connection.queries) - start_query} queries to the database."
        )
        return result
