"""XML streaming processor optimizado.

Procesamiento streaming de XML PLEXOS con performance para archivos grandes.
Arquitectura optimizada para 100MB XML.
"""

from pathlib import Path
from typing import Iterator, Tuple, Union
from xml.etree.ElementTree import iterparse
from zipfile import ZipFile

from ...common.logging_config import get_logger
from ...model.common.exceptions import MissingColumnError
from ...model.common.xml_utils import extract_children_text, strip_namespace
from ...model.entities.entity_registry import EntityRegistry
from ...model.entities.table_register import TableRegister


class XMLProcessor:
    """Streaming XML processor optimizado para archivos grandes."""

    def __init__(self, entity_registry: EntityRegistry, table_registry: TableRegister):
        """
        Inicializa processor con registry de entities.

        Args:
            entity_registry: Registry de Entities validado (usa default si None)
        """
        self.entity_registry = entity_registry
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
                table_name: str = ""
                for _, elem in iterparse(f, events=("end",)):
                    tag = strip_namespace(elem.tag)

                    # Comportamiento 1: Ignorar tablas desconocidas con warning
                    if not self.entity_registry.is_supported(tag):
                        # Solo arma log cuanto se ve una tabla (todas parte por t_).
                        # En caso de ser una columna se ignora para log
                        if tag[0:2] == "t_":
                            if tag == table_name:
                                continue
                            else:
                                table_name = tag
                            self.logger.warning(f"Ignorando tabla desconocida: {tag}")
                        continue

                    self.logger.debug(f"Procesando elemento: {tag}")

                    try:
                        # Extracción ultra-rápida de datos
                        row_data = extract_children_text(elem)
                        self.logger.debug(
                            f"Extraídos {len(row_data)} campos para {tag}"
                        )

                        # Validación de columnas requeridas
                        self.entity_registry.validate_row_data(tag, row_data)

                        # Conversión a Entity y luego a tupla
                        entity = self.entity_registry.create_entity_from_dict(
                            tag, row_data
                        )
                        row_tuple = entity.to_tuple()

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
