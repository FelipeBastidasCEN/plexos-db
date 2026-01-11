from typing import NamedTuple, Self
from xml.etree import ElementTree as ET
from dataclasses import dataclass
import pyarrow as pa


# Arrow schema for TObject table
TOBJECT_SCHEMA = pa.schema([
    ('object_id', pa.int32()),
    ('class_id', pa.int32()),
    ('name', pa.string()),
    ('category_id', pa.int32()),
    ('description', pa.string()),
    ('guid', pa.string())
])


class ArrowTableBuilder:
    """Builder for creating Arrow tables incrementally."""
    
    def __init__(self, schema: pa.Schema, chunk_size: int = 1000):
        self.schema = schema
        self.chunk_size = chunk_size
        self._chunks = []
        self._current_data = {field.name: [] for field in schema}
    
    def add_row(self, **kwargs) -> None:
        """Add a single row to the current chunk."""
        for field_name in self.schema.names:
            value = kwargs.get(field_name)
            self._current_data[field_name].append(value)
        
        # Check if we need to create a new chunk
        if len(self._current_data[self.schema.names[0]]) >= self.chunk_size:
            self._create_chunk()
    
    def _create_chunk(self) -> None:
        """Create an Arrow chunk from current data."""
        if not self._current_data[self.schema.names[0]]:
            return
        
        chunk = pa.Table.from_pydict(self._current_data, schema=self.schema)
        self._chunks.append(chunk)
        
        # Reset current data
        self._current_data = {field.name: [] for field in self.schema}
    
    def finish(self) -> pa.Table:
        """Finalize and return the complete Arrow table."""
        self._create_chunk()  # Add any remaining data
        
        if not self._chunks:
            return pa.Table.from_pydict({name: [] for name in self.schema.names}, schema=self.schema)
        
        return pa.concat_tables(self._chunks)


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
        object_id_text = element.findtext("{*}object_id")
        class_id_text = element.findtext("{*}class_id")
        name_text = element.findtext("{*}name")
        category_id_text = element.findtext("{*}category_id")
        
        if object_id_text is None or class_id_text is None or name_text is None or category_id_text is None:
            raise ValueError("Required XML elements are missing")
            
        return cls(
            object_id=int(object_id_text),
            class_id=int(class_id_text),
            name=name_text,
            category_id=int(category_id_text),
            description=element.findtext("{*}description"),
            guid=element.findtext("{*}GUID"),
        )

    @staticmethod
    def parse_to_arrow(xml_source, chunk_size: int = 1000) -> pa.Table:
        """
        Parse XML source to Arrow table using streaming approach.
        
        Args:
            xml_source: Can be file path, file-like object, or ET.Element
            chunk_size: Number of rows per chunk for memory management
            
        Returns:
            Arrow table with parsed data
        """
        builder = ArrowTableBuilder(TOBJECT_SCHEMA, chunk_size)
        
        # Handle different input types
        if isinstance(xml_source, ET.Element):
            # Parse from existing Element
            elements = xml_source.findall(".//{*}t_object")
            for elem in elements:
                TObject._process_element_to_arrow(elem, builder)
        else:
            # Parse from file or file-like object using streaming
            context = ET.iterparse(xml_source, events=('end',))
            for event, elem in context:
                if elem.tag.endswith('t_object'):
                    TObject._process_element_to_arrow(elem, builder)
                    elem.clear()  # Free memory
        
        return builder.finish()
    
    @staticmethod
    def _process_element_to_arrow(element: ET.Element, builder: ArrowTableBuilder) -> None:
        """Process a single XML element and add to Arrow builder."""
        object_id_text = element.findtext("{*}object_id")
        class_id_text = element.findtext("{*}class_id")
        name_text = element.findtext("{*}name")
        category_id_text = element.findtext("{*}category_id")
        
        # Skip if required fields are missing
        if object_id_text is None or class_id_text is None or name_text is None or category_id_text is None:
            return
        
        builder.add_row(
            object_id=int(object_id_text),
            class_id=int(class_id_text),
            name=name_text,
            category_id=int(category_id_text),
            description=element.findtext("{*}description"),
            guid=element.findtext("{*}GUID")
        )
