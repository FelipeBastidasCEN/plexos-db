"""XML utilities para procesamiento de PLEXOS.

Funciones extraídas de streaming_version.py y optimizadas para performance.
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
        result[strip_namespace(child.tag)] = (child.text or "").strip()
    return result