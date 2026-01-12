from xml.etree.ElementTree import iterparse
from pathlib import Path

xml_name = Path(r"test.xml")


def strip_namespace(tag: str) -> str:
    """
    Remueve namespace default de un tag XML.

    Ejemplo: '{ns}t_object' -> 't_object'

    Args:
        tag: Tag XML con posible namespace

    Returns:
        Tag local sin namespace
    """
    return tag.split("}", 1)[-1]


with xml_name.open("rb") as f:
    for _, elem in iterparse(f, events=("end",)):
        tag = strip_namespace(elem.tag)
        text = elem.text
        print(tag, text)
