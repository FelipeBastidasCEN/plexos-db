"""TObject entity unificada.

Entity con metadata integrada que reemplaza TableSpec + dataclass separados.
"""

from typing import NamedTuple, Self
from xml.etree.ElementTree import Element

import pyarrow as pa


class TObject(NamedTuple):
    _table_name: str = "t_object"
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
                pa.field("class_id", pa.int64(), nullable=False),
                pa.field("name", pa.string(), nullable=False),
                pa.field("category_id", pa.int64(), nullable=False),
                pa.field("index", pa.int64(), nullable=False),
                pa.field("object_id", pa.int64(), nullable=False),
                pa.field("show", pa.bool_(), nullable=False),
                pa.field("guid", pa.string(), nullable=False),
            ]
        )

    @property
    def table_name(self) -> str:
        return self._table_name

    def create_table(self, schema_name: str) -> str:
        return f"""
            CREATE OR REPLACE TABLE {schema_name}.t_object(
                class_id INT NOT NULL,
                name VARCHAR NOT NULL,
                category_id INT NOT NULL,
                "index" INT NOT NULL,
                object_id INT NOT NULL,
                "show" BOOL NOT NULL,
                guid VARCHAR
            );
        """
