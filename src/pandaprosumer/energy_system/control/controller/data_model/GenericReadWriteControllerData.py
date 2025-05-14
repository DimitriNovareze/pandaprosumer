from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pandaprosumer.element.element_toolbox import enforce_types


@enforce_types
@dataclass
class GenericReadWriteControllerData:
    element_name: str
    element_index: List[int]
    period_index: Optional[int] = None
    input_columns: List[str] = field(default_factory=list)
    result_columns: List[str] = field(default_factory=list)