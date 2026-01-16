"""XML streaming processor optimizado.

Procesamiento streaming de XML PLEXOS con performance para archivos grandes.
Arquitectura optimizada para 100MB XML.
"""

from pathlib import Path
from typing import Iterator, Tuple
from zipfile import ZipFile
from xml.etree.ElementTree import iterparse

from ...model.common.xml_utils import strip_namespace, extract_children_text
from ...model.schemas.schema_registry import SchemaRegistry
from ...model.common.exceptions import MissingColumnError
from ...common.logging_config import get_logger


class XMLProcessor:
    """Streaming XML processor optimizado para archivos grandes."""

    def __init__(self, schema_registry: SchemaRegistry):
        """
        Inicializa processor con registry de schemas.

        Args:
            schema_registry: Registry de TableSpecs validado
        """
        self.schema_registry = schema_registry
        self._stats = ProcessingStats()
        self.logger = get_logger("business.processors")

    def stream_from_zip(
        self, zip_path: Path, xml_name: str
    ) -> Iterator[Tuple[str, Tuple]]:
        """
        Stream procesamiento de XML dentro de ZIP.

        Args:
            zip_path: Ruta al archivo ZIP
            xml_name: Nombre del archivo XML dentro del ZIP

        Yields:
            Tuplas de (table_name, row_tuple)
        """
        self.logger.info(f"Iniciando streaming de ZIP: {zip_path.name}, XML: {xml_name}")
        specs = self.schema_registry.get_all_specs()

        with ZipFile(zip_path) as zf:
            with zf.open(xml_name, "r") as f:
                for _, elem in iterparse(f, events=("end",)):
                    tag = strip_namespace(elem.tag)

                    # Comportamiento 1: Ignorar tablas desconocidas con warning
                    if tag not in specs:
                        self.logger.warning(f"Ignorando tabla desconocida: {tag}")
                        continue

                    spec = specs[tag]
                    self.logger.debug(f"Procesando elemento: {tag}")

                    try:
                        # Extracción ultra-rápida de datos
                        row_data = extract_children_text(elem)
                        self.logger.debug(f"Extraídos {len(row_data)} campos para {tag}")

                        # Validación de columnas requeridas
                        # spec.validate_row_data(row_data)

                        # Conversión a tupla usando TableSpec
                        row_tuple = spec.convert_row(row_data)

                        yield tag, row_tuple
                        self._stats.processed_row(tag)

                    except MissingColumnError as e:
                        # Comportamiento 2: Error en columnas faltantes no opcionales
                        self.logger.error(f"Error en {tag}: {e}")
                        raise ValueError(f"Error en {tag}: {e}")

                    # Memory management crítico para archivos grandes
                    elem.clear()


class ProcessingStats:
    """Estadísticas de procesamiento para debugging futuro."""

    def __init__(self):
        self.row_counts = {}
        self.total_rows = 0

    def processed_row(self, table_name: str) -> None:
        """Registra fila procesada."""
        self.row_counts[table_name] = self.row_counts.get(table_name, 0) + 1
        self.total_rows += 1

    def get_stats(self) -> dict:
        """Retorna estadísticas actuales."""
        return {"total_rows": self.total_rows, "rows_by_table": self.row_counts.copy()}
