from dataclasses import dataclass
from pathlib import Path
import duckdb
import pyarrow as pa

from plexos_db.model.ddb import t_object


def _create_schema(conn: duckdb.DuckDBPyConnection) -> None:
    sql: str = "CREATE OR REPLACE SCHEMA plexos_solution;"
    conn.execute(sql)


@dataclass
class ApiDuckDB:
    db_name: str
    db_path: Path
    conn: duckdb.DuckDBPyConnection | None = None

    def connect(self) -> None:
        path: Path = self.db_path / self.db_name
        path.unlink(missing_ok=True)
        self.conn = duckdb.connect(path)

    def close(self) -> None:
        self.conn.close()

    def create_db(self) -> int:
        _create_schema(self.conn)
        self.conn.execute(t_object.create_table())

        return 0

    def t_object(self, data: list[t_object.TObject]) -> None:
        """
        Legacy method - converts list of TObject to Arrow then inserts.
        Consider using t_object_arrow() for better performance.
        """
        t_object.insert_data(self.conn, data)

    def t_object_arrow(self, arrow_table: pa.Table) -> None:
        """
        Insert Arrow table directly to DuckDB without conversion.

        Args:
            arrow_table: Arrow table with t_object data
        """
        t_object.insert_arrow_data(self.conn, arrow_table)
