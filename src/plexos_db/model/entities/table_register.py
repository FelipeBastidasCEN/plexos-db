from typing import Any
from .t_object import TObject2
from .t_key import TKey


class TableRegister:
    SUPPORTED_TABLES: dict[str, Any] = {
        "t_object": TObject2,
        "t_key": TKey,
    }

    def __init__(self, schema: str):
        self.schema = schema

    @classmethod
    def get_table(cls, table_name: str) -> Any | None:
        if not cls.is_supported(table_name):
            return None
        return cls.SUPPORTED_TABLES[table_name]

    @classmethod
    def is_supported(cls, table_name: str) -> bool:
        return table_name in cls.SUPPORTED_TABLES.keys()
