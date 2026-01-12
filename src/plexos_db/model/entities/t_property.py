"""TProperty entity - Dataclass puro para PLEXOS.

Entity para tabla t_property con validación de tipos.
Solo definición de datos sin lógica de procesamiento.
"""

from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class TProperty:
    """Entity para tabla t_property de PLEXOS.
    
    Contiene solo datos, sin lógica de procesamiento o validación.
    """
    property_id: int
    collection_id: int
    enum_id: int | None  # nullable (None -> NULL)
    name: str
    summary_name: str
    unit_id: int
    summary_unit_id: int
    is_multi_band: bool
    is_period: bool
    is_summary: bool
    lang_id: int

    def __post_init__(self) -> None:
        """Validación básica de tipos."""
        if not isinstance(self.property_id, int):
            raise TypeError("property_id debe ser int")
        if not isinstance(self.collection_id, int):
            raise TypeError("collection_id debe ser int")
        if self.enum_id is not None and not isinstance(self.enum_id, int):
            raise TypeError("enum_id debe ser int o None")
        if not isinstance(self.name, str):
            raise TypeError("name debe ser str")
        if not isinstance(self.summary_name, str):
            raise TypeError("summary_name debe ser str")
        if not isinstance(self.unit_id, int):
            raise TypeError("unit_id debe ser int")
        if not isinstance(self.summary_unit_id, int):
            raise TypeError("summary_unit_id debe ser int")
        if not isinstance(self.is_multi_band, bool):
            raise TypeError("is_multi_band debe ser bool")
        if not isinstance(self.is_period, bool):
            raise TypeError("is_period debe ser bool")
        if not isinstance(self.is_summary, bool):
            raise TypeError("is_summary debe ser bool")
        if not isinstance(self.lang_id, int):
            raise TypeError("lang_id debe ser int")

    @classmethod
    def from_dict(cls, data: dict) -> Self:
        """Crea instancia desde diccionario."""
        return cls(
            property_id=data.get("property_id", 0),
            collection_id=data.get("collection_id", 0),
            enum_id=data.get("enum_id"),
            name=data.get("name", ""),
            summary_name=data.get("summary_name", ""),
            unit_id=data.get("unit_id", 0),
            summary_unit_id=data.get("summary_unit_id", 0),
            is_multi_band=data.get("is_multi_band", False),
            is_period=data.get("is_period", False),
            is_summary=data.get("is_summary", False),
            lang_id=data.get("lang_id", 0)
        )

    def to_dict(self) -> dict:
        """Convierte a diccionario."""
        return {
            "property_id": self.property_id,
            "collection_id": self.collection_id,
            "enum_id": self.enum_id,
            "name": self.name,
            "summary_name": self.summary_name,
            "unit_id": self.unit_id,
            "summary_unit_id": self.summary_unit_id,
            "is_multi_band": self.is_multi_band,
            "is_period": self.is_period,
            "is_summary": self.is_summary,
            "lang_id": self.lang_id
        }