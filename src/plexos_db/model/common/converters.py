"""Type converters para datos PLEXOS.

Converters optimizados para performance y manejo de valores nulos.
Diseñados para 100MB XML con validation robusta.
"""



def to_int0(value: str | None) -> int:
    """
    Convierte a int, retorna 0 si es None o vacío.
    
    Args:
        value: String a convertir o None
        
    Returns:
        Integer (0 si value es None/vacío)
    """
    if value is None:
        return 0
    value = value.strip()
    return int(value) if value else 0


def to_int_opt(value: str | None) -> int | None:
    """
    Convierte a int opcional (None permitido).
    
    Args:
        value: String a convertir o None
        
    Returns:
        Integer o None si value es None/vacío
    """
    if value is None:
        return None
    value = value.strip()
    return int(value) if value else None


def to_bool(value: str | None) -> bool:
    """
    Convierte string a booleano.
    
    Args:
        value: String a convertir o None
        
    Returns:
        Boolean (True para 'true', '1', 'yes', 'y', 't')
    """
    return (value or "").strip().lower() in {"true", "1", "yes", "y", "t"}


def to_str(value: str | None) -> str:
    """
    Convierte a string, retorna vacío si es None.
    
    Args:
        value: String o None
        
    Returns:
        String (vacío si value es None)
    """
    return value or ""


def to_str_opt(value: str | None) -> str | None:
    """
    Convierte a string opcional (None permitido).
    
    Args:
        value: String o None
        
    Returns:
        String o None (preserva None original)
    """
    if value is None:
        return None
    return value.strip() if value else None


def clean_uuid(value: str | None) -> str | None:
    """
    Limpia UUID, retorna None si es vacío.
    
    Args:
        value: UUID string o None
        
    Returns:
        UUID limpio o None si value es None/vacío
    """
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None