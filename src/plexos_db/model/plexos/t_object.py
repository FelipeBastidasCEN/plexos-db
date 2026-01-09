from typing import NamedTuple, Self
from xml.etree import ElementTree as ET
from dataclasses import dataclass


@dataclass(frozen=True)
class TObject:
    object_id: int
    class_id: int
    name: str
    category_id: int
    description: str | None
    guid: str | None

    @classmethod
    def from_element(cls, element: ET.Element) -> Self:
        """
        Crea un objecto TObject desde un elemento XML.
        Solo description y guid son opcionales.
        """
        return cls(
            object_id=int(element.findtext("{*}object_id")),
            class_id=int(element.findtext("{*}class_id")),
            name=element.findtext("{*}name"),
            category_id=int(element.findtext("{*}category_id")),
            description=element.findtext("{*}description"),
            guid=element.findtext("{*}GUID"),
        )
