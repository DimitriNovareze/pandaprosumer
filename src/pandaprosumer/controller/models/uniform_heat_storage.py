"""
Module containing the UniformHeatStorageController class.
"""

import numpy as np
import pandas as pd

from pandaprosumer.controller.base import BasicProsumerController


class UniformHeatStorageController(BasicProsumerController):
    """
    Controller for heat storage systems with uniform but evolving temperature.
    """

    @classmethod
    def name(cls):
        return "uniform_heat_storage"

    def __init__(self, prosumer, heat_storage_object, order, level, init_soc=0., init_temperature=60.0, in_service=True, index=None, **kwargs):
        """
        Initializes the UniformHeatStorageController.

        :param prosumer: The prosumer object
        :param heat_storage_object: The heat storage object
        :param order: The order of the controller
        :param level: The level of the controller
        :param init_soc: Initial state of charge
        :param init_temperature: Initial uniform temperature of the heat storage
        :param in_service: The in-service status of the controller
        :param index: The index of the controller
        :param kwargs: Additional keyword arguments
        """
        super().__init__(prosumer, heat_storage_object, order=order, level=level, in_service=in_service, index=index, **kwargs)
        self._soc = float(init_soc)
        self.temperature = init_temperature

    @property
    def _q_received_kw(self):
        return self._get_input("q_received_kw")

    def q_to_receive_kw(self, prosumer):
        """
        Calculates the heat to receive in kW.

        :param prosumer: The prosumer object
        :return: Heat to receive in kW
        """
        self.applied = False
        _q_capacity_kwh = self._get_element_param(prosumer, "q_capacity_kwh")
        fill_level_kwh = self._soc * _q_capacity_kwh
        q_to_receive_kwh = _q_capacity_kwh - fill_level_kwh
        for responder in self._get_generic_mapped_responders(prosumer):
            q_to_receive_kwh += responder.q_to_receive_kw(prosumer)
        return q_to_receive_kwh

    def q_to_deliver_kw(self, prosumer):
        """
        Calculates the heat to deliver in kW.

        :param prosumer: The prosumer object
        :return: Heat to deliver in kW
        """
        q_to_deliver_kw = 0.
        for responder in self._get_generic_mapped_responders(prosumer):
            q_to_deliver_kw += responder.q_to_receive_kw(prosumer)
        return q_to_deliver_kw

    def update_temperature(self, e_received_kwh, capacity_kwh):
        """
        Updates the uniform temperature based on received energy.

        :param e_received_kwh: Energy received in kWh
        :param capacity_kwh: Total capacity of the storage in kWh
        """
        cp = 4.18  # [kJ/kg·K]

        # Approximate volume from capacity (assuming ΔT of 1 K over full capacity)
        # 1 kWh = 3600 kJ => capacity_kwh * 3600 = m * cp * ΔT
        # So m = (capacity_kwh * 3600) / cp for ΔT = 1 K
        m = (capacity_kwh * 3600) / cp  # mass in kg
        if m > 0:
            delta_temp = (e_received_kwh * 3600) / (m * cp)
            self.temperature += delta_temp

    def control_step(self, prosumer):
        """
        Executes the control step for the controller.

        :param prosumer: The prosumer object
        """
        super().control_step(prosumer)
        q_to_deliver_kw = self.q_to_deliver_kw(prosumer)
        _q_capacity_kwh = self._get_element_param(prosumer, "q_capacity_kwh")
        e_received_kwh = self._q_received_kw * self.resol / 3600
        potential_kwh = self._soc * _q_capacity_kwh + e_received_kwh
        demand_kwh = q_to_deliver_kw * self.resol / 3600
        if demand_kwh > potential_kwh:
            demand_kwh = potential_kwh
        if not isinstance(demand_kwh, np.ndarray) and demand_kwh == 0:
            demand_kwh = np.array([0.]) / self.resol / 3600
        fill_level_kwh = potential_kwh - demand_kwh
        self._soc = fill_level_kwh / _q_capacity_kwh
        demand_kw = demand_kwh / (self.resol / 3600)

        # Update temperature
        self.update_temperature(e_received_kwh, _q_capacity_kwh)

        result = np.array([pd.Series(self._soc), pd.Series(demand_kw), pd.Series(self.temperature)])
        self.finalize(prosumer, result.T)
        self.applied = True