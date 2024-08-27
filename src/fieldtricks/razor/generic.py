"""Able to handle generics (including generic aliases like `list[...]`/`dict[...]`)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import GenericAlias, Literal, get_args, get_origin

from inline_snapshot import snapshot
from pydantic import BaseModel, create_model, model_validator
from pydantic.fields import Field, FieldInfo

__all__ = (
    "MascotInfo",
    "MascotMetrics",
    "MascotExtra",
    "MascotMisc",
    "QueryResult",
)


def is_subclass_safe(cls: type, base: type) -> bool:
    """Safely check if cls is a subclass of base, even if cls is a GenericAlias."""
    # If cls is a generic alias (e.g., list[SomeType])
    origin = get_origin(cls)
    if origin is None:
        # Check if cls is a subclass of base
        return isinstance(cls, type) and issubclass(cls, base)
    else:
        # Extract the type inside the generic and check if it's a subclass
        return any(is_subclass_safe(arg, base) for arg in get_args(cls))


def resolve_generic_arg(annotation: GenericAlias, prefix: str) -> GenericAlias:
    origin = get_origin(annotation)
    args = get_args(annotation)
    # Recursively replace BaseModel subclasses in the args
    resolved_args = tuple(
        prune_model_type(arg)
        if is_subclass_safe(arg, BaseModel)
        else (resolve_generic_arg(arg) if get_origin(arg) is not None else arg)
        for arg in args
    )
    # Reconstruct the generic alias with the resolved arguments
    return origin[resolved_args]


def extract_bare_fields(
    fields: dict[str, FieldInfo],
    model_name_prefix: str,
) -> dict[str, tuple[type, Field]]:
    """Removes the Routing 'wrapper' on the field annotations (removing validation)."""
    model_types = {
        name: (
            (
                prune_model_type(info.annotation, prefix=model_name_prefix)
                if is_subclass_safe(info.annotation, BaseModel)
                else info.annotation
            )
            if get_origin(info.annotation) is None
            else resolve_generic_arg(info.annotation, prefix=model_name_prefix)
        )
        for name, info in fields.items()
        if is_subclass_safe(info.annotation, BaseModel)
    }
    result = {
        name: (
            (model_types[name] if name in model_types else info.annotation),
            Field(required=info.is_required),
        )
        for name, info in fields.items()
    }
    return result


def prune_model_type(model: BaseModel, prefix="Bare") -> BaseModel:
    fields = {name: info for name, info in model.model_fields.items()}
    return create_model(
        f"{prefix}{model.__name__}",
        **extract_bare_fields(fields, model_name_prefix=prefix),
    )


class MascotInfo(BaseModel):
    """The main info fields of the result."""

    id: str = Field(alias="character")
    name: str = Field(alias="title")
    fans: int = Field(alias="followers")
    years_old: int = Field(alias="age")
    link: str = Field(alias="homepage_url")
    bio: str


class MascotExtra(BaseModel):
    type: Literal["mascot"] = "mascot"
    metrics: MascotMetrics
    misc: MascotMisc
    friends: dict[int, str] = Field(alias="top_8")

    @model_validator(mode="before")
    def pop_subfields_out(cls, v: dict):
        v.setdefault("metrics", v)
        v.setdefault("misc", v)
        return v


class MascotMetrics(BaseModel):
    awards: int
    medals: int


class MascotMisc(BaseModel):
    hobby: str
    chaotic: bool


class ItemResult(BaseModel):
    id: str
    title: str
    count: int
    date: str  # datetime ISO format


class ThemeTuneResult(ItemResult):
    type: Literal["theme_tune"]


class PhotoShootResult(ItemResult):
    type: Literal["photoshoot"]


class QueryResult(MascotInfo):
    timestamp: str
    theme_tunes: list[ThemeTuneResult]
    photoshoots: list[PhotoShootResult]
    metadata: MascotExtra

    @model_validator(mode="before")
    def pop_subfield_out(cls, v: dict):
        v.setdefault("metadata", v)
        return v


def get_chiitan_info() -> dict:
    """An imaginary API that gives info about Chiitan, the Japanese mascots."""
    return {
        "character": "chiitan",
        "title": "Chiitan☆",
        "followers": 1_000_000,
        "age": 0,
        "homepage_url": "https://chiitan.love/",
        "bio": "Chiitan☆ is a fairy baby otter that wears a turtle as a hat.",
        "timestamp": "2024-08-25T14:36:52.123456",
        "theme_tunes": [
            {
                "type": "theme_tune",
                "id": "chiitan-dance",
                "title": "Chiitan☆ Dance",
                "count": 1200,
                "date": "2022-04-15T10:00:00Z",
            },
        ],
        "photoshoots": [
            {
                "type": "photoshoot",
                "id": "archery",
                "title": "Chiitan☆ Archery Practice",
                "count": 50,
                "date": "2023-07-05T12:00:00Z",
            },
        ],
        "hobby": "extreme sports",
        "chaotic": True,
        "awards": 100,
        "medals": 300,
        "top_8": {
            "1": "Funassyi",
            "2": "Kumamon",
            "3": "Hikonyan",
            "4": "Rilakkuma",
            "5": "Domo-kun",
            "6": "Gudetama",
            "7": "Nyango Star",
            "8": "Korilakkuma",
        },
    }


def check():
    data = get_chiitan_info()
    result = QueryResult.model_validate(data)

    result_dict = result.model_dump()
    print(result_dict)

    assert result_dict == snapshot(
        {
            "id": "chiitan",
            "name": "Chiitan☆",
            "fans": 1000000,
            "years_old": 0,
            "link": "https://chiitan.love/",
            "bio": "Chiitan☆ is a fairy baby otter that wears a turtle as a hat.",
            "timestamp": "2024-08-25T14:36:52.123456",
            "theme_tunes": [
                {
                    "id": "chiitan-dance",
                    "title": "Chiitan☆ Dance",
                    "count": 1200,
                    "date": "2022-04-15T10:00:00Z",
                    "type": "theme_tune",
                },
            ],
            "photoshoots": [
                {
                    "id": "archery",
                    "title": "Chiitan☆ Archery Practice",
                    "count": 50,
                    "date": "2023-07-05T12:00:00Z",
                    "type": "photoshoot",
                },
            ],
            "metadata": {
                "type": "mascot",
                "metrics": {"awards": 100, "medals": 300},
                "misc": {"hobby": "extreme sports", "chaotic": True},
                "friends": {
                    1: "Funassyi",
                    2: "Kumamon",
                    3: "Hikonyan",
                    4: "Rilakkuma",
                    5: "Domo-kun",
                    6: "Gudetama",
                    7: "Nyango Star",
                    8: "Korilakkuma",
                },
            },
        },
    )
    model = QueryResult
    json_schema = json.dumps(model.model_json_schema(), indent=2)
    schema_dir = Path(__file__).parent / "schemas"
    schema_dir.mkdir(exist_ok=True)
    (schema_dir / f"{model.__name__}.json").write_text(json_schema)

    bare_model = prune_model_type(model)
    reparsed = bare_model.model_validate(result_dict)
    assert reparsed.model_dump() == result_dict


check()
