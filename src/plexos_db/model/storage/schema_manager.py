"""DuckDB schema management.

Creación dinámica de tablas desde TableSpecs para PLEXOS.
"""

import duckdb
from ..schemas.base import TableSpec
from ..common.exceptions import DatabaseError


class DuckDBSchemaManager:
    """Manejador de schemas DuckDB con generación dinámica desde TableSpecs."""
    
    def __init__(self, connection: duckdb.DuckDBPyConnection):
        """
        Inicializa manager de schemas.
        
        Args:
            connection: Conexión DuckDB activa
        """
        self.connection = connection
        self._create_plexos_schema()
    
    def _create_plexos_schema(self) -> None:
        """Crea schema plexos si no existe."""
        try:
            self.connection.execute("CREATE SCHEMA IF NOT EXISTS plexos;")
        except Exception as e:
            raise DatabaseError(f"No se puede crear schema plexos: {e}")
    
    def create_table_from_spec(self, spec: TableSpec) -> None:
        """
        Crea tabla DuckDB desde TableSpec.
        
        Args:
            spec: TableSpec con definición de tabla
        """
        columns_sql = self._generate_columns_sql(spec)
        table_name = f"plexos.{spec.table_name}"
        
        sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {columns_sql}
            );
        """
        
        try:
            self.connection.execute(sql)
        except Exception as e:
            raise DatabaseError(f"No se puede crear tabla {spec.table_name}: {e}")
    
    def create_all_tables(self, specs: dict[str, TableSpec]) -> None:
        """
        Crea todas las tablas desde registry de specs.
        
        Args:
            specs: Diccionario de TableSpecs
        """
        for spec in specs.values():
            self.create_table_from_spec(spec)
    
    def _generate_columns_sql(self, spec: TableSpec) -> str:
        """
        Genera SQL de columnas desde TableSpec.
        
        Args:
            spec: TableSpec con definición
            
        Returns:
            String SQL con definición de columnas
        """
        from ..schemas.t_object_schema import T_OBJECT_SPEC
        from ..schemas.t_property_schema import T_PROPERTY_SPEC
        
        # Mapeo de columnas a tipos DuckDB basado en converters
        column_types = self._get_column_types(spec)
        
        columns = []
        for col in spec.columns:
            col_type = column_types.get(col, "VARCHAR")
            
            # Manejo especial para columnas con nombres reservados
            if col.lower() in ["index"]:
                col_name = f'"{col}"'
            else:
                col_name = col
                
            columns.append(f"{col_name} {col_type}")
        
        return ",\n        ".join(columns)
    
    def _get_column_types(self, spec: TableSpec) -> dict[str, str]:
        """
        Obtiene tipos DuckDB desde converters de TableSpec.
        
        Args:
            spec: TableSpec con converters
            
        Returns:
            Diccionario {column_name: duckdb_type}
        """
        from ..common.converters import to_int0, to_int_opt, to_bool, clean_uuid
        
        type_mapping = {
            # Integers
            to_int0: "INTEGER",
            to_int_opt: "INTEGER",
            # Booleans  
            to_bool: "BOOLEAN",
            # UUIDs
            clean_uuid: "UUID",
            # Strings default
            lambda s: (s or "").strip().lower() in {"true", "1", "yes", "y", "t"}: "BOOLEAN",
        }
        
        column_types = {}
        for col, converter in spec.converters.items():
            duckdb_type = type_mapping.get(converter, "VARCHAR")
            
            # Handle nullable types
            if converter in [to_int_opt, clean_uuid]:
                duckdb_type += " DEFAULT NULL"
            
            column_types[col] = duckdb_type
        
        return column_types