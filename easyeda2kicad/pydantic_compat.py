from pydantic import BaseModel, validator


def field_validator(*fields, mode="after", **kwargs):
    pre = mode == "before"
    return validator(*fields, pre=pre, allow_reuse=True, **kwargs)

