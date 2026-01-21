"""Base entity unificada con metadata de procesamiento.

Combina dataclass typing con TableSpec metadata en un solo sistema.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, ClassVar, Optional, Self, get_type_hints
from dataclasses import fields
from xml.etree.ElementTree import Element
from datetime import datetime


class DuckDBType(Enum):
    """Tipos de datos DuckDB mapeados."""

    INTEGER = "INTEGER"
    BIGINT = "BIGINT"
    VARCHAR = "VARCHAR"
    BOOLEAN = "BOOLEAN"
    UUID = "UUID"
    DOUBLE = "DOUBLE"
    DATE = "DATE"
    TIMESTAMP = "TIMESTAMP"


class Field:
    """Field con metadata para procesamiento de datos.

    Combina type hints con metadata de conversión y validación.
    """

    def __init__(
        self,
        *,
        converter: Optional[Callable[[str | None], Any]] = None,
        required: bool = True,
        duckdb_type: Optional[DuckDBType] = None,
        column_name: Optional[str] = None,
        default: Any = None,
    ):
        """
        Inicializa Field con metadata de procesamiento.

        Args:
            converter: Función para convertir desde string XML
            required: Si el campo es requerido (no nullable)
            duckdb_type: Tipo DuckDB para CREATE TABLE
            column_name: Nombre de columna en DB (diferente al field name)
            default: Valor por defecto si no está presente
        """
        self.converter = converter or str
        self.required = required
        self.duckdb_type = duckdb_type or DuckDBType.VARCHAR
        self.column_name = column_name
        self.default = default

        # Para boolean fields con valores especiales
        if self.converter is str:
            # Default converter limpia strings
            self.converter = lambda s: (s or "").strip() if s is not None else default

    def convert(self, value: Any) -> Any:
        """Convierte valor usando el converter definido."""
        if value is None:
            if self.required:
                raise ValueError("Campo requerido es None")
            return self.default
        return self.converter(value)

    def get_sql_definition(self, field_name: str) -> str:
        """Genera definición SQL para CREATE TABLE."""
        col_name = self.column_name or field_name

        # Handle reserved keywords
        if col_name.lower() in ["index", "show"]:
            col_name = f'"{col_name}"'

        sql_type = self.duckdb_type.value

        # Handle nullable columns
        if not self.required:
            sql_type += " DEFAULT NULL"

        return f"{col_name} {sql_type}"


def BooleanField(**kwargs) -> Field:
    """Convenientia para fields booleanos."""
    kwargs.setdefault("duckdb_type", DuckDBType.BOOLEAN)
    kwargs.setdefault(
        "converter",
        lambda s: (s or "").strip().lower() in {"true", "1", "yes", "y", "t"},
    )
    return Field(**kwargs)


def IntegerField(**kwargs) -> Field:
    """Convenientia para fields enteros."""
    kwargs.setdefault("duckdb_type", DuckDBType.INTEGER)
    kwargs.setdefault("converter", int)
    return Field(**kwargs)


def StringField(**kwargs) -> Field:
    """Convenientia para fields de texto."""
    kwargs.setdefault("duckdb_type", DuckDBType.VARCHAR)
    return Field(**kwargs)


def UUIDField(**kwargs) -> Field:
    """Convenientia para fields UUID."""
    kwargs.setdefault("duckdb_type", DuckDBType.UUID)
    kwargs.setdefault("converter", lambda s: (s or "").strip() or None)
    kwargs.setdefault("required", False)  # UUIDs usually optional
    return Field(**kwargs)


@dataclass(frozen=True, slots=True)
class BaseEntity:
    """Base entity con metadata de procesamiento integrada.

    Combina:
    - Dataclass para type safety y IDE support
    - ClassVars para metadata de procesamiento
    - Métodos para conversión y validación
    """

    # --- Metadata ClassVars (sobreescribir en subclasses) ---
    row_tag: ClassVar[str] = ""  # Tag XML para esta entidad
    fields: ClassVar[dict[str, Field]] = {}

    def __post_init__(self):
        """Validación post-creación."""
        # Validar que todos los fields requeridos tengan valores
        for field_name, field_def in self.fields.items():
            value = getattr(self, field_name, None)
            if field_def.required and value is None:
                raise ValueError(
                    f"Campo requerido '{field_name}' es None en {self.__class__.__name__}"
                )

    @classmethod
    def get_columns(cls) -> tuple[str, ...]:
        """
        Retorna columnas en orden para SQL.

        Orden: primero los fields definidos en fields, luego los demás.

        Returns:
            Tupla con nombres de columnas en orden de inserción
        """
        # Ordenar por definición en fields dict (preserva orden)
        field_columns = []

        # Primero: columnas definidas en fields
        for field_name in cls.fields.keys():
            column_name = cls.fields[field_name].column_name or field_name
            field_columns.append(column_name)

        # Luego: columnas de dataclass no en fields
        dataclass_fields = [f.name for f in cls.__dataclass_fields__.values()]
        other_columns = [col for col in dataclass_fields if col not in cls.fields]

        return tuple(field_columns + other_columns)

    @classmethod
    def get_converters(cls) -> dict[str, Callable]:
        """
        Retorna diccionario de converters por nombre de campo.

        Returns:
            {field_name: converter_function}
        """
        return {name: field_def.converter for name, field_def in cls.fields.items()}

    @classmethod
    def get_required_columns(cls) -> set[str]:
        """
        Retorna conjunto de columnas requeridas.

        Returns:
            Set de nombres de columnas requeridas
        """
        return {name for name, field_def in cls.fields.items() if field_def.required}

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "BaseEntity":
        """
        Crea instancia desde diccionario de datos XML.

        Args:
            data: Diccionario {column_name: string_value} desde XML

        Returns:
            Instancia de la entidad con tipos convertidos

        Raises:
            ValueError: Si faltan campos requeridos o hay errores de conversión
        """
        # Validar campos requeridos
        required = cls.get_required_columns()
        missing = required - set(data.keys())
        if missing:
            raise ValueError(f"Campos requeridos faltantes en {cls.row_tag}: {missing}")

        # Convertir datos
        converted = {}
        for field_name, field_def in cls.fields.items():
            raw_value = data.get(field_name)
            try:
                converted[field_name] = field_def.convert(raw_value)
            except Exception as e:
                raise ValueError(f"Error convirtiendo campo '{field_name}': {e}")

        # Manejar otros fields no definidos explícitamente
        dataclass_fields = [f.name for f in cls.__dataclass_fields__.values()]
        for field_name in dataclass_fields:
            if field_name not in converted and field_name in data:
                # Usar default converter (string)
                converted[field_name] = data[field_name]

        return cls(**converted)

    def to_tuple(self) -> tuple:
        """
        Convierte entidad a tupla para bulk insert.

        Returns:
            Tupla con valores en orden de columnas SQL
        """
        values = []

        for field_name in self.fields.keys():
            value = getattr(self, field_name)
            values.append(value)

        # Agregar valores de otros dataclass fields
        dataclass_fields = [f.name for f in self.__dataclass_fields__.values()]
        for field_name in dataclass_fields:
            if field_name not in self.fields and hasattr(self, field_name):
                value = getattr(self, field_name)
                values.append(value)

        return tuple(values)

    @classmethod
    def validate_row_data(cls, data: dict[str, str]) -> None:
        """
        Valida datos de fila sin crear instancia.

        Args:
            data: Diccionario de datos XML

        Raises:
            ValueError: Si la validación falla
        """
        # Validar campos requeridos
        required = cls.get_required_columns()
        missing = required - set(data.keys())
        if missing:
            raise ValueError(f"Campos requeridos faltantes en {cls.row_tag}: {missing}")

        # Validar que se puedan convertir
        for field_name, field_def in cls.fields.items():
            if field_name in data:
                try:
                    field_def.convert(data[field_name])
                except Exception as e:
                    raise ValueError(f"Error validando campo '{field_name}': {e}")

    @classmethod
    def get_table_sql(cls, schema_name: str = "plexos") -> str:
        """
        Genera SQL CREATE TABLE completo.

        Args:
            schema_name: Nombre del schema DuckDB

        Returns:
            String SQL para CREATE TABLE
        """
        columns_sql = []

        for field_name, field_def in cls.fields.items():
            column_def = field_def.get_sql_definition(field_name)
            columns_sql.append(column_def)

        all_columns = ",\n    ".join(columns_sql)

        return f"""
CREATE TABLE IF NOT EXISTS {schema_name}.{cls.row_tag} (
    {all_columns}
);
        """.strip()

    def to_dict(self) -> dict:
        """
        Convierte entidad a diccionario.

        Returns:
            Diccionario con todos los campos y valores
        """
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }


def process_value(name: str, elem: Element, row_type: Any) -> Any:
    text: str | None = elem.findtext(f"{{*}}{name}")
    # optional: bool = False

    # Manejo de tipo opcional se extrae el tipo que no es None.
    # Esta función solo funciona para tipo opcional, digase "Type[T] | None"
    # if type(row_type) is UnionType:
    # optional = True
    # row_type = [t for t in get_args(row_type) if t is not type(None)][0]

    # Verificador de que vienen todos los valores que se necesitan
    # if text is None and optional is False:
    #     raise ValueError(f"falta campo: {name} y no es opcional.")

    if row_type is str:
        return text
    elif row_type is int:
        return int(text)
    elif row_type is float:
        return float(text)
    elif row_type is bool:
        return text.strip().lower() == "true"
    elif row_type is datetime:
        return datetime.strptime(text, "%Y-%m-%d %H:%M")
    else:
        return str(text)


@dataclass(frozen=True, slots=True)
class BaseTable:
    @classmethod
    def from_element(cls, elem: Element) -> Self:
        table_types = get_type_hints(cls)
        data = {
            fd.name: process_value(fd.name, elem, table_types[fd.name])
            for fd in fields(cls)
        }
        return cls(**data)
