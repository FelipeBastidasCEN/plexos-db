"""Base classes para table specifications.

Clases base para definir y procesar especificaciones de tablas PLEXOS.
"""

from dataclasses import dataclass, field
from typing import Callable, Mapping, Sequence, Any

from ...common.logging_config import get_logger


@dataclass(frozen=True, slots=True)
class TableSpec:
    """Especificación de tabla PLEXOS con metadata y conversión."""

    row_tag: str
    columns: Sequence[str] = field(default_factory=list)
    converters: Mapping[str, Callable[[str | None], Any]] = field(default_factory=dict)
    table_name: str = field(init=False)
    _logger: Any = field(init=False, default=None)

    def __post_init__(self):
        """Inicializa valores derivados."""
        # Derivar table_name de row_tag
        table_name = self.row_tag
        if table_name.startswith("t_"):
            table_name = table_name[2:]
        object.__setattr__(self, "table_name", table_name)
        object.__setattr__(self, "_logger", get_logger("model.schemas"))

    def get_converter(self, column: str) -> Callable[[str | None], Any]:
        """
        Obtiene converter para una columna.

        Args:
            column: Nombre de la columna

        Returns:
            Converter function o identity si no está definido
        """
        return self.converters.get(column, lambda x: x)

    def get_required_columns(self) -> list[str]:
        """
        Obtiene lista de columnas requeridas (no opcionales).

        Returns:
            Lista de nombres de columnas requeridas
        """
        from ..common.converters import to_int_opt, to_str_opt

        required = []
        for col in self.columns:
            converter = self.converters.get(col)
            # Si el converter no es opcional, la columna es requerida
            if converter not in (to_int_opt, to_str_opt, None):
                required.append(col)
        return required

    def validate_row_data(self, row_data: dict[str, str]) -> None:
        """
        Valida que todas las columnas requeridas estén presentes.

        Args:
            row_data: Datos de la fila desde XML

        Raises:
            MissingColumnError: Si faltan columnas requeridas
        """
        from ..common.exceptions import MissingColumnError

        required = self.get_required_columns()
        missing = [
            col for col in required if col not in row_data or row_data[col] is None
        ]
        if missing:
            raise MissingColumnError(
                f"Columnas requeridas faltantes en {self.row_tag}: {missing}",
                missing_columns=missing,
            )

    def convert_row(self, row_data: dict[str, str]) -> tuple[Any, ...]:
        """
        Convierte datos de fila usando converters definidos.

        Args:
            row_data: Datos brutos desde XML

        Returns:
            Tupla con datos convertidos en orden de columns
        """
        logger = get_logger("model.schemas")
        logger.debug(f"Convirtiendo {len(row_data)} campos para tabla {self.table_name}")
        
        result = []
        for col in self.columns:
            raw = row_data.get(col)
            converter = self.get_converter(col)
            result.append(converter(raw))

        return tuple(result)
