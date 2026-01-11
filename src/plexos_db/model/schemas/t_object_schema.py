"""TableSpec para t_object.

Especificación de procesamiento para tabla t_object basada en streaming_version.py.
"""

from .base import TableSpec
from ..common.converters import to_int0, to_str, clean_uuid


T_OBJECT_SPEC = TableSpec(
    row_tag="t_object",
    columns=(
        "class_id", 
        "name", 
        "category_id", 
        "index", 
        "object_id", 
        "show", 
        "guid"
    ),
    converters={
        "class_id": to_int0,
        "name": to_str,
        "category_id": to_int0,
        "index": to_int0,
        "object_id": to_int0,
        "show": lambda s: (s or "").strip().lower() in {"true", "1", "yes", "y", "t"},
        "guid": clean_uuid,  # None si está vacío
    }
)