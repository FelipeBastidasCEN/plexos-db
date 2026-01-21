"""CLI main entry point.

Parser argparse principal para PLEXOS-DB CLI con argumentos completos.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from ..common.logging_config import get_logger, setup_logging
from ..model.common.exceptions import PLEXOSDBError
from .commands import ImportCommand, ListTablesCommand, ValidateCommand


def create_parser() -> argparse.ArgumentParser:
    """
    Crea parser principal con todos los comandos y argumentos.

    Returns:
        ArgumentParser configurado
    """
    parser = argparse.ArgumentParser(
        prog="plexos-db",
        description="Aplicación CLI para convertir salida PLEXOS (ZIP) en base de datos DuckDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  plexos-db import --input solution.zip --output data.duckdb
  plexos-db import --input solution.zip --output data.duckdb --chunk-size 20000
  plexos-db list-tables
  plexos-db validate --input solution.zip
        """,
    )

    # Subcomandos
    subparsers = parser.add_subparsers(
        dest="command",
        help="Comandos disponibles",
        required=True,
        metavar="{import,list-tables,validate}",
    )

    # Import command
    _create_import_parser(subparsers)

    # List tables command
    _create_list_tables_parser(subparsers)

    # Validate command
    _create_validate_parser(subparsers)

    # Global options
    parser.add_argument("--version", action="version", version="plexos-db 0.2.0")

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Mostrar información detallada del procesamiento",
    )

    return parser


def _create_import_parser(subparsers) -> None:
    """Crea parser para comando import."""
    import_parser = subparsers.add_parser(
        "import",
        help="Importar datos PLEXOS desde ZIP a DuckDB",
        description="Importa datos desde un archivo ZIP de PLEXOS y crea base de datos DuckDB optimizada.",
    )

    import_parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Ruta al archivo ZIP de PLEXOS (requerido)",
    )

    import_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Ruta a la base de datos DuckDB de salida (requerido)",
    )

    import_parser.add_argument(
        "--xml-name",
        type=str,
        default="Model PRGdia_Full_Definitivo Solution.xml",
        help="Nombre del archivo XML dentro del ZIP (default: Model PRGdia_Full_Definitivo Solution.xml)",
    )

    import_parser.add_argument(
        "--chunk-size",
        type=int,
        default=10000,
        help="Tamaño de chunks para procesamiento (default: 10000)",
    )

    import_parser.add_argument(
        "--overwrite", action="store_true", help="Sobreescribir base de datos existente"
    )


def _create_list_tables_parser(subparsers) -> None:
    """Crea parser para comando list-tables."""
    list_parser = subparsers.add_parser(
        "list-tables",
        help="Listar tablas PLEXOS soportadas",
        description="Muestra todas las tablas PLEXOS que el sistema puede procesar.",
    )

    list_parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="Formato de salida (default: table)",
    )


def _create_validate_parser(subparsers) -> None:
    """Crea parser para comando validate."""
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validar archivo ZIP PLEXOS",
        description="Valida que un archivo ZIP PLEXOS tenga la estructura correcta sin procesar datos.",
    )

    validate_parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Ruta al archivo ZIP de PLEXOS a validar",
    )

    validate_parser.add_argument(
        "--xml-name",
        type=str,
        default="SolutionDataset.xml",
        help="Nombre del archivo XML a validar (default: SolutionDataset.xml)",
    )


def main(argv: Optional[List[str]] = None) -> int:
    """
    Entry point principal de CLI.

    Args:
        argv: Argumentos de línea de comandos (usa sys.argv si es None)

    Returns:
        Exit code (0 = éxito, 1 = error)
    """
    if argv is None:
        argv = sys.argv[1:]

    try:
        parser = create_parser()
        args = parser.parse_args(argv)

        # Configurar logging basado en argumentos
        log_level = "DEBUG" if args.verbose else "INFO"
        logger = setup_logging(log_level=log_level)
        logger.info(f"Iniciando PLEXOS-DB con comando: {args.command}")

        # Ejecutar comando correspondiente
        if args.command == "import":
            cmd = ImportCommand(args)
            return cmd.execute()
        elif args.command == "list-tables":
            cmd = ListTablesCommand(args)
            return cmd.execute()
        elif args.command == "validate":
            cmd = ValidateCommand(args)
            return cmd.execute()
        else:
            parser.error(f"Comando desconocido: {args.command}")

    except KeyboardInterrupt:
        logger = get_logger("cli")
        logger.info("Operación cancelada por el usuario")
        print("\nOperación cancelada por el usuario.")
        return 130
    except PLEXOSDBError as e:
        logger = get_logger("cli")
        logger.error(f"Error PLEXOS-DB: {e}")
        print(f"Error PLEXOS-DB: {e}")
        return 1
    except Exception as e:
        logger = get_logger("cli")
        logger.error(f"Error inesperado: {e}")
        verbose = "--verbose" in (argv or [])
        if verbose:
            logger.exception("Detalles del error:")
        print(f"Error inesperado: {e}")
        if verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
