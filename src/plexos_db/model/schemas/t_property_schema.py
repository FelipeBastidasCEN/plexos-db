"""TableSpec para t_property.

Especificación de procesamiento optimizada para tabla t_property.
"""

from .base import TableSpec
from ..common.converters import to_int0, to_int_opt, to_str, to_bool


T_PROPERTY_SPEC = TableSpec(
    row_tag="t_property",
    columns=(
        "property_id",
        "collection_id",
        "enum_id",  # nullable (None -> NULL)
        "name",
        "summary_name",
        "unit_id",
        "summary_unit_id",
        "is_multi_band",
        "is_period",
        "is_summary",
        "lang_id",
    ),
    converters={
        "property_id": to_int0,
        "collection_id": to_int0,
        "enum_id": to_int_opt,  # key point (missing -> NULL)
        "name": to_str,
        "summary_name": to_str,
        "unit_id": to_int0,
        "summary_unit_id": to_int0,
        "is_multi_band": to_bool,
        "is_period": to_bool,
        "is_summary": to_bool,
        "lang_id": to_int0,
    }
)