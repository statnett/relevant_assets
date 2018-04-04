""" Module for network components such as buses, lines and transformers

"""
import collections
import warnings
import math

import numpy as np

from component_base import Branch, Component
from monsterexceptions import (
    PsseBaseException, PsseWnddtException, PsseMacdatdException
)
from monsterpsspy import MonsterPssPy
from monsterexceptions import PsseLoddtException, PsseMacintException
from serviceenumsandcontants import ComponentStatus, ComponentTypeEnum
from component_busdetails import BusDetails
from component_errors import (
    TwoWindingTransformerInitError, ThreeWindingTransformerInitError, LoadInitError,
    MachineInitError
)
from sharedconstantsandenums import RATE_NAME

warnings.simplefilter('ignore')


class Line(Branch):
    """Main class for a transmission line and cables"""
    _component_type = ComponentTypeEnum.LineComponent

    def __init__(
            self, from_bus, to_bus, identificator, rx=None, length=None,
            rate_a=None, rate_b=None, rate_c=None, msl_component=False, msl_lines=None
    ):
        self.msl_component = msl_component
        self.msl_lines = msl_lines
        self._validate_voltage_levels(from_bus, to_bus)
        super(Line, self).__init__(from_bus, to_bus, identificator, rx, length)

    @staticmethod
    def _validate_voltage_levels(from_bus, to_bus):
        if from_bus.base_voltage != to_bus.base_voltage:
            warnings.warn(
                'Voltage at %s different from voltage at %s.' % (from_bus, to_bus)
            )

    def _change_status(self, from_status, to_status):
        if self.status() == from_status and not self.msl_component:
            if self.msl_lines:
                MonsterPssPy.multi_section_line_edit(
                    self.from_bus.number,
                    self.to_bus.number,
                    self.identificator,
                    [to_status.get_index()]
                )
            else:
                MonsterPssPy.branch_data(
                    self.from_bus.number,
                    self.to_bus.number,
                    self.identificator,
                    [to_status.get_index()]
                )

    def is_branch(self):
        return True


class OverHeadLine(Line):
    """Main class for a transmission line.

    The line is described according to the model in PSSE.

    Parameters
    ==========
    from_bus: Bus component
        the from bus component (not the bus number)
    to_bus: Bus component
        the to bus component (not the bus number)
    Id:str
        the string id of the line
    length: double (optional)
        line length in km.
    rate_a, rate_b, rate_c: double (optional)
        rates as given in the PSSE model.
    metered_from: Bus component (optional)
        the bus from which the line is metered from

    Examples
    ========

        >>> frogner400 = component.Bus(51081, 'FROGNER4', 400)
        >>> aadal = component.Bus(51171, 'ADAL4', 400)
        >>> frogner_aadal = component.Line(frogner400, aadal, '1')

    Raises
    ======
        Error if rates are not ordered.

    """
    _component_type = ComponentTypeEnum.OverHeadLineComponent


class Cable(Line):
    """ Main class for a transmission line.

    This class is similar to (overhead) Line, except for a different _component_type. This
    is done as cables and overhead lines have different failure statistics.
    """

    _component_type = ComponentTypeEnum.CableComponent


class TwoWindingTransformer(Branch):
    """ Main class for a two winding trasnformer

    The transformer is described according to the model in PSSE.

    Parameters
    ==========
    from_bus: Bus component
        the from bus component (not the bus number)
    to_bus: Bus component
        the to bus component (not the bus number)
    name: str (optional)
        name of transformer
    metered_from: Bus component (optional)
        the bus from which the line is metered from

    Examples
    ========

        >>> from accc_pv.component import TwoWindingTransformer
        >>> frogner400 = component.Bus(51081, 'FROGNER4', 400)
        >>> frogner300 = component.Bus(51082, 'FROGNER3', 300)
        >>> f_trafo = TwoWindingTransformer(frogner400, frogner300, '1')

    Raises
    ======
        TwoWindingTransformerInitError

    """

    _component_type = ComponentTypeEnum.TwoWindingTransformerComponent

    def __init__(
            self, from_bus, to_bus, identificator, rx=None, rate_a=None,
            rate_b=None, rate_c=None, name=None, metered_from=True
    ):
        if name is not None and not isinstance(name, str):
            raise TwoWindingTransformerInitError(
                'Two winding name must be a string!'
            )

        self.name = name
        self.metered_from = metered_from
        Branch.__init__(
            self, from_bus, to_bus, identificator, metered_from=metered_from, rx=rx
        )

    def _change_status(self, from_status, to_status):
        if self.status() == from_status:
            MonsterPssPy.two_winding_data(
                self.from_bus.number,
                self.to_bus.number,
                self.identificator,
                [to_status.get_index()],
                []
            )


class ThreeWindingTransformer(Branch):
    """ Main class for a three winding trasnformer

    The transformer is described according to the model in PSSE.

    Parameters
    ==========
    from_bus: Bus component
        the from bus component (not the bus number)
    to_bus: Bus component
        the to bus component (not the bus number)
    other_bus: Bus component
        tertiary component winding
    name: str (optional)
        name of transformer
    none_metered_end: Bus component (optional)
        the bus from which the line is metered from

    Examples
    ========

        >>> from accc_pv.component import ThreeWindingTransformer
        >>> f400 = component.Bus(51081, 'FROGNER4', 400)
        >>> f300 = component.Bus(51082, 'FROGNER3', 300)
        >>> fX = component.Bus(51085, 'FROGNERX', 66)
        >>> f_trafo = ThreeWindingTransformer(400, f300, fX, '1')

    Raises
    ======
        ThreeWindingTransformerInitError

    """

    _component_type = ComponentTypeEnum.ThreeWindingTransformerComponent

    def __init__(
            self, from_bus, to_bus, other_bus, identificator,
            name=None, non_metered_end=None
    ):
        if not isinstance(other_bus, BusDetails):
            raise ThreeWindingTransformerInitError(
                'The other_bus must be of Bus-type.'
            )
        if name is not None and not isinstance(name, str):
            raise ThreeWindingTransformerInitError(
                'Transformer name must be a string.'
            )
        if non_metered_end is not None and \
                not isinstance(non_metered_end, BusDetails):
            raise ThreeWindingTransformerInitError(
                'non_metered_end must be a bus.'
            )
        if non_metered_end is not None and \
                non_metered_end not in (from_bus, to_bus, other_bus):
            raise ThreeWindingTransformerInitError(
                'non_metered_end must be one of the three defining buses.'
            )
        self.other_bus = other_bus
        self.three_winding_name = name
        self.non_metered_end = non_metered_end
        Branch.__init__(self, from_bus, to_bus, identificator)

    def __str__(self):
        """ Return the string representation of a three winding transformer

        Examples
        ========
            >>> f400 = component.Bus(51081, 'FROGNER4', 400)
            >>> f300 = component.Bus(51082, 'FROGNER3', 300)
            >>> fX = component.Bus(51085, 'FROGNERX', 66)
            >>> f_trafo = ThreeWindingTransformer(f400, f300, fX, '1')
            >>> f_trafo.__str__()
            'Three winding transformer Bus 51081 FROGNER4 400.0 - Bus 51082
            FROGNER3 300.0 - Bus 51085 FROGNERX 66.0 1'

        """
        return 'Three winding transformer %s - %s - %s %s' % (
            self.from_bus,
            self.to_bus,
            self.other_bus,
            self.identificator
        )

    def _make_screening_string(self):
        self._screening_string = '{} THREEWINDING AT BUS {} TO BUS {} TO BUS {} CKT {}\n'.format(
            self.action_string['disconnect'], self.from_bus.number, self.to_bus.number,
            self.other_bus, self.identificator
        )

    def _relay_screening_string(self):
        screening_string = '{} THREEWINDING AT BUS {} TO BUS {} TO BUS {} CKT {}\n'.format(
            self._relay_action(), self.from_bus.number, self.to_bus.number, self.other_bus,
            self.identificator
        )
        return screening_string

    def status(self):
        _status = MonsterPssPy.tr3int(
            self.from_bus.number,
            self.to_bus.number,
            self.other_bus.number,
            self.identificator,
            'STATUS'
        )
        return self._component_status(_status)

    def _change_status(self, from_status, to_status):
        """ Take a two winding transformer out of service in the PSSE model.

        This function uses the psspy API to manually set a line in out
        of service. It manipulates the 'status' argument of the
        :func:`psspy.two_winding_data_3` function and sets it to 0.

        Warnings
        ========
        If the line is a part of a multi-line section a waring is issued.
        In this case the same line might be tripped more than once.

        Raises
        ======
        A psspy.PsseException is rasied if one tries to trip an already
        disconnected line.

        """

        if self.status() == from_status:
            MonsterPssPy.three_wnd_imped_chng(
                self.from_bus.number,
                self.to_bus.number,
                self.other_bus.number,
                self.identificator,
                [MonsterPssPy._i()] * 7 + [to_status.get_index()],
                []
            )

    def get_real_power(self):
        buses = collections.deque(self.get_busnumbers())
        pct = -1
        for i in range(3):
            buses.rotate(1)
            pct_wnd = MonsterPssPy.wnddat(
                buses[0], buses[1], buses[2], self.identificator, 'PCTRTA'
            )
            if pct_wnd > pct:
                pct = pct_wnd
                n_rotate = i + 1
        buses.rotate(n_rotate)
        return MonsterPssPy.wnddt2(
            buses[0], buses[1], buses[2], self.identificator, 'FLOW'
        ).real

    def _flow(self, *branch_buses_and_id):
        try:
            s = MonsterPssPy.wnddt2(*branch_buses_and_id, string='FLOW')
        except PsseWnddtException as e:
            if e._ierr == 7:
                s = []
            else:
                raise
        return s

    def flow_amp_rate(self):
        buses = collections.deque(self.get_busnumbers(False))
        flow = []
        rate_a = self.get_rate()
        for i in range(3):
            branch_buses_and_id = [buses[0], buses[1], buses[2], self.identificator]
            s = self._flow(branch_buses_and_id)
            if s:
                i_rate = MonsterPssPy.wnddat(*branch_buses_and_id, string='PCTRTA')
                s_rate = rate_a[i] * i_rate / 100.0
                if s_rate < abs(s.real):
                    flow.append(complex(s.real, 0))
                else:
                    flow.append(complex(s.real, math.sqrt(s_rate**2 - s.real**2)))
            buses.rotate(-1)
        return flow

    def flow(self):
        buses = collections.deque(self.get_busnumbers(False))
        flow = []
        for i in range(3):
            branch_buses_and_id = [buses[0], buses[1], buses[2], self.identificator]
            s = self._flow(*branch_buses_and_id)
            flow.append(s)
            buses.rotate(-1)
        return flow

    def get_flow_direction(self):
        return [np.sign(flow.real) for flow in self.flow()]

    def set_rate(self, file_path):
        buses = collections.deque(self.get_busnumbers(False))
        self._rate[file_path] = []
        for i in range(3):
            self._rate[file_path].append(
                MonsterPssPy.wnddat(buses[0], buses[1], buses[2], self.identificator, RATE_NAME)
            )
            buses.rotate(-1)

    def set_rx(self):
        buses = collections.deque(self.get_busnumbers(False))
        self.rx = []
        for i in range(3):
            self.rx.append(
                MonsterPssPy.wnddt2(buses[0], buses[1], buses[2], self.identificator, 'RX')
            )
            buses.rotate(-1)


class Load(Component):
    """ Main class for load components

    Parameters
    ==========
    bus: Bus component
    identificator: str

    """

    _component_type = ComponentTypeEnum.LoadComponent
    action_string = {'connect': 'ADD', 'disconnect': 'REMOVE'}

    def __init__(self, load_bus, load_id):
        if not isinstance(load_bus, BusDetails):
            raise LoadInitError('load_bus must be a Bus type.')
        if not isinstance(load_id, str):
            raise LoadInitError('load_id must be a String.')

        self.from_bus = load_bus
        self.identificator = load_id.strip()
        super(type(self), self).__init__(activation_sign=-1.0)

    def get_pq(self):
        """ Get PQ value from case as a complex value

        """
        return MonsterPssPy.loddt2(self.from_bus.number, self.identificator, 'MVA', 'ACT')

    def is_injection(self):
        return True

    def set_pq(self, cmplx_pq):
        """Set PQ value in case as actual MVA load

        """
        try:
            return MonsterPssPy.load_chng(
                self.from_bus.number,
                self.identificator,
                realar1=cmplx_pq.real,
                realar2=cmplx_pq.imag
            )
        except PsseBaseException:
            raise

    def get_base_voltage(self):
        """ Return base voltage of load

        Defined as the base voltage of the connected bus.

        """
        return self.from_bus.get_base_voltage()

    def get_area(self):
        """ Return the area of the load

        Defined as the area of the conencted bus.

        """
        area_list = list()
        area_list.extend([self.from_bus.get_area()])

        return list(set(area_list))

    def get_zone(self):
        """ Return the zone of the load

        Defined as the zone of the conencted bus.

        """
        zone_list = list()
        zone_list.extend([self.from_bus.get_zone()])

        return list(set(zone_list))

    def __str__(self):
        """ Return string representation of a Load object

        Examples
        ========
            >>> from accc_pv.component import Load, Bus
            >>> f400 = component.Bus(51081, 'FROGNER4', 400)
            >>> my_load = Load(f400, '1')
            >>> my_load.__str__()
            'Load 51081 1'

        """
        return 'Load %i %s' % (self.from_bus.number, self.identificator)

    def _make_screening_string(self):
        self._screening_string = 'REMOVE LOAD {} FROM BUS {}\n'.format(
            self.identificator, self.from_bus.number
        )

    def _relay_screening_string(self):
        return '{} LOAD {} FROM BUS {}\n'.format(
            self._relay_action(), self.identificator, self.from_bus.number
        )

    def status(self):
        try:
            _status = MonsterPssPy.lodint(self.from_bus.number, self.identificator, 'STATUS')
        except PsseLoddtException as e:
            if e._ierr == 4:
                _status = e._value
            else:
                raise
        return self._component_status(_status)

    def _change_status(self, from_status, to_status):
        # Do we need to scale production on generators due to droop?
        if len(self._scale_area):
            scale_area = self._scale_area
        else:
            scale_area = MonsterPssPy.aareaint(-1, 1, 'NUMBER')[0]

        # Get total load
        try:
            s_total = MonsterPssPy.loddt2(self.from_bus.number, self.identificator, 'TOTAL', 'ACT')
        except PsseLoddtException as e:
            if to_status == ComponentStatus.on and e._ierr == 4:
                s_total = -e._value
            else:
                raise

        if self.status() == to_status:
            if to_status == ComponentStatus.off:
                raise PsseBaseException('Load component already out of service.', None)
            else:
                raise PsseBaseException('Load component already in service.', None)
        try:
            MonsterPssPy.load_chng(
                self.from_bus.number, self.identificator,
                intgar1=to_status.get_index()
            )
            # Define SID for scale area
            sid = 2
            MonsterPssPy.bsys(sid, numarea=len(scale_area), areas=scale_area)
            # Scale with (3) incremental powers, (0) ignore machine
            # power limits, (0) No Q changes and (2) only type 2 and 3
            # buses.
            MonsterPssPy.scal(sid, 0, 0, [0, 0, 0, 2, 0], [0.0, -s_total.real] + [0.0] * 5)

        except PsseBaseException:
            raise


class Machine(Component):
    """ Main class for machine components

    Parameters
    ==========
    bus: Bus component
    identificator: str

    """

    _component_type = ComponentTypeEnum.MachineComponent
    action_string = {'connect': 'ADD', 'disconnect': 'REMOVE'}

    def __init__(self, machine_bus, machine_id):
        if not isinstance(machine_bus, BusDetails):
            raise MachineInitError('machine_bus must be a Bus type.')
        if not isinstance(machine_id, str):
            raise MachineInitError('machine_id must be a String.')

        self.from_bus = machine_bus
        self.identificator = machine_id.strip()
        self.p_lim = self.get_p_lim()
        super(type(self), self).__init__()

    def is_injection(self):
        return True

    def get_base_voltage(self):
        """ Return base voltage of machine

        Defined as the base voltage of the connected bus.

        """
        return self.from_bus.get_base_voltage()

    def get_area(self):
        """ Return the area of the machine

        Defined as the area of the connected bus.

        """
        area_list = list()
        area_list.extend([self.from_bus.get_area()])

        return list(set(area_list))

    def get_zone(self):
        """ Return the zone of the machine

        Defined as the zone of the conencted bus.

        """
        zone_list = list()
        zone_list.extend([self.from_bus.get_zone()])

        return list(set(zone_list))

    def __str__(self):
        """ Return string representation of a Machine object

        Examples
        ========
            >>> from accc_pv.component import Machine, Bus
            >>> f400 = component.Bus(51081, 'FROGNER4', 400)
            >>> my_machine = Machine(f400, '1')
            >>> my_machine.__str__()
            'Machine 51081 1'

        """
        return 'Machine %i %s' % (self.from_bus.number, self.identificator)

    def _make_screening_string(self):
        self._screening_string = 'REMOVE MACHINE {} FROM BUS {}\n'.format(
            self.identificator, self.from_bus.number
        )

    def _relay_screening_string(self):
        return '{} MACHINE {} FROM BUS {}\n'.format(
            self._relay_action(), self.identificator, self.from_bus.number
        )

    def status(self):
        try:
            _status = MonsterPssPy.macint(self.from_bus.number, self.identificator, 'STATUS')
        except PsseMacintException as e:
            if e._ierr == 4:
                _status = e._value
            else:
                raise
        return self._component_status(_status)

    def _change_status(self, from_status, to_status):

        # Do we need to scale production on generators due to droop?
        if len(self._scale_area):
            scale_area = self._scale_area
        else:
            scale_area = MonsterPssPy.aareaint(-1, 1, 'NUMBER')[0]

        # Get total load
        s_total = self.get_pq(to_status)

        if self.status() == to_status:
            if to_status == ComponentStatus.off:
                raise PsseBaseException('Machine component already out of service.', None)
            else:
                raise PsseBaseException('Machine component already in service.', None)

        try:
            MonsterPssPy.machine_data(
                self.from_bus.number, self.identificator,
                [ComponentStatus.off.get_index()]
            )
            # Define SID for scale area
            sid = 2
            MonsterPssPy.bsys(sid, numarea=len(scale_area), areas=scale_area)
            # Scale with (3) incremental powers, (0) ignore machine
            # power limits, (0) No Q changes and (2) only type 2 and 3
            # buses.
            MonsterPssPy.scal(sid, 0, 0, [0, 0, 0, 2, 0], [0.0, s_total.real] + [0.0] * 5)

        except PsseBaseException:
            raise

    def get_pq(self, to_status=ComponentStatus.off):
        """ Get PQ actual machine power output from case as a complex value

        """
        try:
            s_total = MonsterPssPy.macdt2(self.from_bus.number, self.identificator, 'PQ')
        except PsseMacdatdException as e:
            if to_status == ComponentStatus.on and e._ierr == 4:
                s_total = -e._value
            else:
                raise
        return s_total

    def get_p_lim(self):
        """ Get pmin and pmax as a tuple (pmin, pmax)

        """
        try:
            pmin = MonsterPssPy.macdat(self.from_bus.number, self.identificator, 'PMIN')
        except PsseMacdatdException as e:
            if e._ierr == 4:  # machine offline. ignore error and continue
                pmin = e._value
            else:
                raise e
        try:
            pmax = MonsterPssPy.macdat(self.from_bus.number, self.identificator, 'PMAX')
        except PsseMacdatdException as e:
            if e._ierr == 4:  # machine offline. ignore error and continue
                pmax = e._value
            else:
                raise e
        return (pmin, pmax)

    def set_p(self, p):
        """Set active power output of machine in case as MW

        """
        try:
            return MonsterPssPy.machine_chng(
                self.from_bus.number,
                self.identificator,
                realar1=p,
            )
        except PsseBaseException:
            raise
