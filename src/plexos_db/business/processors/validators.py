"""Validators optimizados para business layer.

Validación manual optimizada para performance con archivos grandes.
Implementa el comportamiento definido: ignorar desconocidas, error faltantes.
"""

from pathlib import Path

# from ...model.schemas.base import TableSpec
# from ...model.common.exceptions import MissingColumnError


# class RowValidator:
#     """Validación manual optimizada para 100MB XML."""

#     @staticmethod
#     def validate_fast(row_data: Dict[str, str], spec: TableSpec) -> tuple[Any, ...]:
#         """
#         Validación ultra-rápida para 100MB XML.
#         Retorna tuple directamente para inserción.

#         Args:
#             row_data: Datos brutos desde XML
#             spec: TableSpec con validación

#         Returns:
#             Tupla con datos convertidos

#         Raises:
#             MissingColumnError: Si faltan columnas requeridas
#         """
#         # Validación rápida de columnas requeridas
#         RowValidator._validate_required_fast(row_data, spec)

#         # Conversión directa a tupla
#         result = []
#         for col in spec.columns:
#             raw = row_data.get(col)
#             converter = spec.get_converter(col)
#             result.append(converter(raw))

#         return tuple(result)

#     @staticmethod
#     def _validate_required_fast(row_data: Dict[str, str], spec: TableSpec) -> None:
#         """
#         Verifica presencia de campos requeridos - O(n) optimizado.

#         Args:
#             row_data: Datos de la fila
#             spec: TableSpec con definición

#         Raises:
#             MissingColumnError: Si faltan columnas requeridas
#         """
#         # Pre-compute required columns si no está cacheado
#         if not hasattr(spec, "_required_columns_cache"):
#             spec._required_columns_cache = spec.get_required_columns()

#         required = spec._required_columns_cache

#         # Fast membership check
#         missing = [
#             col for col in required if col not in row_data or row_data[col] is None
#         ]
#         if missing:
#             raise MissingColumnError(
#                 f"Columnas requeridas faltantes: {missing}", missing_columns=missing
#             )


class FileValidator:
    """Validación de archivos ZIP y XML."""

    @staticmethod
    def validate_zip_path(zip_path: Path) -> None:
        """
        Valida que el path del ZIP sea válido.

        Args:
            zip_path: Path al archivo ZIP

        Raises:
            ValueError: Si el path no es válido
        """
        if not zip_path.exists():
            raise ValueError(f"Archivo ZIP no existe: {zip_path}")

        if not zip_path.is_file():
            raise ValueError(f"Path no es un archivo: {zip_path}")

        if zip_path.suffix.lower() != ".zip":
            raise ValueError(f"Archivo debe ser ZIP: {zip_path}")

    @staticmethod
    def validate_db_path(db_path: Path) -> None:
        """
        Valida que el path de la base de datos sea válido.

        Args:
            db_path: Path a la base de datos

        Raises:
            ValueError: Si el path no es válido
        """
        parent_dir = db_path.parent
        if not parent_dir.exists():
            raise ValueError(f"Directorio de salida no existe: {parent_dir}")

        if db_path.suffix.lower() not in (".duckdb", ".ddb"):
            raise ValueError(f"Base de datos debe ser .duckdb: {db_path}")

    @staticmethod
    def validate_xml_name(xml_name: str) -> None:
        """
        Valida nombre del archivo XML.

        Args:
            xml_name: Nombre del archivo XML

        Raises:
            ValueError: Si el nombre no es válido
        """
        if not xml_name:
            raise ValueError("Nombre del archivo XML no puede estar vacío")

        if not xml_name.lower().endswith(".xml"):
            raise ValueError(f"Archivo debe ser XML: {xml_name}")
