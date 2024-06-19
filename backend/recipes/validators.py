from django.core.exceptions import ValidationError

from .constants import ERROR_ZERO_MESSAGE


def validate_forbidden_zero(value):
    if value == 0:
        raise ValidationError(ERROR_ZERO_MESSAGE)
    return value
