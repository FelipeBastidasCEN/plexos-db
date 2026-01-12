"""DuckDB bulk loading optimizado.

Inserción masiva por chunks para performance con archivos grandes.
"""

import duckdb
from typing import Iterator, Tuple
from ..common.exceptions import DatabaseError


class DuckDBBulkLoader:
    """Bulk loader optimizado para DuckDB con chunks y prepared statements."""

    def __init__(self, connection: duckdb.DuckDBPyConnection, chunk_size: int = 100):
        """
        Inicializa bulk loader.

        Args:
            connection: Conexión DuckDB activa
            chunk_size: Tamaño de chunks para inserción (default: 50K)
        """
        self.connection = connection
        self.chunk_size = chunk_size
        self._buffers = {}
        self._prepared_statements = {}

    def insert_rows(self, row_iter: Iterator[Tuple[str, Tuple]]) -> None:
        """
        Inserta filas usando chunks y prepared statements.

        Args:
            row_iter: Iterator de (table_name, row_tuple)
        """
        # Transacción grande para performance
        self.connection.execute("BEGIN;")
        try:
            for table_name, row_tuple in row_iter:
                print(table_name, row_tuple)
                if table_name not in self._buffers:
                    self._prepare_table(table_name)

                self._buffers[table_name].append(row_tuple)

                if len(self._buffers[table_name]) >= self.chunk_size:
                    self._flush_table(table_name)

            # Flush final de todas las tablas
            for table_name in list(self._buffers.keys()):
                self._flush_table(table_name)

            self.connection.execute("COMMIT;")

        except Exception:
            self.connection.execute("ROLLBACK;")
            raise DatabaseError("Error durante inserción masiva")

    def _prepare_table(self, table_name: str) -> None:
        """
        Prepara statement y buffer para una tabla.

        Args:
            table_name: Nombre de la tabla
        """
        # Generar INSERT SQL dinámicamente
        # Necesitamos saber las columnas desde el registry
        from ..schemas.schema_registry import SchemaRegistry

        spec = SchemaRegistry.get_spec(table_name)

        placeholders = ", ".join(["?"] * len(spec.columns))
        sql = f"""
            INSERT INTO plexos.{spec.table_name}
            ({
            ", ".join(
                [f'"{col}"' if col.lower() == "index" else col for col in spec.columns]
            )
        })
            VALUES ({placeholders})
        """

        self._prepared_statements[table_name] = self.connection.prepare(sql)
        self._buffers[table_name] = []

    def _flush_table(self, table_name: str) -> None:
        """
        Inserta buffer de una tabla y lo limpia.

        Args:
            table_name: Nombre de la tabla
        """
        buffer = self._buffers[table_name]
        if not buffer:
            return

        statement = self._prepared_statements[table_name]
        statement.executemany(buffer)
        buffer.clear()

    def get_stats(self) -> dict[str, int]:
        """
        Obtiene estadísticas de inserción.

        Returns:
            Diccionario con estadísticas por tabla
        """
        return {table_name: len(buffer) for table_name, buffer in self._buffers.items()}

    def reset_buffers(self) -> None:
        """Limpia todos los buffers."""
        for buffer in self._buffers.values():
            buffer.clear()
