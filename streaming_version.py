from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator, Mapping, Sequence
from zipfile import ZipFile
from xml.etree.ElementTree import Element, iterparse

import duckdb


# ----------------------------
# XML helpers
# ----------------------------


def local(tag: str) -> str:
    """Strip default namespace: '{ns}t_object' -> 't_object'."""
    return tag.split("}", 1)[-1]


def children_map(elem: Element) -> dict[str, str]:
    """Direct children -> {local_tag: text stripped}."""
    out: dict[str, str] = {}
    for ch in list(elem):
        out[local(ch.tag)] = (ch.text or "").strip()
    return out


# ----------------------------
# Converters (tolerant)
# ----------------------------


def to_int0(s: str | None) -> int:
    if s is None:
        return 0
    s = s.strip()
    return int(s) if s else 0


def to_int_opt(s: str | None) -> int | None:
    if s is None:
        return None
    s = s.strip()
    return int(s) if s else None


def to_bool(s: str | None) -> bool:
    return (s or "").strip().lower() in {"true", "1", "yes", "y", "t"}


# ----------------------------
# Table spec + row streamer
# ----------------------------


@dataclass(frozen=True)
class TableSpec:
    row_tag: str
    columns: Sequence[str]
    converters: Mapping[str, Callable[[str | None], object]]


def stream_rows_from_zip(
    zip_path: Path,
    xml_member_name: str,
    specs: Sequence[TableSpec],
) -> Iterator[tuple[str, tuple[object, ...]]]:
    """
    One-pass streaming over XML inside ZIP.
    Yields: (table_tag, row_tuple)
    """
    spec_by_tag = {s.row_tag: s for s in specs}

    with ZipFile(zip_path) as zf:
        with zf.open(xml_member_name, "r") as f:
            for _, elem in iterparse(f, events=("end",)):
                tag = local(elem.tag)
                spec = spec_by_tag.get(tag)
                if spec is None:
                    continue

                m = children_map(elem)

                row: list[object] = []
                for col in spec.columns:
                    raw = m.get(col)  # None if missing
                    conv = spec.converters.get(col)
                    if conv is not None:
                        row.append(conv(raw))
                    else:
                        row.append(raw if raw is not None else None)

                yield tag, tuple(row)

                # keep memory low
                elem.clear()


# ----------------------------
# DuckDB loading (chunked executemany)
# ----------------------------


def ensure_schema_and_tables(con: duckdb.DuckDBPyConnection) -> None:
    # Ajusta schema si quieres; DuckDB no requiere schema, pero puede ayudar.
    con.execute("CREATE SCHEMA IF NOT EXISTS plexos;")

    con.execute("""
        CREATE TABLE IF NOT EXISTS plexos.t_object (
            class_id     INTEGER,
            name         VARCHAR,
            category_id  INTEGER,
            "index"      INTEGER,
            object_id    INTEGER,
            show         BOOLEAN,
            guid         UUID
        );
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS plexos.t_property (
            property_id       INTEGER,
            collection_id     INTEGER,
            enum_id           INTEGER,   -- nullable (None -> NULL)
            name              VARCHAR,
            summary_name      VARCHAR,
            unit_id           INTEGER,
            summary_unit_id   INTEGER,
            is_multi_band     BOOLEAN,
            is_period         BOOLEAN,
            is_summary        BOOLEAN,
            lang_id           INTEGER
        );
    """)


def insert_chunks_to_duckdb(
    con: duckdb.DuckDBPyConnection,
    row_iter: Iterator[tuple[str, tuple[object, ...]]],
    chunk_size: int = 10_000,
) -> None:
    """
    Buffers rows per table and loads with executemany in chunks.
    """
    buffers: dict[str, list[tuple[object, ...]]] = {
        "t_object": [],
        "t_property": [],
    }

    sql_by_table = {
        "t_object": """
            INSERT INTO plexos.t_object
            (class_id, name, category_id, "index", object_id, show, guid)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        "t_property": """
            INSERT INTO plexos.t_property
            (property_id, collection_id, enum_id, name, summary_name, unit_id,
             summary_unit_id, is_multi_band, is_period, is_summary, lang_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
    }

    def flush(table: str) -> None:
        buf = buffers[table]
        if not buf:
            return
        con.executemany(sql_by_table[table], buf)
        buf.clear()

    # Opcional: transacción grande para acelerar muchísimo
    con.execute("BEGIN;")
    try:
        for table, row in row_iter:
            if table not in buffers:
                continue

            buffers[table].append(row)

            if len(buffers[table]) >= chunk_size:
                flush(table)

        # flush final
        for t in list(buffers.keys()):
            flush(t)

        con.execute("COMMIT;")
    except Exception:
        con.execute("ROLLBACK;")
        raise


# ----------------------------
# Specs for your tables
# ----------------------------

T_OBJECT = TableSpec(
    row_tag="t_object",
    columns=("class_id", "name", "category_id", "index", "object_id", "show", "GUID"),
    converters={
        "class_id": to_int0,
        "name": lambda s: (s or ""),
        "category_id": to_int0,
        "index": to_int0,
        "object_id": to_int0,
        "show": to_bool,
        # DuckDB UUID: si viene vacío, mejor None
        "GUID": lambda s: (s.strip() if s and s.strip() else None),
    },
)

T_PROPERTY = TableSpec(
    row_tag="t_property",
    columns=(
        "property_id",
        "collection_id",
        "enum_id",  # optional => None
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
        "name": lambda s: (s or ""),
        "summary_name": lambda s: (s or ""),
        "unit_id": to_int0,
        "summary_unit_id": to_int0,
        "is_multi_band": to_bool,
        "is_period": to_bool,
        "is_summary": to_bool,
        "lang_id": to_int0,
    },
)


# ----------------------------
# End-to-end function
# ----------------------------


def load_plexos_solution_zip_to_duckdb(
    zip_path: Path,
    xml_member_name: str,
    duckdb_path: Path,
    chunk_size: int = 10_000,
) -> None:
    con = duckdb.connect(str(duckdb_path))
    try:
        ensure_schema_and_tables(con)

        rows = stream_rows_from_zip(
            zip_path=zip_path,
            xml_member_name=xml_member_name,
            specs=[T_OBJECT, T_PROPERTY],
        )

        insert_chunks_to_duckdb(con, rows, chunk_size=chunk_size)
    finally:
        con.close()


# ----------------------------
# Example usage
# ----------------------------

if __name__ == "__main__":
    load_plexos_solution_zip_to_duckdb(
        zip_path=Path("PLEXOS_Solution.zip"),
        xml_member_name="SolutionDataset.xml",  # ajusta al nombre real dentro del zip
        duckdb_path=Path("plexos.duckdb"),
        chunk_size=20_000,
    )
