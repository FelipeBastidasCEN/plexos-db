"""CLI commands implementation.

Comandos CLI para PLEXOS-DB con integration con Business Layer.
"""

import json
import sys
from typing import Dict, Any

from ..business.services.import_service import ImportService
from ..business.processors.validators import FileValidator
from ..model.schemas.schema_registry import SchemaRegistry
from ..model.common.exceptions import PLEXOSDBError


class BaseCommand:
    """Clase base para comandos CLI."""

    def __init__(self, args):
        """
        Inicializa comando con argumentos parseados.

        Args:
            args: Argumentos de argparse
        """
        self.args = args
        self.verbose = getattr(args, "verbose", False)

    def _print(self, message: str, force: bool = False) -> None:
        """
        Imprime mensaje según modo verbose.

        Args:
            message: Mensaje a imprimir
            force: Si fuerza impresión independientemente de verbose
        """
        if self.verbose or force:
            print(message)

    def _print_error(self, message: str) -> None:
        """Imprime mensaje de error."""
        print(f"ERROR: {message}", file=sys.stderr)

    def _print_success(self, message: str) -> None:
        """Imprime mensaje de éxito."""
        print(f"✅ {message}")


class ImportCommand(BaseCommand):
    """Comando para importar datos PLEXOS."""

    def execute(self) -> int:
        """
        Ejecuta comando de importación.

        Returns:
            Exit code (0 = éxito, 1 = error)
        """
        try:
            self._print(f"Iniciando importación desde {self.args.input}")
            self._print(f"Salida: {self.args.output}")
            self._print(f"XML: {self.args.xml_name}")
            self._print(f"Chunk size: {self.args.chunk_size}")

            # Validar dry run
            if self.args.dry_run:
                self._print("MODO DRY RUN - Solo validación")
                return self._validate_only()

            # Crear servicio de importación
            import_service = ImportService()

            # Ejecutar importación
            result = import_service.import_plexos_data(
                zip_path=self.args.input,
                db_path=self.args.output,
                xml_name=self.args.xml_name,
                chunk_size=self.args.chunk_size,
                overwrite=self.args.overwrite,
            )

            # Mostrar resultados
            self._show_import_results(result)
            self._print_success("Importación completada exitosamente")

            return 0

        except PLEXOSDBError as e:
            self._print_error(f"Error PLEXOS-DB: {e}")
            return 1
        except Exception as e:
            self._print_error(f"Error inesperado: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()
            return 1

    def _validate_only(self) -> int:
        """Valida archivos sin procesar (dry run)."""
        try:
            FileValidator.validate_zip_path(self.args.input)
            FileValidator.validate_db_path(self.args.output)
            FileValidator.validate_xml_name(self.args.xml_name)

            self._print_success("Validación exitosa - archivos listos")
            return 0

        except PLEXOSDBError as e:
            self._print_error(f"Error de validación: {e}")
            return 1

    def _show_import_results(self, result: Dict[str, Any]) -> None:
        """Muestra resultados de importación."""
        import_stats = result.get("import_stats", {})
        bulk_stats = result.get("bulk_stats", {})

        self._print("\n📊 Estadísticas de Importación:")
        self._print(f"  Total filas procesadas: {import_stats.get('total_rows', 0)}")

        rows_by_table = import_stats.get("rows_by_table", {})
        if rows_by_table:
            self._print("  Filas por tabla:")
            for table, count in rows_by_table.items():
                self._print(f"    {table}: {count}")

        if bulk_stats:
            self._print("  Estadísticas bulk:")
            for table, count in bulk_stats.items():
                self._print(f"    {table}: {count} filas en buffer")


class ListTablesCommand(BaseCommand):
    """Comando para listar tablas soportadas."""

    def execute(self) -> int:
        """
        Ejecuta comando list-tables.

        Returns:
            Exit code (0 = éxito, 1 = error)
        """
        try:
            schema_registry = SchemaRegistry()
            tables = schema_registry.get_all_table_names()

            if self.args.format == "table":
                self._show_table_format(tables)
            elif self.args.format == "json":
                self._show_json_format(tables)
            elif self.args.format == "csv":
                self._show_csv_format(tables)

            self._print_success(f"Listadas {len(tables)} tablas soportadas")
            return 0

        except PLEXOSDBError as e:
            self._print_error(f"Error PLEXOS-DB: {e}")
            return 1
        except Exception as e:
            self._print_error(f"Error inesperado: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()
            return 1

    def _show_table_format(self, tables: list[str]) -> None:
        """Muestra tablas en formato tabla."""
        self._print("Tablas PLEXOS soportadas:")
        self._print("=" * 40)
        for table in tables:
            self._print(f"  📄 {table}")
        self._print("=" * 40)

    def _show_json_format(self, tables: list[str]) -> None:
        """Muestra tablas en formato JSON."""
        data = {"supported_tables": tables, "count": len(tables)}
        print(json.dumps(data, indent=2))

    def _show_csv_format(self, tables: list[str]) -> None:
        """Muestra tablas en formato CSV."""
        print("table_name")
        for table in tables:
            print(table)


class ValidateCommand(BaseCommand):
    """Comando para validar archivos ZIP."""

    def execute(self) -> int:
        """
        Ejecuta comando validate.

        Returns:
            Exit code (0 = éxito, 1 = error)
        """
        try:
            self._print(f"Validando archivo: {self.args.input}")
            self._print(f"XML objetivo: {self.args.xml_name}")

            # Validar archivo ZIP
            FileValidator.validate_zip_path(self.args.input)
            FileValidator.validate_xml_name(self.args.xml_name)

            # Intentar leer XML básico
            from zipfile import ZipFile
            from xml.etree.ElementTree import iterparse

            with ZipFile(self.args.input) as zf:
                file_list = zf.namelist()
                if self.args.xml_name not in file_list:
                    self._print_error(
                        f"Archivo XML no encontrado en ZIP: {self.args.xml_name}"
                    )
                    return 1

                self._print(f"Archivos en ZIP: {len(file_list)}")
                self._print(f"XML encontrado: {self.args.xml_name}")

                # Validar estructura básica del XML
                with zf.open(self.args.xml_name, "r") as f:
                    elem_count = 0
                    table_tags = set()

                    for _, elem in iterparse(f, events=("end",)):
                        elem_count += 1
                        tag = elem.tag.split("}", 1)[-1]  # Remover namespace
                        table_tags.add(tag)
                        elem.clear()

                        if elem_count % 10000 == 0:
                            self._print(f"  Procesados: {elem_count} elementos")

                    self._print(f"Total elementos XML: {elem_count}")
                    self._print(f"Tablas encontradas: {len(table_tags)}")

                    schema_registry = SchemaRegistry()
                    supported = schema_registry.get_all_table_names()
                    unknown = [t for t in table_tags if t not in supported]

                    if unknown:
                        self._print(f"⚠️  Tablas desconocidas: {unknown}")
                        self._print(
                            f"✅ Tablas soportadas: {[t for t in table_tags if t in supported]}"
                        )
                    else:
                        self._print_success("Todas las tablas son soportadas")

            self._print_success("Validación completada exitosamente")
            return 0

        except PLEXOSDBError as e:
            self._print_error(f"Error PLEXOS-DB: {e}")
            return 1
        except Exception as e:
            self._print_error(f"Error inesperado: {e}")
            if self.verbose:
                import traceback

                traceback.print_exc()
            return 1
