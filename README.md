# PLEXOS-DB

Aplicación CLI para convertir una salida PLEXOS (ZIP) en una base de datos DuckDB optimizada, utilizando streaming para procesamiento eficiente de archivos XML grandes (hasta 100MB).

## Arquitectura

El proyecto implementa una arquitectura de 3 capas con validación manual y stack minimalista:

```
CLI Layer → Business Layer → Model Layer
    ↓              ↓              ↓
Interfaz    → Procesamiento → Almacenamiento
Usuario      + Validación     + DuckDB
```

### Estructura del Proyecto

```
plexos-db/
├── src/plexos_db/
│   ├── cli/                          # CLI Layer - Interfaz de usuario
│   │   ├── __init__.py
│   │   ├── main.py                   # Parser argparse y entry point
│   │   └── commands.py                # Comandos CLI
│   ├── business/                     # Business Layer - Lógica de procesamiento
│   │   ├── __init__.py
│   │   ├── processors/               # Procesamiento de datos
│   │   │   ├── __init__.py
│   │   │   ├── xml_processor.py      # Streaming XML parser
│   │   │   └── validators.py         # Validación manual optimizada
│   │   └── services/                 # Servicios de orquestación
│   │       ├── __init__.py
│   │       └── import_service.py      # Servicio principal de importación
│   └── model/                        # Model Layer - Definiciones y almacenamiento
│       ├── entities/                  # Dataclasses puros
│       │   ├── __init__.py
│       │   ├── t_object.py           # Entity t_object
│       │   ├── t_property.py         # Entity t_property
│       │   └── all_entities.py       # Registry de entidades
│       ├── schemas/                    # Table specifications
│       │   ├── __init__.py
│       │   ├── base.py                # Clase TableSpec base
│       │   ├── t_object_schema.py     # TableSpec para t_object
│       │   ├── t_property_schema.py   # TableSpec para t_property
│       │   └── schema_registry.py     # Registry validado de schemas
│       ├── storage/                   # Almacenamiento DuckDB
│       │   ├── __init__.py
│       │   ├── connection.py          # Gestión de conexiones
│       │   ├── schema_manager.py      # Creación dinámica de tablas
│       │   └── bulk_loader.py         # Inserción optimizada por chunks
│       └── common/                    # Utilidades compartidas
│           ├── __init__.py
│           ├── converters.py          # Type converters
│           ├── xml_utils.py           # XML parsing utilities
│           └── exceptions.py          # Custom exceptions
├── config/                            # Configuración (futura)
│   ├── schemas.yaml                  # Definiciones de tablas extensibles
│   └── default.yaml                  # Configuración por defecto
├── reports/                          # Reports y views (futura)
│   ├── views/                         # Archivos .sql para vistas
│   └── queries/                       # Archivos .sql para reportes
├── streaming_version.py               # Legacy - será eliminado
├── pyproject.toml                    # Configuración del proyecto
└── README.md                         # Esta documentación
```

## Uso

### CLI Básica

```bash
plexos-db import --input path/to/solution.zip --output path/to/database.duckdb
```

### Argumentos

- `--input, -i`: Ruta al archivo ZIP de PLEXOS (requerido)
- `--output, -o`: Ruta a la base de datos DuckDB de salida (requerido)
- `--xml-name`: Nombre del archivo XML dentro del ZIP (default: "SolutionDataset.xml")
- `--chunk-size`: Tamaño de chunks para procesamiento (default: 10_000)

### Ejemplo completo

```bash
plexos-db import \
  --input "/data/solutions/solution_2024.zip" \
  --output "/data/processed/solution_2024.duckdb" \
  --xml-name "SolutionDataset.xml" \
  --chunk-size 20_000
```

## Plan de Implementación

El proyecto está migrando desde `streaming_version.py` a la arquitectura de 3 capas. El plan se ejecuta secuencialmente:

### Fase 1: Limpieza y Fundación (Días 1-3)
- **Día 1**: Preparación del entorno y creación de estructura
- **Día 2**: Migración de utilidades core desde `streaming_version.py`
- **Día 3**: Validación foundation y limpieza de código viejo

### Fase 2: Model Layer Completo (Días 4-7)
- **Día 4**: Entities refactoring (100% rewrite)
- **Día 5-6**: Schemas y storage layer
- **Día 7**: Model integration y testing

### Fase 3: Business Layer (Días 8-11)
- **Día 8-9**: XML processing engine optimizado
- **Día 10**: Service layer implementation
- **Día 11**: Business layer testing

### Fase 4: CLI Layer (Días 12-14)
- **Día 12-13**: CLI implementation desde cero
- **Día 14**: CLI integration y testing

### Fase 5: Finalización (Días 15-16)
- **Día 15**: Integration final y cleanup
- **Día 16**: Ready for user testing

### Fase 6: Preparación Futura (Post-implementación)
- Sistema de logging (warnings tablas desconocidas)
- Sistema de .sql views para reports
- Preparación para decodificación binaria con t_key_index

## Comportamiento Definido

### Validación y Errores
- **Tablas desconocidas en XML**: Ignoradas silenciosamente (logging futuro)
- **Columnas faltantes no opcionales**: Error con mensaje claro
- **Errores de estructura**: Error descriptivo con contexto

### Performance
- **Streaming**: Procesamiento con baja memoria para archivos hasta 100MB
- **Chunk loading**: Inserción por batches optimizada para DuckDB
- **Validation manual**: Sin overhead de frameworks para máxima velocidad

## Características Técnicas

### Stack Minimalista
- **Dependencies**: Solo DuckDB + PyArrow
- **Validation**: Manual optimizada (no Pydantic)
- **Processing**: Streaming XML con memory management
- **Database**: DuckDB con inserción masiva

### Extensibilidad Futura
- **Dynamic schemas**: Soporte para <20 tablas vía registry
- **SQL views**: Sistema simple de archivos .sql para reports
- **Binary processing**: Preparado para decodificación con t_key_index
- **Logging**: Hooks para sistema de logs completo

## Development

### Prerrequisitos
- Python 3.13+
- DuckDB 1.4.3+
- PyArrow 22.0.0+

### Instalación
```bash
pip install -e .
```

### Testing
```bash
python -m pytest src/tests/
```

## Roadmap

- [x] Streaming XML parser con chunk loading
- [x] Validación manual optimizada  
- [ ] Arquitectura de 3 capas completa
- [ ] CLI con argumentos completos
- [ ] Sistema de logging integrado
- [ ] Soporte para .sql views y reports
- [ ] Decodificación binaria con t_key_index
