import numpy as np
from pandaprosumer import BasicProsumerController
from pandapower.auxiliary import read_from_net, write_to_net
from pandaprosumer.mapping import FluidMixMapping
from pandaprosumer.constants import CELSIUS_TO_K

class GenericReadWriteController(BasicProsumerController):
    def __init__(self,net, generic_write_read_data,
                 consumer_prosumer= None, controller = None,
                 initiator_columns_read=[], responder_columns_read=[],
                 initiator_columns_write=[], responder_columns_write=[],
                 res_table=None, index=0,
                 order=0, level=0, in_service=True, name=None, **kwargs):
        """
        :param write_mapping:
        :param read_mapping:
        """
        super().__init__(net, basic_prosumer_object=generic_write_read_data,
                         order=order, level=level, in_service=in_service,
                         index=index, name=name, **kwargs)
        self.res_table = res_table or "res_"+self.element_name
        self.index = index
        self.applied = False
        self.consumer_prosumer = consumer_prosumer
        self.controller = controller
        self.initiator_columns_read = initiator_columns_read
        self.responder_columns_read = responder_columns_read
        self.initiator_columns_write = initiator_columns_write
        self.responder_columns_write = responder_columns_write


    def initialize_control(self, net):
        self.applied = False

    def control_step(self, net):
        # --- Read: Outputs from net to prosumer ---
        result_row = []
        to_write = []

        for column_name in self.input_columns:
            val = read_from_net(net, self.res_table, self.index, column_name)
            to_write.append((column_name, val))
            result_row.append(val)
        results = np.array([result_row])

        # --- Write: Inputs from prosumer to net ---
        for column_name, value in to_write:
            val = self._get_input(column_name, net)
            print(val, value)
            write_to_net(net, self.res_table, self.index, column_name, val)

        # --- Finalize to communicate back to prosumer ---
        self.finalize(net, results)

        for i in range(len(self.initiator_columns_read)):
            responder_controller = self.consumer_prosumer.controller.iloc[self.controller].object
            init_col_idx = self.result_columns.index(self.initiator_columns_read[i])
            resp_col_idx = responder_controller.input_columns.index(self.responder_columns_read[i])
            responder_controller.inputs[:, resp_col_idx] = np.nan_to_num(
                responder_controller.inputs[:, resp_col_idx], nan=0.0) + self.step_results[:, init_col_idx]

        for i in range(len(self.initiator_columns_write)):
            initiator_controller = self.consumer_prosumer.controller.iloc[self.controller].object
            init_col_idx = initiator_controller.result_columns.index(self.initiator_columns_write[i])
            resp_col_idx = self.input_columns.index(self.responder_columns_write[i])
            self.inputs[:, resp_col_idx] = np.nan_to_num(
                self.inputs[:, resp_col_idx], nan=0.0) + initiator_controller.step_results[:, init_col_idx]



        self.applied = True

    def is_converged(self, net):
        return self.applied
