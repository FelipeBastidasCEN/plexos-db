from dataclasses import dataclass
from pathlib import Path
import duckdb

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
        t_object.insert_data(self.conn, data)
