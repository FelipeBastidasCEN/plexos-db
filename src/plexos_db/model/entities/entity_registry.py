"""Entity registry centralizado.

Registry simplificado que apunta directamente a entities con metadata integrada.
Reemplaza al SchemaRegistry original.
"""

from typing import Dict, Type, Callable

from ..common.exceptions import UnknownTableError
from .base_entity import BaseEntity
from .t_object import TObject
from .t_property import TProperty


class EntityRegistry:
    """Registry centralizado de entities con metadata integrada.

    Reemplaza SchemaRegistry eliminando la duplicación con TableSpecs.
    """

    # ÚNICO lugar para agregar nuevas entidades
    SUPPORTED_ENTITIES: Dict[str, Type[BaseEntity]] = {
        "t_object": TObject,
        "t_property": TProperty,
        # FUTURO: Agregar aquí nuevas entidades
    }

    @classmethod
    def get_entity_class(cls, table_name: str) -> Type[BaseEntity]:
        """
        Obtiene clase de entidad por nombre de tabla.

        Args:
            table_name: Nombre de la tabla (ej: "t_object")

        Returns:
            Clase de entidad correspondiente

        Raises:
            UnknownTableError: Si la tabla no está soportada
        """
        if table_name not in cls.SUPPORTED_ENTITIES.keys():
            from ...common.logging_config import get_logger

            logger = get_logger("model.entity_registry")
            logger.warning(f"Tabla desconocida encontrada: {table_name}")

            raise UnknownTableError(
                table_name=table_name,
                supported_tables=list(cls.SUPPORTED_ENTITIES.keys()),
            )
        return cls.SUPPORTED_ENTITIES[table_name]

    @classmethod
    def is_supported(cls, table_name: str) -> bool:
        """
        Verifica si una tabla es soportada.

        Args:
            table_name: Nombre de la tabla

        Returns:
            True si la tabla es soportada
        """
        return table_name in cls.SUPPORTED_ENTITIES

    @classmethod
    def get_all_entities(cls) -> Dict[str, Type[BaseEntity]]:
        """
        Retorna copia del registry de entidades.

        Returns:
            Diccionario con todas las entidades soportadas
        """
        return cls.SUPPORTED_ENTITIES.copy()

    @classmethod
    def get_all_table_names(cls) -> list[str]:
        """
        Retorna lista de nombres de tablas soportadas.

        Returns:
            Lista de nombres de tablas
        """
        return list(cls.SUPPORTED_ENTITIES.keys())

    @classmethod
    def get_required_columns(cls, table_name: str) -> list[str]:
        """
        Obtiene columnas requeridas para una tabla.

        Args:
            table_name: Nombre de la tabla

        Returns:
            Lista de nombres de columnas requeridas
        """
        entity_class = cls.get_entity_class(table_name)
        return list(entity_class.get_required_columns())

    @classmethod
    def get_table_columns(cls, table_name: str) -> tuple[str, ...]:
        """
        Obtiene columnas en orden para SQL.

        Args:
            table_name: Nombre de la tabla

        Returns:
            Tupla con nombres de columnas en orden
        """
        entity_class = cls.get_entity_class(table_name)
        return entity_class.get_columns()

    @classmethod
    def get_converters(cls, table_name: str) -> dict[str, Callable]:
        """
        Obtiene converters para una tabla.

        Args:
            table_name: Nombre de la tabla

        Returns:
            Diccionario de {column_name: converter_function}
        """
        entity_class = cls.get_entity_class(table_name)
        return entity_class.get_converters()

    @classmethod
    def validate_row_data(cls, table_name: str, data: dict[str, str]) -> None:
        """
        Valida datos de fila para una tabla.

        Args:
            table_name: Nombre de la tabla
            data: Datos de la fila desde XML

        Raises:
            ValueError: Si la validación falla
        """
        entity_class = cls.get_entity_class(table_name)
        entity_class.validate_row_data(data)

    @classmethod
    def create_entity_from_dict(
        cls, table_name: str, data: dict[str, str]
    ) -> BaseEntity:
        """
        Crea entidad desde diccionario de datos XML.

        Args:
            table_name: Nombre de la tabla
            data: Diccionario de datos XML

        Returns:
            Instancia de la entidad con datos convertidos
        """
        entity_class = cls.get_entity_class(table_name)
        return entity_class.from_dict(data)


# Instancia global para acceso conveniente
entity_registry = EntityRegistry()
