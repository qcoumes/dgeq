"""Contains Type for typing and constants.

Constant prefixed with `DGEQ_` can be overridden in `settings.py`.
"""

from django.conf import settings


# Default max depth before a field lookup fail.
DGEQ_MAX_NESTED_FIELD_DEPTH = getattr(settings, "DGEQ_MAX_NESTED_FIELD_DEPTH", 10)

# Separators use in subquery for some commands (like `c:annotate` or `c:join`)
# `DGEQ_SUBQUERY_SEP_FIELDS` is used to separate field/value(s) pairs
# `DGEQ_SUBQUERY_SEP_VALUES` is used to separate values in a same field
DGEQ_SUBQUERY_SEP_FIELDS = getattr(settings, 'DGEQ_SUBQUERY_SEP_FIELDS', '|')
DGEQ_SUBQUERY_SEP_VALUES = getattr(settings, 'DGEQ_SUBQUERY_SEP_VALUES', "'")

# Default limit on row count when 'c:limit' is not provided (set to 0 to get
# every row)
DGEQ_DEFAULT_LIMIT = getattr(settings, "DGEQ_DEFAULT_LIMIT", 10)

# Maximum number of row returned in a response (set to '0' to allow any limit).
# InvalidCommandError will be raised if an higher number is given to 'c:limit'
DGEQ_MAX_LIMIT = getattr(settings, "DGEQ_MAX_LIMIT", 200)
