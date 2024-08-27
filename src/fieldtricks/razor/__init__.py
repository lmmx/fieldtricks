"""The razor prunes away unused model field metadata and validators.

It does this recursively, including looking inside generics.
"""

from .generic import prune_model_type

__all__ = ("prune_model_type",)
