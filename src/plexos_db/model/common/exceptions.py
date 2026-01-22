"""Custom exceptions para PLEXOS-DB.

Excepciones específicas para manejo de errores en procesamiento de datos.
"""


class PLEXOSDBError(Exception):
    """Error base para PLEXOS-DB."""


class ValidationError(PLEXOSDBError):
    """Error en validación de datos."""

    pass


class MissingColumnError(ValidationError):
    """Columna requerida faltante en datos."""

    def __init__(self, message: str, missing_columns: list[str] | None = None):
        super().__init__(message)
        self.missing_columns = missing_columns or []


class UnknownTableError(ValidationError):
    """Tabla no soportada encontrada en XML."""

    def __init__(self, table_name: str, supported_tables: list[str]):
        message = (
            f"Tabla '{table_name}' no soportada. Tablas soportadas: {supported_tables}"
        )
        super().__init__(message)
        self.table_name = table_name
        self.supported_tables = supported_tables


class XMLParsingError(PLEXOSDBError):
    """Error en parsing de XML."""

    pass


class DatabaseError(PLEXOSDBError):
    """Error en operaciones de base de datos."""

    pass


class ConfigurationError(PLEXOSDBError):
    """Error en configuración del sistema."""

    pass
