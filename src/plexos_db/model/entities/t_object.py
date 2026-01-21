"""TObject entity unificada.

Entity con metadata integrada que reemplaza TableSpec + dataclass separados.
"""

from dataclasses import dataclass
from typing import ClassVar, Optional, NamedTuple, Self
from xml.etree.ElementTree import Element

import pyarrow as pa

from .base_entity import BaseEntity, BooleanField, IntegerField, StringField, UUIDField


@dataclass(frozen=True, slots=True)
class TObject(BaseEntity):
    """Entity para tabla t_object de PLEXOS con metadata integrada."""

    # --- Campos de datos (tipos para IDE/mypy) ---
    class_id: int
    name: str
    category_id: int
    index: int
    object_id: int
    show: bool
    guid: Optional[str] = None

    # --- Metadata ClassVars ---
    row_tag: ClassVar[str] = "t_object"

    # ClassVar para fields metadata (requerido por BaseEntity)
    fields: ClassVar[dict] = {
        "class_id": IntegerField(required=True),
        "name": StringField(required=True),
        "category_id": IntegerField(required=True),
        "index": IntegerField(required=True, column_name="index"),
        "object_id": IntegerField(required=True),
        "show": BooleanField(required=True),
        "guid": UUIDField(required=False),
    }

    # --- Métodos específicos de TObject ---

    def __str__(self) -> str:
        """Representación legible."""
        return f"TObject(id={self.object_id}, class_id={self.class_id}, name='{self.name}')"

    @property
    def is_enabled(self) -> bool:
        """Verifica si el objeto está habilitado."""
        return self.show

    def get_identifier(self) -> str:
        """Retorna identificador único."""
        if self.guid:
            return self.guid
        return f"{self.class_id}:{self.object_id}"


class TObject2(NamedTuple):
    class_id: int
    name: str
    category_id: int
    index: int
    object_id: int
    show: bool
    guid: str | None = None

    @classmethod
    def from_element(cls, elem: Element) -> Self:
        return cls(
            class_id=int(elem.findtext("{*}class_id")),
            name=elem.findtext("{*}name"),
            category_id=int(elem.findtext("{*}category_id")),
            index=int(elem.findtext("{*}index")),
            object_id=int(elem.findtext("{*}object_id")),
            show=True if elem.findtext("{*}show") == "true" else False,
            guid=elem.findtext("{*}GUID"),
        )

    def schema(self) -> pa.schema:
        return pa.schema(
            [
                pa.field("class_id", pa.int64()),
                pa.field("name", pa.string()),
                pa.field("category_id", pa.int64()),
                pa.field("index", pa.int64()),
                pa.field("object_id", pa.int64()),
                pa.field("show", pa.bool_()),
                pa.field("guid", pa.string()),
            ]
        )

    @property
    def table_name(self) -> str:
        return "t_object"
