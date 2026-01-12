"""Import service principal.

Servicio de orquestación principal para importación PLEXOS.
Coordina XML processor + storage layer con error handling.
"""

from pathlib import Path
from typing import Optional

from ...model.storage.connection import DuckDBConnection
from ...model.storage.schema_manager import DuckDBSchemaManager
from ...model.storage.bulk_loader import DuckDBBulkLoader
from ...model.schemas.schema_registry import SchemaRegistry
from ..processors.xml_processor import XMLProcessor
from ..processors.validators import FileValidator
from ...model.common.exceptions import DatabaseError, ConfigurationError


class ImportService:
    """Servicio principal de importación PLEXOS."""

    def __init__(self, schema_registry: Optional[SchemaRegistry] = None):
        """
        Inicializa servicio de importación.

        Args:
            schema_registry: Registry de schemas (usa default si None)
        """
        self.schema_registry = schema_registry or SchemaRegistry()
        self.xml_processor = XMLProcessor(self.schema_registry)

    def import_plexos_data(
        self,
        zip_path: Path,
        db_path: Path,
        xml_name: str = "Model PRGdia_Full_Definitivo Solution.xml",
        chunk_size: int = 100,
        overwrite: bool = True,
    ) -> dict:
        """
        Importa datos PLEXOS desde ZIP a DuckDB.

        Args:
            zip_path: Ruta al archivo ZIP PLEXOS
            db_path: Ruta a la base de datos DuckDB
            xml_name: Nombre del archivo XML dentro del ZIP
            chunk_size: Tamaño de chunks para procesamiento
            overwrite: Si sobreescribir base de datos existente

        Returns:
            Diccionario con estadísticas de importación

        Raises:
            ValueError: Error en validación de archivos
            DatabaseError: Error en operaciones de base de datos
            ConfigurationError: Error en configuración
        """
        # Validación de inputs
        self._validate_inputs(zip_path, db_path, xml_name, chunk_size)

        # Conexión a base de datos
        with DuckDBConnection(db_path, read_only=False) as conn:
            try:
                # Crear schemas y tablas
                schema_manager = DuckDBSchemaManager(conn)
                all_specs = self.schema_registry.get_all_specs()
                schema_manager.create_all_tables(all_specs)

                # Procesar XML e insertar datos
                bulk_loader = DuckDBBulkLoader(conn, chunk_size)

                row_iter = self.xml_processor.stream_from_zip(zip_path, xml_name)
                bulk_loader.insert_rows(row_iter)

                # Obtener estadísticas
                stats = self.xml_processor._stats.get_stats()
                bulk_stats = bulk_loader.get_stats()

                return {
                    "import_stats": stats,
                    "bulk_stats": bulk_stats,
                    "success": True,
                }

            except Exception as e:
                if isinstance(e, (DatabaseError, ConfigurationError)):
                    raise
                raise DatabaseError(f"Error durante importación: {e}")

    def _validate_inputs(
        self, zip_path: Path, db_path: Path, xml_name: str, chunk_size: int
    ) -> None:
        """
        Valida todos los inputs de importación.

        Args:
            zip_path: Ruta al ZIP
            db_path: Ruta a la base de datos
            xml_name: Nombre del XML
            chunk_size: Tamaño de chunk

        Raises:
            ValueError: Si algún input es inválido
            ConfigurationError: Si la configuración es inválida
        """
        # Validación de archivos
        FileValidator.validate_zip_path(zip_path)
        FileValidator.validate_db_path(db_path)
        FileValidator.validate_xml_name(xml_name)

        # Validación de configuración
        if chunk_size <= 0:
            raise ConfigurationError(f"chunk_size debe ser > 0, recibido: {chunk_size}")

        if chunk_size > 1_000_000:
            raise ConfigurationError(
                f"chunk_size muy grande (>1M), recibido: {chunk_size}"
            )

    def get_supported_tables(self) -> list[str]:
        """
        Retorna lista de tablas soportadas.

        Returns:
            Lista de nombres de tablas soportadas
        """
        return self.schema_registry.get_all_table_names()

    def is_table_supported(self, table_name: str) -> bool:
        """
        Verifica si una tabla es soportada.

        Args:
            table_name: Nombre de la tabla

        Returns:
            True si la tabla es soportada
        """
        return self.schema_registry.is_supported(table_name)
