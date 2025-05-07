from dataclasses import dataclass, field
from typing import List

@dataclass
class UniformHeatStorageControllerData:
    """
    Data class for a heat storage controller with uniform temperature.

    Attributes
    ----------
    element_index : List[int]
        List of element indices.
    input_columns : List[str]
        List of input column names.
    result_columns : List[str]
        List of result column names.
    period_index : int, optional
        Index of the period, default is None.
    element_name : str
        Name of the element.
    uniform_temperature : float
        The uniform temperature of the heat storage.
    """
    element_index: List[int]
    element_name: str = 'uniform_heat_storage'
    period_index: int = None
    input_columns: List[str] = field(default_factory=lambda: ["q_received_kw"])
    result_columns: List[str] = field(default_factory=lambda: ["soc", "q_delivered_kw"])
    uniform_temperature: float = 60.0  # Default uniform temperature in Celsius