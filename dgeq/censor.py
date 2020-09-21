from typing import Dict, Iterable, Optional, Type, Union

from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.db import models

from dgeq.exceptions import UnknownFieldError


# Fields always private
DEFAULT_PRIVATE_FIELDS = {
    User: ["password"]
}
DGEQ_PRIVATE_FIELDS = getattr(settings, "DGEQ_PRIVATE_FIELDS", DEFAULT_PRIVATE_FIELDS)



class Censor:
    """Allow to completely remove specific fields of specific models in the
    resulting rows.
    
    Censor instance take two dictionary mapping `Model` to a list of
    public / private fields.
    
    A field will be removed if:
    
    * `model` has defined public fields and `field` is not in the list.
    * `model` has defined private fields and `field` is in the list.
    * `field` if a related field, `self.use_permissions` is `True`, and the
       current `user` has not the *view* permission on the related model.
       
    If `model` has both explicitly defined public and private fields, private
    fields are ignored.
    """
    
    
    def __init__(self, public: Dict[Type[models.Model], Iterable[str]] = None,
                 private: Dict[Type[models.Model], Iterable[str]] = None,
                 user: Union[User, AnonymousUser] = None, use_permissions=False):
        if use_permissions and user is None:
            raise ValueError("user should be provided if use_permissions is set to True")
        
        self.user = user
        self.public = public or dict()
        self.private = private or dict()
        self.use_permissions = use_permissions
    
    
    def is_private(self, model: Type[models.Model], field: str) -> bool:
        """Return `True` if this `Model`'s `field` should be removed for the
        current user."""
        if self.use_permissions:
            try:
                field_instance = model._meta.get_field(
                    field if not field.endswith("_set") else field[:-4]
                )
            except FieldDoesNotExist:
                raise UnknownFieldError(model, field, self)
            if field_instance.is_relation:
                content_type = ContentType.objects.get_for_model(field_instance.remote_field.model)
                if not self.user.has_perm(f"{content_type.app_label}.view_{content_type.model}"):
                    return True
        
        if model in DGEQ_PRIVATE_FIELDS and field in DGEQ_PRIVATE_FIELDS[model]:
            return True
        
        if model in self.public:
            return field not in self.public[model]
        
        if model in self.private:
            return field in self.private[model]
        
        return False
    
    
    def is_public(self, model: Type[models.Model], field: str) -> bool:
        """Return `True` if this `Model`'s `field` should not be removed for the
        current user."""
        return not self.is_private(model, field)
    
    
    def censor(self, model: Type[models.Model], fields: Iterable[str]):
        """Return a censored set corresponding to the public field of
        `fields`."""
        return {f for f in fields if self.is_public(model, f)}
