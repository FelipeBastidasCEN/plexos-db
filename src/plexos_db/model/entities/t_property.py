"""TProperty entity unificada.

Entity con metadata integrada que reemplaza TableSpec + dataclass separados.
"""

from dataclasses import dataclass
from typing import Optional, ClassVar
from .base_entity import BaseEntity, IntegerField, StringField, BooleanField


@dataclass(frozen=True, slots=True)
class TProperty(BaseEntity):
    """Entity para tabla t_property de PLEXOS con metadata integrada."""
    
    # --- Campos de datos (tipos para IDE/mypy) ---
    property_id: int
    collection_id: int
    enum_id: Optional[int]  # nullable (None -> NULL)
    name: str
    summary_name: str
    unit_id: int
    summary_unit_id: int
    is_multi_band: bool
    is_period: bool
    is_summary: bool
    lang_id: int
    
    # --- Metadata ClassVars ---
    row_tag: ClassVar[str] = "t_property"
    
    # ClassVar para fields metadata (requerido por BaseEntity)
    fields: ClassVar[dict] = {
        "property_id": IntegerField(required=True),
        "collection_id": IntegerField(required=True),
        "enum_id": IntegerField(required=False, default=None),
        "name": StringField(required=True),
        "summary_name": StringField(required=True),
        "unit_id": IntegerField(required=True),
        "summary_unit_id": IntegerField(required=True),
        "is_multi_band": BooleanField(required=True),
        "is_period": BooleanField(required=True),
        "is_summary": BooleanField(required=True),
        "lang_id": IntegerField(required=True),
    }
    
    # --- Métodos específicos de TProperty ---
    
    def __str__(self) -> str:
        """Representación legible."""
        return f"TProperty(id={self.property_id}, name='{self.name}', collection_id={self.collection_id})"
    
    @property
    def has_enum(self) -> bool:
        """Verifica si la propiedad tiene enumeración."""
        return self.enum_id is not None
    
    @property
    def is_time_varying(self) -> bool:
        """Verifica si la propiedad varía en tiempo."""
        return self.is_period
    
    @property 
    def is_aggregable(self) -> bool:
        """Verifica si la propiedad es agregable."""
        return self.is_summary
    
    def get_full_identifier(self) -> str:
        """Retorna identificador completo."""
        if self.has_enum:
            return f"{self.property_id}:{self.collection_id}:{self.enum_id}"
        return f"{self.property_id}:{self.collection_id}"