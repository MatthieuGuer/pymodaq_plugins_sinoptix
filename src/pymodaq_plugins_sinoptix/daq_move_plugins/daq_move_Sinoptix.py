
from typing import Union, List, Dict
from pymodaq.control_modules.move_utility_classes import (DAQ_Move_base, comon_parameters_fun,
                                                          main, DataActuatorType, DataActuator)

from pymodaq_utils.utils import ThreadCommand  # object used to send info back to the main thread
from pymodaq_gui.parameter import Parameter

from pymodaq_plugins_sinoptix.hardware.MRM import MRM

import serial
from serial.tools.list_ports import comports

class DAQ_Move_Sinoptix(DAQ_Move_base):
    """ Instrument plugin class for an actuator.

    """
    is_multiaxes = False
    _axis_names: Union[List[str], Dict[str, int]] = ['Motor angle']
    _controller_units: Union[str, List[str]] = "" #'°'
    _epsilon: Union[float, List[float]] = 0.01
    # data_actuator_type = DataActuatorType.DataActuator  # wether you use the new data style for actuator otherwise set this
    # # as  DataActuatorType.float  (or entirely remove the line)

    stage_names = []

    ports = [port.device for port in comports()]

    params = [
        {'title': 'COM port:', 'name': 'COM_port', 'type': 'list', 'value': 'COM6', 'limits': ports},
        {'title': 'Device ID:', 'name': 'device_id', 'type': 'str', 'value': "d001A"},
        {'title': 'RPM:', 'name': 'rpm', 'type': 'float', 'value': "100"},
        {'title': 'Temperature:', 'name': 'temperature', 'type': 'str', 'value': "", 'readonly':True},
        {'title': 'Closed loop:', 'name': 'closed_loop', 'type': 'group', 'children': [
            {'title': 'Kp:', 'name': 'kp', 'type': 'int', 'min':0, 'max':255, 'value':5},
            {'title': 'Kd:', 'name': 'kd', 'type': 'int', 'min':0, 'max':255, 'value':30},
            ]},
        ] + comon_parameters_fun(is_multiaxes, axis_names=stage_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: MRM = None

        self.device_id = self.settings.child('device_id').value()
        self.COM = self.settings.child('COM_port').value()
        self.rpm = self.settings.child('rpm').value()
        self.kp = self.settings.child('closed_loop', 'kp').value()
        self.kd = self.settings.child('closed_loop', 'kd').value()
        
    def get_actuator_value(self):
        pos = self.controller.get_position()
        self.settings.child("temperature").setValue(self.controller.temperature)
        return pos

    def user_condition_to_reach_target(self) -> bool:
        """ Implement a condition for exiting the polling mechanism and specifying that the
        target value has been reached

       Returns
        -------
        bool: if True, PyMoDAQ considers the target value has been reached
        """
        # TODO either delete this method if the usual polling is fine with you, but if need you can
        #  add here some other condition to be fullfilled either a completely new one or
        #  using or/and operations between the epsilon_bool and some other custom booleans
        #  for a usage example see DAQ_Move_brushlessMotor from the Thorlabs plugin
        return True

    def close(self):
        """Terminate the communication protocol"""
        self.controller.close()

    def commit_settings(self, param: Parameter):

        if param.name() == 'device_id':
            self.device_id = param.value()
        elif param.name() == "COM":
            self.COM = param.value()
        elif param.name() == "rpm":
            self.rpm = param.value()
        elif param.name() == "kp":
            self.kp = param.value()
        elif param.name() == "kd":
            self.kd = param.value()
        else:
            pass

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """
        self.controller = MRM(self.device_id, self.COM)
        try:
            self.controller.open()
            info = f"opened device {self.device_id} on port {self.COM}"
            initialized = True
            self.move_done_signal.connect(self.controller.on_move_done)
        except serial.SerialException:
            info = "Unable to open port"
            initialized = False

        return info, initialized

    def move_abs(self, value: DataActuator):
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one

        self.controller.move(target_angle=value, rpm=self.rpm, kp=self.kp, kd=self.kd)
        # self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))


    def move_rel(self, value: DataActuator):
        self.target_value = value + self.current_value
        self.move_abs(self.target_value)

    def move_home(self):
        self.move_abs(0)

    def stop_motion(self):
        """Stop the actuator and emits move_done signal"""
        self.controller.on_move_done()


if __name__ == '__main__':
    main(__file__)
