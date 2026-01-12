"""XML utilities para procesamiento de PLEXOS.

Funciones optimizadas para performance con archivos XML grandes.
Memory management para procesamiento de 100MB XML.
"""

from xml.etree.ElementTree import Element


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


def extract_children_text(elem: Element) -> dict[str, str]:
    """
    Extrae texto de elementos hijos directos.

    Args:
        elem: Elemento XML padre

    Returns:
        Diccionario {tag_local: text_stripped}
    """
    result: dict[str, str] = {}
    for child in list(elem):
        tag_name: str = strip_namespace(child.tag)
        text_value: str = child.text
        result[tag_name] = (text_value or "").strip()
    return result
