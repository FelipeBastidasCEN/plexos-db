"""TableSpec para t_object.

Especificación de procesamiento optimizada para tabla t_object.
"""

from .base import TableSpec


T_OBJECT_SPEC = TableSpec(
    row_tag="t_object",
    columns=(
        "class_id",
        "name",
        "category_id",
        "index",
        "object_id",
        "show",
        "GUID",
    ),
    converters={
        "class_id": int,
        "name": str,
        "category_id": int,
        "index": int,
        "object_id": int,
        "show": lambda s: (s or "").strip().lower()
        in {"true", "true", "1", "yes", "y", "t"},
        "GUID": str,  # None si está vacío
    },
)
