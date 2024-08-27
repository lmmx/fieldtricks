"""A simple proof of concept razor, deprecated for generic handling version."""

from typing import TypeVar

from pydantic import BaseModel, create_model
from pydantic.fields import Field, FieldInfo

__all__ = ("extract_bare_fields", "prune_model_type")

T = TypeVar("T", bound=BaseModel)


def extract_bare_fields(fields: dict[str, FieldInfo]) -> dict[str, tuple[type, Field]]:
    """Removes the Routing 'wrapper' on the field annotations (removing validation)."""
    return {
        name: (info.annotation, Field(required=info.is_required))
        for name, info in fields.items()
    }


def prune_model_type(model: BaseModel, prefix="") -> BaseModel:
    fields = {name: info for name, info in model.model_fields.items()}
    return create_model(
        f"{prefix}{model.__name__}",
        **extract_bare_fields(fields),
    )
