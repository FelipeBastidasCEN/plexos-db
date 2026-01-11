from dataclasses import asdict

import duckdb as ddb
import pyarrow as pa

from plexos_db.model.plexos.t_object import TObject


def create_table() -> str:
    return """
        CREATE OR REPLACE TABLE plexos_solution.t_object (
            object_id INT,
            class_id INT,
            name VARCHAR,
            category_id INT,
            description VARCHAR,
            guid VARCHAR
        )
    """


def insert_data(conn: ddb.DuckDBPyConnection, data: list[TObject]) -> int:
    """
    Legacy method - converts list of TObject to Arrow then inserts.
    Consider using insert_arrow_data() for better performance.
    """
    table = pa.Table.from_pylist([asdict(d) for d in data])
    conn.from_arrow(table).create("t_object")
    return 0


def insert_arrow_data(conn: ddb.DuckDBPyConnection, arrow_table: pa.Table) -> int:
    """
    Insert Arrow table directly to DuckDB without conversion.
    
    Args:
        conn: DuckDB connection
        arrow_table: Arrow table with t_object data
        
    Returns:
        0 on success
    """
    conn.from_arrow(arrow_table).create("t_object")
    return 0
