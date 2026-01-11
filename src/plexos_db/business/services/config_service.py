"""Configuration service.

Gestión de configuración para PLEXOS-DB.
Preparado para configuración YAML futura.
"""

from pathlib import Path
from typing import Dict, Any, Optional
from ...model.common.exceptions import ConfigurationError


class ConfigService:
    """Servicio de configuración para PLEXOS-DB."""
    
    # Default configuration values
    DEFAULT_CONFIG = {
        "xml": {
            "default_name": "SolutionDataset.xml",
            "encoding": "utf-8"
        },
        "database": {
            "default_chunk_size": 10_000,
            "max_chunk_size": 1_000_000,
            "schema_name": "plexos"
        },
        "processing": {
            "max_memory_mb": 1024,
            "timeout_seconds": 300
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Inicializa servicio de configuración.
        
        Args:
            config_path: Ruta a archivo de configuración (opcional)
        """
        self.config_path = config_path
        self._config = self.DEFAULT_CONFIG.copy()
        
        if config_path and config_path.exists():
            self._load_config()
    
    def _load_config(self) -> None:
        """
        Carga configuración desde archivo.
        
        FUTURO: Implementar carga YAML cuando se agregue soporte
        
        Raises:
            ConfigurationError: Si no se puede cargar la configuración
        """
        try:
            # Placeholder para carga de archivos de configuración futuros
            # Por ahora solo se valida que el archivo exista
            if self.config_path.suffix.lower() in ['.yaml', '.yml']:
                # FUTURO: Implementar carga YAML
                pass
            elif self.config_path.suffix.lower() == '.json':
                # FUTURO: Implementar carga JSON
                pass
            else:
                raise ConfigurationError(f"Formato de configuración no soportado: {self.config_path}")
                
        except Exception as e:
            raise ConfigurationError(f"Error cargando configuración desde {self.config_path}: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Obtiene valor de configuración usando dot notation.
        
        Args:
            key_path: Path a la configuración (ej: "database.default_chunk_size")
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración
            
        Example:
            config.get("database.default_chunk_size")  # returns 10000
        """
        keys = key_path.split('.')
        current = self._config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        Establece valor de configuración usando dot notation.
        
        Args:
            key_path: Path a la configuración (ej: "database.default_chunk_size")
            value: Valor a establecer
            
        Raises:
            ConfigurationError: Si el path es inválido
        """
        keys = key_path.split('.')
        current = self._config
        
        try:
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            
            current[keys[-1]] = value
            
        except Exception as e:
            raise ConfigurationError(f"Error estableciendo configuración {key_path}: {e}")
    
    def get_xml_defaults(self) -> Dict[str, Any]:
        """
        Retorna configuración por defecto para XML.
        
        Returns:
            Diccionario con configuración XML
        """
        return self.get("xml", {}).copy()
    
    def get_database_config(self) -> Dict[str, Any]:
        """
        Retorna configuración de base de datos.
        
        Returns:
            Diccionario con configuración de database
        """
        return self.get("database", {}).copy()
    
    def get_processing_config(self) -> Dict[str, Any]:
        """
        Retorna configuración de procesamiento.
        
        Returns:
            Diccionario con configuración de processing
        """
        return self.get("processing", {}).copy()
    
    def validate_chunk_size(self, chunk_size: int) -> None:
        """
        Valida que el chunk_size esté en rango válido.
        
        Args:
            chunk_size: Tamaño de chunk a validar
            
        Raises:
            ConfigurationError: Si el chunk_size es inválido
        """
        min_size = 1
        max_size = self.get("database.max_chunk_size", 1_000_000)
        
        if chunk_size < min_size:
            raise ConfigurationError(f"chunk_size debe ser >= {min_size}, recibido: {chunk_size}")
        
        if chunk_size > max_size:
            raise ConfigurationError(f"chunk_size debe ser <= {max_size}, recibido: {chunk_size}")
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        Retorna toda la configuración actual.
        
        Returns:
            Diccionario con toda la configuración
        """
        return self._config.copy()