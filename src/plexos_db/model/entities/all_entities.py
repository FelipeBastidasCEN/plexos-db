"""Registry de entidades PLEXOS.

Registro centralizado de todas las entidades soportadas en el sistema.
Solo entidades explícitamente definidas son soportadas - no dinámico.
"""

from typing import Type, Union
from .t_object import TObject
from .t_property import TProperty


# Registry de entidades soportadas
SUPPORTED_ENTITIES = {
    "t_object": TObject,
    "t_property": TProperty,
    # Nuevas entidades se agregan explícitamente aquí
}


def get_entity_class(table_name: str) -> Type:
    """
    Obtiene clase de entidad por nombre de tabla.
    
    Args:
        table_name: Nombre de la tabla (ej: "t_object")
        
    Returns:
        Clase de entity correspondiente
        
    Raises:
        ValueError: Si la tabla no está soportada
    """
    if table_name not in SUPPORTED_ENTITIES:
        raise ValueError(f"Entidad '{table_name}' no definida. "
                       f"Entidades soportadas: {list(SUPPORTED_ENTITIES.keys())}")
    return SUPPORTED_ENTITIES[table_name]


def get_all_entities() -> dict[str, Type]:
    """
    Retorna copia del registry de entidades.
    
    Returns:
        Diccionario con todas las entidades soportadas
    """
    return SUPPORTED_ENTITIES.copy()


def is_supported(table_name: str) -> bool:
    """
    Verifica si una tabla es soportada.
    
    Args:
        table_name: Nombre de la tabla
        
    Returns:
        True si la tabla es soportada
    """
    return table_name in SUPPORTED_ENTITIES


# Union type para type hints - se expande con nuevas entidades
AnyPLEXOSEntity = Union[TObject, TProperty]


# Lista de nombres de tablas soportadas para validaciones
SUPPORTED_TABLE_NAMES = list(SUPPORTED_ENTITIES.keys())