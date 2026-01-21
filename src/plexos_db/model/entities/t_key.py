from typing import NamedTuple, Self
from xml.etree.ElementTree import Element

import pyarrow as pa


class TKey(NamedTuple):
    key_id: int
    membership_id: int
    phase_id: int
    property_id: int
    period_type_id: int

    @classmethod
    def from_element(cls, element: Element) -> Self:
        return cls(
            key_id=int(element.findtext("{*}key_id")),
            membership_id=int(element.findtext("{*}membership_id")),
            phase_id=int(element.findtext("{*}phase_id")),
            property_id=int(element.findtext("{*}property_id")),
            period_type_id=int(element.findtext("{*}period_type_id")),
        )

    def schema(self) -> pa.schema:
        return pa.schema(
            [
                pa.field("key_id", pa.int64()),
                pa.field("membership_id", pa.int64()),
                pa.field("phase_id", pa.int64()),
                pa.field("property_id", pa.int64()),
                pa.field("period_type_id", pa.int64()),
            ]
        )

    @property
    def table_name(self) -> str:
        return "t_key"
