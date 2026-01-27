"""DuckDB schema management.

Creación dinámica de tablas desde Entities unificadas para PLEXOS.
"""

from typing import Type

import duckdb

from ..common.exceptions import DatabaseError
from ..entities.base_entity import BaseEntity
from ..entities.table_register import TableRegister


class DuckDBSchemaManager:
    """Manejador de schemas DuckDB con generación dinámica desde Entities."""

    def __init__(
        self, connection: duckdb.DuckDBPyConnection, table_registry: TableRegister
    ):
        """
        Inicializa manager de schemas.

        Args:
            connection: Conexión DuckDB activa
            schema_name: Nombre del schema (default: "plexos")
        """
        self.connection = connection
        self.table_registry = table_registry

    def _create_plexos_schema(self) -> None:
        """Crea schema plexos si no existe."""
        try:
            self.connection.execute(
                f"CREATE SCHEMA IF NOT EXISTS {self.table_registry.schema_name};"
            )
        except Exception as e:
            raise DatabaseError(
                f"No se puede crear schema {self.table_registry.schema_name}: {e}"
            )

    def create_table_from_entity(self, entity_class: Type[BaseEntity]) -> None:
        """
        Crea tabla DuckDB desde Entity.

        Args:
            entity_class: Clase Entity con metadata
        """
        table_sql = entity_class.get_table_sql(self.schema_name)

        try:
            self.connection.execute(table_sql)
        except Exception as e:
            raise DatabaseError(f"No se puede crear tabla {entity_class.row_tag}: {e}")

    def create_all_tables(self, entities: dict[str, Type[BaseEntity]]) -> None:
        """
        Crea todas las tablas desde registry de entities.

        Args:
            entities: Diccionario de Entity classes
        """
        for entity_class in entities.values():
            self.create_table_from_entity(entity_class)

    def create_all_supported_tables(self) -> None:
        """
        Crea todas las tablas soportadas usando EntityRegistry.
        """
        entities = EntityRegistry.get_all_entities()
        self._create_plexos_schema()
        tables = self.table_registry.SUPPORTED_TABLES
        self.create_all_tables(entities)
