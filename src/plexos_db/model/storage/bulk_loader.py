"""DuckDB bulk loading optimizado.

Inserción masiva por chunks para performance con archivos grandes.
"""

from typing import Iterator, Tuple

import duckdb

from ..common.exceptions import DatabaseError
from ..entities.entity_registry import EntityRegistry


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
        # Obtener entity class desde registry
        entity_class = EntityRegistry.get_entity_class(table_name)
        columns = entity_class.get_columns()

        # Generar INSERT SQL dinámicamente
        placeholders = ", ".join(["?"] * len(columns))

        # Handle reserved keywords en column names
        formatted_columns = []
        for col in columns:
            if col.lower() in ("index", "show"):
                formatted_columns.append(f'"{col}"')
            else:
                formatted_columns.append(col)

        table_db_name = table_name  # Remover 't_' prefix para DB
        sql = f"""
            INSERT INTO plexos.{table_db_name}
            ({", ".join(formatted_columns)})
            VALUES ({placeholders})
        """

        # Usar execute con parameters en lugar de prepare (DuckDB no tiene prepare)
        self._prepared_statements[table_name] = sql
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

        sql = self._prepared_statements[table_name]
        self.connection.executemany(sql, buffer)
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
