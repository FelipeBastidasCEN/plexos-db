"""Logging configuration centralizada para PLEXOS-DB.

Configuración de logging con múltiples handlers:
- Consola con colores para CLI
- Rotación automática de archivos
- SQLite para persistencia de errores y warnings
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    enable_file: bool = True,
    enable_sqlite: bool = True,
    sqlite_path: Optional[Path] = None,
    sqlite_min_level: str = "WARNING",
    max_file_size_mb: int = 10,
    backup_count: int = 5,
) -> logging.Logger:
    """
    Configura logging para PLEXOS-DB con múltiples handlers.

    Args:
        log_level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directorio para logs de archivo
        enable_file: Habilitar logging a archivo con rotación
        enable_sqlite: Habilitar logging a SQLite
        sqlite_path: Ruta a base de datos SQLite
        sqlite_min_level: Nivel mínimo para SQLite
        max_file_size_mb: Tamaño máximo de archivo antes de rotar
        backup_count: Número de archivos de backup a mantener

    Returns:
        Logger configurado para PLEXOS-DB
    """

    # Configuración por defecto
    if log_dir is None:
        log_dir = Path("logs")
    if sqlite_path is None:
        sqlite_path = Path("plexos_logs.db")

    # Asegurar que directorio de logs exista
    log_dir.mkdir(exist_ok=True)

    # Logger principal
    logger = logging.getLogger("plexos_db")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Limpiar handlers existentes para evitar duplicados
    logger.handlers.clear()

    # 1. Handler de consola (con colores para CLI)
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s", "%Y/%m/%d %H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    # 2. Handler de archivo con rotación automática
    if enable_file:
        file_path = log_dir / "plexos_db.log"
        file_handler = logging.handlers.RotatingFileHandler(
            file_path,
            maxBytes=max_file_size_mb * 1024 * 1024,  # Convertir MB a bytes
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # 3. Handler SQLite para persistencia
    if enable_sqlite:
        sqlite_handler = SQLiteHandler(sqlite_path)
        sqlite_handler.setLevel(getattr(logging, sqlite_min_level.upper()))
        sqlite_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        sqlite_handler.setFormatter(sqlite_formatter)
        logger.addHandler(sqlite_handler)

    return logger


class ColoredFormatter(logging.Formatter):
    """Formatter con colores para CLI."""

    # Códigos de color ANSI
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record):
        # Agregar colores al nivel
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}"
                f"{record.levelname}"
                f"{self.COLORS['RESET']}"
            )

        return super().format(record)


class SQLiteHandler(logging.Handler):
    """Handler personalizado para SQLite con tabla optimizada."""

    def __init__(self, db_path: Path):
        super().__init__()
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Inicializa base de datos SQLite y tabla de logs."""
        import sqlite3

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,
                    logger_name TEXT NOT NULL,
                    message TEXT NOT NULL,
                    module TEXT,
                    function TEXT,
                    line_number INTEGER,
                    thread_id INTEGER,
                    process_id INTEGER
                )
            """)

            # Índices para performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_level 
                ON logs(level)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_logs_created 
                ON logs(created)
            """)
            conn.commit()

    def emit(self, record):
        """Escribe log record a SQLite."""
        import sqlite3

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO logs (
                        level, logger_name, message, module, 
                        function, line_number, thread_id, process_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        record.levelname,
                        record.name,
                        record.getMessage(),
                        getattr(record, "module", None),
                        getattr(record, "funcName", None),
                        getattr(record, "lineno", None),
                        record.thread,
                        record.process,
                    ),
                )
                conn.commit()
        except Exception:
            # Evitar recursión infinita si falla el logging
            self.handleError(record)


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene logger configurado para un módulo específico.

    Args:
        name: Nombre del módulo (ej: 'model.schemas')

    Returns:
        Logger para el módulo especificado
    """
    return logging.getLogger(f"plexos_db.{name}")
