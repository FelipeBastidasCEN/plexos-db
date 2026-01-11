"""Schema registry con validación.

Registro centralizado y validado de TableSpecs para PLEXOS.
Solo schemas explícitamente definidos son soportados.
"""

from typing import Dict
from .base import TableSpec
from .t_object_schema import T_OBJECT_SPEC
from .t_property_schema import T_PROPERTY_SPEC
from ..common.exceptions import UnknownTableError


class SchemaRegistry:
    """Registry validado de TableSpecs - NO dinámico."""
    
    # UNICO lugar para agregar tablas nuevas
    SUPPORTED_TABLES: Dict[str, TableSpec] = {
        "t_object": T_OBJECT_SPEC,
        "t_property": T_PROPERTY_SPEC,
        # FUTURO: Agregar aquí nuevas tablas
    }
    
    @classmethod
    def get_spec(cls, table_name: str) -> TableSpec:
        """
        Obtiene TableSpec por nombre de tabla.
        
        Args:
            table_name: Nombre de la tabla (ej: "t_object")
            
        Returns:
            TableSpec correspondiente
            
        Raises:
            UnknownTableError: Si la tabla no está soportada
        """
        if table_name not in cls.SUPPORTED_TABLES:
            # FUTURO: Aquí se conectará con sistema de logs
            # logger.warning(f"Tabla desconocida encontrada: {table_name}")
            raise UnknownTableError(
                table_name=table_name,
                supported_tables=list(cls.SUPPORTED_TABLES.keys())
            )
        return cls.SUPPORTED_TABLES[table_name]
    
    @classmethod
    def is_supported(cls, table_name: str) -> bool:
        """
        Verifica si una tabla es soportada.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            True si la tabla es soportada
        """
        return table_name in cls.SUPPORTED_TABLES
    
    @classmethod
    def get_all_specs(cls) -> Dict[str, TableSpec]:
        """
        Retorna copia del registry de specs.
        
        Returns:
            Diccionario con todos los TableSpecs soportados
        """
        return cls.SUPPORTED_TABLES.copy()
    
    @classmethod
    def get_all_table_names(cls) -> list[str]:
        """
        Retorna lista de nombres de tablas soportadas.
        
        Returns:
            Lista de nombres de tablas
        """
        return list(cls.SUPPORTED_TABLES.keys())
    
    @classmethod
    def get_required_columns(cls, table_name: str) -> list[str]:
        """
        Obtiene columnas requeridas para una tabla.
        
        Args:
            table_name: Nombre de la tabla
            
        Returns:
            Lista de nombres de columnas requeridas
        """
        spec = cls.get_spec(table_name)
        return spec.get_required_columns()


# Instancia global para acceso conveniente
schema_registry = SchemaRegistry()