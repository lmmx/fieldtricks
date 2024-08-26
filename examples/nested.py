import json
from pathlib import Path
from typing import TypeVar

from fieldrouter import Routing, RoutingModel
from inline_snapshot import snapshot
from pydantic import BaseModel, Field, create_model
from pydantic.fields import FieldInfo

__all__ = ("NestedModel",)

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


class NestedModel(RoutingModel):
    field_1: Routing(str, "a.aa.aaa.0")
    field_2: Routing(str, "a.aa.aaa.1")
    field_3: Routing(int, "b.bb.2")


def check():
    json_str = '{"a":{"aa":{"aaa":["value_1","value_2"]}},"b":{"bb":[3,4,5]}}'
    result = NestedModel.model_validate_json(json_str)

    result_dict = result.model_dump()
    print(result_dict)

    assert result_dict == snapshot(
        {"field_1": "value_1", "field_2": "value_2", "field_3": 5},
    )

    model = NestedModel
    json_schema = json.dumps(model.model_json_schema(), indent=2)
    schema_dir = Path(__file__).parent / "schemas"
    schema_dir.mkdir(exist_ok=True)
    (schema_dir / f"{model.__name__}.json").write_text(json_schema)

    bare_model = prune_model_type(model)
    reparsed = bare_model.model_validate(result_dict)
    assert reparsed.model_dump() == result_dict


check()
