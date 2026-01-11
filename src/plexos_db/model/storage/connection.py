"""DuckDB connection management.

Gestión de conexiones DuckDB con manejo de errores y configuración.
"""

import duckdb
from pathlib import Path
from typing import Optional
from ..common.exceptions import DatabaseError


class DuckDBConnection:
    """Manejador de conexiones DuckDB con contexto seguro."""
    
    def __init__(self, db_path: Path, read_only: bool = False):
        """
        Inicializa conexión DuckDB.
        
        Args:
            db_path: Ruta a la base de datos
            read_only: Si la conexión es de solo lectura
        """
        self.db_path = db_path
        self.read_only = read_only
        self._connection: Optional[duckdb.DuckDBPyConnection] = None
    
    def connect(self) -> duckdb.DuckDBPyConnection:
        """
        Establece conexión a DuckDB.
        
        Returns:
            Conexión DuckDB activa
            
        Raises:
            DatabaseError: Si no se puede conectar
        """
        if self._connection is not None:
            return self._connection
        
        try:
            if self.read_only:
                self._connection = duckdb.connect(str(self.db_path), read_only=True)
            else:
                self._connection = duckdb.connect(str(self.db_path))
            return self._connection
        except Exception as e:
            raise DatabaseError(f"No se puede conectar a {self.db_path}: {e}")
    
    def close(self) -> None:
        """Cierra la conexión."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None
    
    def __enter__(self) -> duckdb.DuckDBPyConnection:
        """Context manager entry."""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()
    
    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Obtiene conexión activa."""
        if self._connection is None:
            return self.connect()
        return self._connection