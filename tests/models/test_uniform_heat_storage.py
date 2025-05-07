import pytest
from pandaprosumer import *


def _default_argument():
    return {"q_capacity_kwh": 100}


def _default_period(prosumer):
    return create_period(prosumer, 1,
                         name="foo",
                         start="2020-01-01 00:00:00",
                         end="2020-01-01 11:59:59",
                         timezone="utc")


class TestUniformHeatStorage:
    """
    Tests the functionalities of a SHS element and controller
    """

    def test_define_element(self):
        """
        Test the creation of a  heat storage element in a prosumer container with default parameters values
        """
        prosumer = create_empty_prosumer_container()
        create_period(prosumer, 1)

        uhs_params = {}

        create_uniform_heat_storage(prosumer, **uhs_params)
        assert hasattr(prosumer, "uniform_heat_storage")
        assert len(prosumer.uniform_heat_storage) == 1

        expected_columns = ['name', 'q_capacity_kwh', 'in_service']
        expected_values = [None, True, 0]

        assert sorted(prosumer.uniform_heat_storage.columns) == sorted(expected_columns)
        assert prosumer.uniform_heat_storage.iloc[0].values == pytest.approx(expected_values, nan_ok=True)

    def test_define_element_param(self):
        """
        Test the creation of a  heat storage element in a prosumer container with custom parameters values
        """
        prosumer = create_empty_prosumer_container()
        create_period(prosumer, 1)

        uhs_params = {"q_capacity_kwh": 100}

        uhs_idx = create_uniform_heat_storage(prosumer, name='foo', in_service=False, custom='test', index=4, **uhs_params)
        assert hasattr(prosumer, "uniform_heat_storage")
        assert len(prosumer.uniform_heat_storage) == 1
        assert uhs_idx == 4
        assert prosumer.uniform_heat_storage.index[0] == uhs_idx

        expected_columns = ['name', 'q_capacity_kwh', 'in_service', 'custom']
        expected_values = ['foo', False, 100, 'test']

        assert sorted(prosumer.uniform_heat_storage.columns) == sorted(expected_columns)
        assert prosumer.uniform_heat_storage.iloc[0].values == pytest.approx(expected_values)

    def test_define_controller(self):
        """
        Test the creation of a  heat storage controller in a prosumer container
        """
        prosumer = create_empty_prosumer_container()
        create_controlled_uniform_heat_storage(prosumer,
                                       order=0,
                                       period=_default_period(prosumer),
                                       **_default_argument())

        assert hasattr(prosumer, "controller")
        assert len(prosumer.controller) == 1

    def test_controller_columns(self):
        """
        Check that the input and result columns of the  heat storage controller are the one expected
        """
        prosumer = create_empty_prosumer_container()
        shs_controller_idx = create_controlled_uniform_heat_storage(prosumer,
                                                            order=0,
                                                            period=_default_period(prosumer),
                                                            **_default_argument())
        shs_controller = prosumer.controller.iloc[shs_controller_idx].object

        input_columns_expected = ["q_received_kw"]
        result_columns_expected = ["soc", "q_delivered_kw"]

        assert shs_controller.input_columns == input_columns_expected
        assert shs_controller.result_columns == result_columns_expected

    def test_controller_run_control_no_demand(self):
        """
        Test the control step of the controller with no demand
        """
        prosumer = create_empty_prosumer_container()
        uhs_controller_idx = create_controlled_uniform_heat_storage(prosumer,
                                                            order=0,
                                                            period=_default_period(prosumer),
                                                            **_default_argument())
        uhs_controller = prosumer.controller.iloc[uhs_controller_idx].object

        q_in_kw = 0
        q_out_kw = 0
        uhs_controller.inputs = np.array([[q_in_kw]])
        uhs_controller.q_to_deliver_kw = lambda x: q_out_kw
        uhs_controller.time_step(prosumer, "2020-01-01 00:00:00")
        uhs_controller.control_step(prosumer)

        soc = (q_in_kw - q_out_kw) * uhs_controller.resol / 3600 / 100
        expected = [soc, q_out_kw]
        assert uhs_controller.step_results == pytest.approx(np.array([expected]))

    def test_controller_run_control_charge(self):
        """
        Test the control step of the controller with no demand
        """
        prosumer = create_empty_prosumer_container()
        uhs_controller_idx = create_controlled_uniform_heat_storage(prosumer,
                                                            order=0,
                                                            period=_default_period(prosumer),
                                                            **_default_argument())
        uhs_controller = prosumer.controller.iloc[uhs_controller_idx].object

        q_in_kw = 10
        q_out_kw = 0
        uhs_controller.inputs = np.array([[q_in_kw]])
        uhs_controller.q_to_deliver_kw = lambda x: q_out_kw
        uhs_controller.time_step(prosumer, "2020-01-01 00:00:00")
        uhs_controller.control_step(prosumer)

        soc = (q_in_kw - q_out_kw) * uhs_controller.resol / 3600 / 100
        expected = [soc, q_out_kw]
        assert uhs_controller.step_results == pytest.approx(np.array([expected]))

    def test_controller_run_control_discharge(self):
        """
        Test the control step of the controller with no demand
        """
        prosumer = create_empty_prosumer_container()
        uhs_controller_idx = create_controlled_heat_storage(prosumer,
                                                            order=0,
                                                            period=_default_period(prosumer),
                                                            init_soc=0.5,
                                                            **_default_argument())
        uhs_controller = prosumer.controller.iloc[uhs_controller_idx].object

        q_in_kw = 10
        q_out_kw = 100
        uhs_controller.inputs = np.array([[q_in_kw]])
        uhs_controller.q_to_deliver_kw = lambda x: q_out_kw
        uhs_controller.time_step(prosumer, "2020-01-01 00:00:00")
        uhs_controller.control_step(prosumer)

        soc = 0.5 + (q_in_kw - q_out_kw) * uhs_controller.resol / 3600 / 100
        expected = [soc, q_out_kw]
        assert uhs_controller.step_results == pytest.approx(np.array([expected]))

    def test_controller_run_control_overcharge(self):
        """
        Test the control step of the controller with no demand
        """
        prosumer = create_empty_prosumer_container()
        uhs_controller_idx = create_controlled_heat_storage(prosumer,
                                                            order=0,
                                                            period=_default_period(prosumer),
                                                            init_soc=0.5,
                                                            **_default_argument())
        uhs_controller = prosumer.controller.iloc[uhs_controller_idx].object

        q_in_kw = 1e6
        q_out_kw = 1000
        uhs_controller.inputs = np.array([[q_in_kw]])
        uhs_controller.q_to_deliver_kw = lambda x: q_out_kw
        uhs_controller.time_step(prosumer, "2020-01-01 00:00:00")

        with pytest.raises(ValueError):
            uhs_controller.control_step(prosumer)

        # Case where the extra charge would be added to output of the storage instead of raising an exception
        # capacity_kwh = 100
        # soc = 0.5 - (q_in_kw - q_out_kw) * shs_controller.resol / 3600 / 100
        # overcharge_kwh = (1 - soc) * capacity_kwh
        # soc = 1
        # q_out_kw += (overcharge_kwh - capacity_kwh) * 3600 / shs_controller.resol
        # expected = [soc, q_out_kw]
        # assert shs_controller.step_results == pytest.approx(np.array([expected]))

    def test_controller_t_m_to_receive(self):
        prosumer = create_empty_prosumer_container()
        period = create_period(prosumer, 1,
                               name="foo",
                               start="2020-01-01 00:00:00",
                               end="2020-01-01 00:00:09",
                               timezone="utc")
        q_capacity_kwh = 100
        init_soc = 0.4
        uhs_params = {"q_capacity_kwh": q_capacity_kwh}

        uhs_controller_indx = create_controlled_heat_storage(prosumer, init_soc=init_soc, period=period, **uhs_params)
        uhs_controller = prosumer.controller.iloc[uhs_controller_indx].object

        q_to_fill_kwh = (1-init_soc) * q_capacity_kwh
        assert uhs_controller.q_to_receive_kw(prosumer) == pytest.approx(q_to_fill_kwh * 3600/uhs_controller.resol)

        q_in_kw = 1000
        q_out_kw = 100
        uhs_controller.q_to_deliver_kw = lambda x: q_out_kw
        assert uhs_controller.q_to_receive_kw(prosumer) == pytest.approx(q_to_fill_kwh * 3600/uhs_controller.resol + q_out_kw)

        uhs_controller.inputs = np.array([[q_in_kw]])
        assert uhs_controller.q_to_receive_kw(prosumer) == pytest.approx(q_to_fill_kwh * 3600/uhs_controller.resol + q_out_kw - q_in_kw)
