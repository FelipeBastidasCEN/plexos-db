from pathlib import Path
from xml.etree.ElementTree import iterparse, Element
from time import perf_counter
from types import UnionType
from typing import (
    NamedTuple,
    Self,
    get_type_hints,
    Any,
    get_args,
)
from collections.abc import Iterator
from dataclasses import dataclass, asdict, fields
from datetime import datetime

import duckdb
import pyarrow as pa


def process_value(name: str, elem: Element, row_type: Any) -> Any:
    text: str | None = elem.findtext(f"{{*}}{name}")
    # optional: bool = False

    # Manejo de tipo opcional se extrae el tipo que no es None.
    # Esta función solo funciona para tipo opcional, digase "Type[T] | None"
    # if type(row_type) is UnionType:
    # optional = True
    # row_type = [t for t in get_args(row_type) if t is not type(None)][0]

    # Verificador de que vienen todos los valores que se necesitan
    # if text is None and optional is False:
    #     raise ValueError(f"falta campo: {name} y no es opcional.")

    if row_type is str:
        return text
    elif row_type is int:
        return int(text)
    elif row_type is float:
        return float(text)
    elif row_type is bool:
        return text.strip().lower() == "true"
    elif row_type is datetime:
        return datetime.strptime(text, "%Y-%m-%d %H:%M")
    else:
        return str(text)


@dataclass(frozen=True, slots=True)
class BaseTable:
    @classmethod
    def from_element(cls, elem: Element) -> Self:
        table_types = get_type_hints(cls)
        data = {
            fd.name: process_value(fd.name, elem, table_types[fd.name])
            for fd in fields(cls)
        }
        return cls(**data)


# @dataclass(frozen=True, slots=True)
class TObject(NamedTuple):
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


# @dataclass(frozen=True, slots=True)
class TKey(NamedTuple):
    key_id: int
    membership_id: int
    phase_id: int
    property_id: int
    period_type_id: int

    @classmethod
    def from_element(cls, element: Element) -> Self:
        return cls(
            key_id=int(element.findtext("{*}key_id")),
            membership_id=int(element.findtext("{*}membership_id")),
            phase_id=int(element.findtext("{*}phase_id")),
            property_id=int(element.findtext("{*}property_id")),
            period_type_id=int(element.findtext("{*}period_type_id")),
        )

    def schema(self) -> pa.schema:
        return pa.schema(
            [
                pa.field("key_id", pa.int64()),
                pa.field("membership_id", pa.int64()),
                pa.field("phase_id", pa.int64()),
                pa.field("property_id", pa.int64()),
                pa.field("period_type_id", pa.int64()),
            ]
        )

    @property
    def table_name(self) -> str:
        return "t_key"


PlexosTable = TObject | TKey


class TableRegister:
    SUPPORTED_ENTITIES: dict[str, NamedTuple] = {
        "t_object": TObject,
        "t_key": TKey,
    }

    @classmethod
    def get_table(cls, table_name: str) -> NamedTuple:
        if not cls.is_supported(table_name):
            return None
        return cls.SUPPORTED_ENTITIES[table_name]

    @classmethod
    def is_supported(cls, table_name: str) -> bool:
        return table_name in cls.SUPPORTED_ENTITIES.keys()


def strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1]


def stream_xml(xml_path: Path) -> Iterator[PlexosTable]:
    with xml_path.open("rb") as f:
        for _, elem in iterparse(f, events=("end",)):
            tag = strip_namespace(elem.tag)
            if not TableRegister.is_supported(tag):
                continue
            table = TableRegister.get_table(tag)
            row = table.from_element(elem)
            yield row
            elem.clear()


def flush(buf, pa_schema, conn, schema_name, table_name) -> None:
    if len(buf) < 1:
        return None
    print(f"buffer_size: {len(buf)} - table_name: {table_name}")
    record = pa.RecordBatch.from_pylist(buf, schema=pa_schema)
    conn.from_arrow(record).insert_into(f"{schema_name}.{table_name}")
    return None


def insert_rows(
    conn: duckdb.DuckDBPyConnection,
    schema_name: str,
    buf_size: int,
    row_iter: Iterator[PlexosTable],
) -> int:
    buffer = []
    count = 0
    current_table: PlexosTable | None = None
    for table_row in row_iter:
        # caso inicial
        if current_table is None:
            current_table = table_row
        if table_row.table_name != current_table.table_name:
            flush(
                buffer,
                current_table.schema(),
                conn,
                schema_name,
                current_table.table_name,
            )
            buffer.clear()
            current_table = table_row
        count += 1
        buffer.append(table_row._asdict())
        if len(buffer) >= buf_size:
            flush(
                buffer,
                current_table.schema(),
                conn,
                schema_name,
                current_table.table_name,
            )
            buffer.clear()
    if len(buffer) > 1:
        flush(
            buffer, current_table.schema(), conn, schema_name, current_table.table_name
        )
        buffer.clear()
    conn.close()
    return count


def main():
    zip_path = Path(
        r"C:\Users\felipe.bastidas\test\PCP\20251011\Datos\Model PRGdia_Full_Definitivo Solution\Model PRGdia_Full_Definitivo Solution\Model PRGdia_Full_Definitivo Solution.xml"
    )
    start = perf_counter()
    db_path = Path("pcp.ddb")
    db_path.unlink(missing_ok=True)
    db = duckdb.connect(db_path)
    schema_name: str = "plexos_solution"
    db.execute(f"CREATE OR REPLACE SCHEMA {schema_name};")
    db.execute(
        f"""CREATE OR REPLACE TABLE {schema_name}.t_object(class_id INT, name VARCHAR, category_id INT, "index" INT, object_id INT, "show" BOOL, guid VARCHAR);"""
    )
    db.execute(
        f"""CREATE OR REPLACE TABLE {schema_name}.t_key(key_id INT,membership_id INT, phase_id INT, property_id INT, period_type_id INT);"""
    )
    row_iter = stream_xml(zip_path)
    buffer_max_size: int = 5000
    count = insert_rows(db, schema_name, buffer_max_size, row_iter)

    end = perf_counter()
    print(f"procesados: {count}")
    print(f"total_time: {end - start:.1f} seg")


if __name__ == "__main__":
    main()
