from dataclasses import dataclass
from typing import Self
from xml.etree import ElementTree as ET
from array import array
from pathlib import Path
from zipfile import ZipFile

from plexos_db.model.plexos.t_object import TObject

BIN_NAME: str = "t_data_0.BIN"


@dataclass
class ApiPlexos:
    xml: ET.Element
    bin: array[float]

    @classmethod
    def from_zip(cls, zip_path: Path) -> Self:
        assert zip_path.exists(), f"ERROR: file does not exists: {zip_path}"
        assert zip_path.suffix == ".zip", f"ERROR: file is not zipfile: {zip_path}"

        with ZipFile(zip_path) as zip_file:
            # procesando XML
            xml_name: str = zip_path.with_suffix(".xml").name
            with zip_file.open(xml_name, "r") as zip_xml:
                tree_xml: ET.ElementTree = ET.parse(zip_xml)
                xml_root: ET.Element = tree_xml.getroot()

            # procesando BIN
            # Se hace check % 8 dado que deberia ser un vector de doubles.
            zip_bin: bytes = zip_file.read(BIN_NAME, "rb")
            if len(zip_bin) % 8 != 0:
                raise ValueError(f"ERROR: bin file with wrong size: {len(zip_bin)}")

            arr: array[float] = array("d")
            arr.frombytes(zip_bin)

        return cls(xml=xml_root, bin=arr)

    def t_object(self) -> list[TObject]:
        search_path: str = ".//{*}t_object"
        elements: list[ET.Element] = self.xml.findall(search_path)
        assert len(elements) >= 1, "ERRPR: no t_object table in XML."
        return [TObject.from_element(elem) for elem in elements]
