from typing import Any, Type, Union

from django.conf import settings
from django.db import models


# Default max depth before a field lookup fail. Can be overridden in settings.py
MAX_FOREIGN_FIELD_DEPTH = getattr(settings, "DGEQ_MAX_FOREIGN_FIELD_DEPTH", 10)



class DgeqError(Exception):
    """Base exception for `dgeq` module.
    
    Exception inheriting `DgeqError` must declare attributes `code` containing
    an string containing only the character `[A-Z_]`. This code must be
    unique. Code `UNKNOWN` is reserved and must not be used.
    
    Such exceptions can also declare an attribute `details` containing a list
    of attribute's name that be output into the error payload."""
    
    code = "BASE_ERROR"
    details = []



class SearchModifierError(DgeqError):
    """Raised when using a wrong combination of search modifier and value."""
    
    code = "INVALID_SEARCH_MODIFIER"
    details = ['modifier', 'value', 'type']
    
    
    def __init__(self, modifier: str, value: Any):
        self.modifier = modifier
        self.value = value
        self.type = type(value).__name__
    
    
    def __str__(self):
        return (
            f"Search modifier '{self.modifier}' cannot be used on type "
            f"'{type(self.value).__name__}' "
            f"(type was extrapolated from value '{self.value}')"
        )



class UnknownFieldError(DgeqError):
    """Raised when an unknown field is used inside a `Filter` or in any
    command."""
    
    code = "UNKNOWN_FIELD"
    details = ['valid_fields', 'unknown']
    
    
    def __init__(self, model: Type[models.Model], unknown: str):
        include_hidden = getattr(settings, "DGEQ_INCLUDE_HIDDEN", False)
        
        self.model = model
        self.unknown = unknown
        self.valid_fields = [f.name for f in model._meta.get_fields(include_hidden=include_hidden)]
    
    
    def __str__(self):
        return (
            f"Unknown field '{self.unknown}' in table '{self.model.__name__}, valid fields are "
            f"{self.valid_fields}"
        )



class NotARelatedFieldError(DgeqError):
    """Raised when using a field that is not a related field."""
    
    code = "NOT_A_RELATED_FIELD"
    details = ['model_name', 'field', 'foreign_fields']
    
    
    def __init__(self, model: Union[Type[models.Model], models.Model], field: str):
        include_hidden = getattr(settings, "DGEQ_INCLUDE_HIDDEN", False)
        
        self.model = model
        self.model_name = model.__name__
        self.field = field
        self.foreign_fields = [
            f.name for f in model._meta.get_fields(include_hidden=include_hidden) if
            f.remote_field is not None
        ]
    
    
    def __str__(self):
        return (
            f"Field '{self.field}' in table '{self.model.__name__}, is neither a foreign key nor "
            f"a list of foreign key. Valid fields are {self.foreign_fields}"
        )



class FieldDepthError(DgeqError):
    """Raised if a field lookup exceed `MAX_FOREIGN_FIELD_DEPTH`."""
    
    code = "FIELD_DEPTH_ERROR"
    details = ['field', 'max_depth']
    
    
    def __init__(self, field: str):
        self.field = field
        self.max_depth = MAX_FOREIGN_FIELD_DEPTH
    
    
    def __str__(self):
        return (
            f"Field `{self.field}` exceed the allowed depth of related field of"
            f" {MAX_FOREIGN_FIELD_DEPTH}"
        )



class InvalidCommandError(DgeqError):
    """Raised when a commands is misused or its value is invalid."""
    
    code = "INVALID_VALUE_ERROR"
    details = ['command']
    
    
    def __init__(self, command: str, message: str):
        self.command = command
        self.message = message
    
    
    def __str__(self):
        return f"Invalid command `{self.command}`: {self.message}"
