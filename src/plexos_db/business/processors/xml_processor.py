"""XML streaming processor optimizado.

Procesamiento streaming de XML PLEXOS con performance para archivos grandes.
Arquitectura optimizada para 100MB XML.
"""

from pathlib import Path
from typing import Iterator, Tuple
from xml.etree.ElementTree import iterparse
from zipfile import ZipFile

from ...common.logging_config import get_logger
from ...model.common.exceptions import MissingColumnError
from ...model.entities.table_register import TableRegister

def strip_namespace(tag: str) -> str:
    return tag.split("}", 1)[-1]

class XMLProcessor:
    """Streaming XML processor optimizado para archivos grandes."""

    def __init__(self, table_registry: TableRegister):
        """
        Inicializa processor con registry de entities.

        Args:
            entity_registry: Registry de Entities validado (usa default si None)
        """
        self.table_registry = table_registry
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
        self.logger.info(
            f"Iniciando streaming de ZIP: {zip_path.name}, XML: {xml_name}"
        )

        with ZipFile(zip_path) as zf:
            with zf.open(xml_name, "r") as f:
                for _, elem in iterparse(f, events=("end",)):
                    tag = strip_namespace(elem.tag)

                    if not self.table_registry.is_supported(tag):
                        continue

                    try:
                        table = self.table_registry.get_table(tag)
                        row = table.from_element(elem)

                        yield row 
                        self._stats.processed_row(tag)

                    except MissingColumnError as e:
                        self.logger.error(f"Error en {tag}: {e}")
                        raise ValueError(f"Error en {tag}: {e}")

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
