"""TObject entity - Dataclass puro para PLEXOS.

Refactorizado desde versión original, eliminando toda lógica de procesamiento y Arrow.
Solo definición de datos sin comportamiento.
"""

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class TObject:
    """Entity para tabla t_object de PLEXOS.
    
    Contiene solo datos, sin lógica de procesamiento o validación.
    """
    object_id: int
    class_id: int
    name: str
    category_id: int
    description: str | None = None
    guid: str | None = None

    def __post_init__(self) -> None:
        """Validación básica de tipos."""
        if not isinstance(self.object_id, int):
            raise TypeError("object_id debe ser int")
        if not isinstance(self.class_id, int):
            raise TypeError("class_id debe ser int")
        if not isinstance(self.name, str):
            raise TypeError("name debe ser str")
        if not isinstance(self.category_id, int):
            raise TypeError("category_id debe ser int")

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Crea instancia desde diccionario."""
        return cls(
            object_id=data.get("object_id", 0),
            class_id=data.get("class_id", 0),
            name=data.get("name", ""),
            category_id=data.get("category_id", 0),
            description=data.get("description"),
            guid=data.get("guid")
        )

    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "object_id": self.object_id,
            "class_id": self.class_id,
            "name": self.name,
            "category_id": self.category_id,
            "description": self.description,
            "guid": self.guid
        }