import math
import collections
import numpy as np
from uuid import uuid1
from monsterexceptions import PsseBrnfloException
from monsterpsspy import MonsterPssPy
from serviceenumsandcontants import ComponentStatus, ComponentTypeEnum, BusType
from component_busdetails import BusDetails
from component_errors import BranchInitError, LineInitError
from sharedconstantsandenums import RATE_NAME


class Component(object):
    """ Base class of network components

    Each component has two basic methods:
        - trip (bring the component out of service)
        - reconnect (bring the component into service

    In addition each component has get-methods for:
        - base_voltage
        - area
        - area
        - zone

    """

    from_bus = 0
    to_bus = 0
    other_bus = 0
    identificator = ''
    _sorted_tuple = None
    _component_type = ComponentTypeEnum.BaseComponent
    _screening_string = None

    def __init__(self, activation_sign=1.0):
        self._relays = list()
        self._relay_activation = None
        self._activation_sign = activation_sign
        self._component_relay_action = 'disconnect'
        self._scale_area = list()
        self.unique_identifier = uuid1()
        self._t_branch_as_relay = False
        self._initial_status = {}
        self._make_screening_string()
        self.db_id = None
        self.tuple_string = None
        self._sorted_short_tuple_string = None
        self._sorted_short_tuple = None
        self._rate = dict()
        try:
            self.set_rate('')
        except:
            pass

    def _relay_action(self):
        return self.action_string[self._component_relay_action]

    def set_activation(self):
        if self._relay_activation:
            self._relay_activation.set_activation()

    def is_branch(self):
        return False

    def is_injection(self):
        return False

    def get_screening_string(self, case_id, check_relays=True):
        if self._screening_string is None:
            self._make_screening_string()
        relay_screening_string = ''
        if check_relays and self._relay_activation and self._relay_activation.activated():
            for component in self._get_relays(case_id, t_branch=self._t_branch_as_relay):
                if component != self:
                    relay_screening_string += component._relay_screening_string()
        return self._screening_string + relay_screening_string

    def disconnect(self):
        self._change_status(ComponentStatus.on, ComponentStatus.off)

    def connect(self):
        self._change_status(ComponentStatus.off, ComponentStatus.on)

    def fault(self, case_id):
        """ Bring a Component object out of service due to fault in the PSSE model

        """

        self.disconnect()

        if self._relay_activation and self._relay_activation.activated():
            for component in self._get_relays(case_id, t_branch=self._t_branch_as_relay):
                if component != self:
                    if component._component_relay_action == 'disconnect':
                        component.disconnect()
                    elif component._component_relay_action == 'connect':
                        component.connect()

    def _relay_armed(self, case_id):
        return (
            self._initial_status[case_id] == ComponentStatus.on and
            self._component_relay_action == 'disconnect' or
            self._initial_status[case_id] == ComponentStatus.off and
            self._component_relay_action == 'connect'
        )

    def _get_relays(self, case_id, t_branch=False):
        relays = []
        if self._relay_armed(case_id):
            for component in self._relays:
                component._append_relays(case_id, relays, t_branch)
        return relays

    def _append_relays(self, case_id, relays, t_branch):
        if self._relay_armed(case_id) and self not in relays:
            relays.append(self)
            if t_branch:  # Will only search for further _relays if this is a t-branch
                for component in self._relays:
                    component._append_relays(case_id, relays, t_branch)

    def _set_tuple(self):
        _tuple = tuple(
            sorted([int(self.from_bus), int(self.to_bus), int(self.other_bus)]) +
            [str(self.identificator).strip(), self._component_type]
        )
        self._sorted_tuple = _tuple
        self._sorted_short_tuple = tuple(self._sorted_tuple[:4])

    def get_base_voltage(self):
        """ Return the base voltage of the component

        """
        raise NotImplementedError

    def get_area(self):
        """ Return the PSSE area of the component
        """
        raise NotImplementedError

    def get_zone(self):
        """ Return the PSSE zone of the component

        """
        raise NotImplementedError

    def get_rate(self):
        return self._rate

    def set_rate(self, file_path):
        pass

    def _buses(self):
        return [bus for bus in [self.from_bus, self.to_bus, self.other_bus] if bus]

    def get_busnumbers(self, with_id=False):
        numbers = [bus.number for bus in self._buses()]
        if with_id:
            numbers.append(self.identificator)
        return numbers

    def get_type(self):
        """ Return type of component

        """
        return self._component_type

    def inital_status(self, case_id):
        return self._initial_status[case_id]

    def add_inital_status(self, case_id, case):
        self._initial_status[case_id] = case

    @staticmethod
    def _component_status(status):
        if status:
            return ComponentStatus.on
        else:
            return ComponentStatus.off

    def status(self):
        """ Return the current status of the component
        """
        raise NotImplementedError

    def __hash__(self):
        """ This hash function provides a unique hash value for each component.
        It is based on the string property of the object and this is assumed to
        be unique in this case.

        """
        return hash(
            self.get_tuple_string()
        )

    def get_sorted_tuple(self):
        if self._sorted_tuple is None:
            self._set_tuple()
        return self._sorted_tuple

    def get_sorted_short_tuple_string(self):
        if self._sorted_short_tuple_string is None:
            self._sorted_short_tuple_string = '_'.join(
                [str(c) for c in self.get_sorted_short_tuple()]
            )
        return self._sorted_short_tuple_string

    def get_sorted_short_tuple(self):
        if self._sorted_short_tuple is None:
            self._set_tuple()
        return self._sorted_short_tuple

    def get_tuple_string(self):
        if self.tuple_string is None:
            self.tuple_string = '_'.join([str(c) for c in self.get_sorted_tuple()])
        return self.tuple_string


    def set_scale_area_when_tripped(self, area=[]):
        """Set area to scale when the component is tripped

        Paramenters
        ==========
        area :

        """
        self._scale_area = list(area)

    def is_connection(self):
        return isinstance(self, Branch)


class Bus(Component):

    _component_type = ComponentTypeEnum.BusComponent
    action_string = {'disconnect': 'OPEN'}

    def __init__(self, from_bus):
        if not isinstance(from_bus, BusDetails):
            raise BranchInitError('From- and to-bus should be a Bus type.')

        self.from_bus = from_bus
        super(type(self), self).__init__()

    def _make_screening_string(self):
        self._screening_string = '{} BUS {} {}\n'.format(
            self.action_string['disconnect'], self.from_bus.number, self.identificator
        )

    def get_area(self):
        return [self.from_bus.get_area()]

    def get_zone(self):
        return [self.from_bus.get_zone()]

    def get_base_voltage(self):
        return self.from_bus.base_voltage

    def is_dummy(self):
        return self.from_bus.is_dummy()

    def get_bus_number(self):
        return self.from_bus.number

    def status(self):
        if MonsterPssPy.busint(self.from_bus.number, 'TYPE') == BusType.disconnected:
            return ComponentStatus.off
        else:
            return ComponentStatus.on


class Branch(Component):
    """ Class for a general branch network component.

    The branch class is the base class of lines and transformers.

    Parameters
    ==========
    from_bus: Bus component
        instance of Bus object
    to_bus: Bus component
        instance of Bus object
    Id: str
        string object identifier

    """

    _component_type = ComponentTypeEnum.BranchComponent
    action_string = {'connect': 'CLOSE', 'disconnect': 'TRIP'}

    def __init__(
            self, from_bus, to_bus, identificator, rx=None, length=None, metered_from=True
    ):
        self._validate_input(
            from_bus, to_bus, identificator, length, metered_from
        )
        self.from_bus = from_bus
        self.to_bus = to_bus
        self.identificator = identificator.strip()
        self.length = length
        self.rx = rx
        self.overload_in_basecase = 0.0
        super(Branch, self).__init__()

    @staticmethod
    def _validate_input(
            from_bus, to_bus, identificator, length, metered_from
    ):
        if not isinstance(from_bus, BusDetails) or not isinstance(to_bus, BusDetails):
            raise BranchInitError('From- and to-bus should be a Bus type.')
        if not isinstance(identificator, str):
            raise BranchInitError('Branch Id must be a string.')
        if from_bus == to_bus:
            raise BranchInitError('From bus cannot be equal to to bus.')
        if length is not None and isinstance(length, str):
            raise LineInitError('Line length cannot be a string!')
        if length is not None and length < 0:
            raise LineInitError(
                'Length of a branch cannot be negative'
            )
        if not isinstance(metered_from, bool):
            raise LineInitError(
                'metered_from should be bool!'
            )

    def get_id(self):
        return self.identificator

    def get_base_voltage(self):
        """Return base voltage of branch

        Defined as the maximum value of the three Bus components that constitute
        the transformer.

        Returns
        =======
        voltage : float
                  Maximum bus voltage for component

        """
        return max(self.get_voltages())

    def get_voltages(self):
        return [bus.get_base_voltage() for bus in self._buses()]

    def set_rate(self, file_path):
        self._rate[file_path] = MonsterPssPy.brndat(*self.get_busnumbers(True), string=RATE_NAME)

    def get_real_power(self):
        args = self.get_busnumbers(True) + ['P']
        return MonsterPssPy.brnmsc(*args)

    def status(self):
        status = MonsterPssPy.brnint(
            self.from_bus.number, self.to_bus.number, self.identificator, 'STATUS'
        )
        return ComponentStatus.get_enum(status)

    def get_area(self):
        """ Returns the union of the from_bus areas and the to_bus areas.

        """
        return list(set(bus.get_area() for bus in self._buses()))

    def get_zone(self):
        """ Returns the union of the from_bus zones and the to_bus zones.

        """
        return list(set(bus.get_zone() for bus in self._buses()))

    def _make_screening_string(self):
        self._screening_string = '{} BRANCH FROM BUS {} TO BUS {} CKT {}\n'.format(
            self.action_string['disconnect'], self.from_bus.number, self.to_bus.number,
            self.identificator
        )

    def _relay_screening_string(self):
        return '{} BRANCH FROM BUS {} TO BUS {} CKT {}\n'.format(
            self._relay_action(), self.from_bus.number, self.to_bus.number, self.identificator
        )

    def _flow(self, *args):
        try:
            s = MonsterPssPy.brnflo(*args)
        except PsseBrnfloException as e:
            if e._ierr == 3:
                return []
            raise
        return s

    def flow(self):
        args = self.get_busnumbers(True)
        return self._flow(*args)

    def flow_amp_rate(self):
        args = self.get_busnumbers(True)
        s = self._flow(*args)
        if s:
            s_rate = self.get_rate()
            irate_1 = MonsterPssPy.brnmsc(*args, string='PCTRTA')
            irate_2 = MonsterPssPy.brnmsc(args[1], args[0], args[2], string='PCTRTA')

            s_rate *= max(irate_1, irate_2) / 100.0
            if s_rate < abs(s.real):
                return complex(s.real, 0)
            else:
                return complex(s.real, math.sqrt(s_rate**2 - s.real**2))
        else:
            return s

    def get_flow_direction(self):
        return np.sign(self.flow().real)

    def __eq__(self, other):
        return self is other or self.get_sorted_tuple() == other.get_sorted_tuple()

    def __str__(self):
        return '{br_name} {from_num} {from_name} - {to_num} {to_name} {br_id}'.format(
            br_name=type(self).__name__,
            from_num=self.from_bus.number,
            from_name=self.from_bus.name,
            to_num=self.to_bus.number,
            to_name=self.to_bus.name,
            br_id=self.identificator
        )

    def __repr__(self):
        return self.__str__()

    def intersection(self, busn):
        return set((self.from_bus.number, self.to_bus.number)).intersection(busn)

    def monitor_this(self, areas):
        return (
            self.status() == ComponentStatus.on and
            (areas is None or set(self.get_area()).issubset(areas))
        )

    def sensitivity(
            self, mainsys, dfxfile, netmod='ac', brnflowtyp='amp',
            transfertyp='export', dispmod=2, toln=0.3
    ):
        busnr = self.get_busnumbers(False)
        if self._component_type == ComponentTypeEnum.ThreeWindingTransformerComponent:
            n = 3
        else:
            n = 1
            busnr.append(0)

        busnr = collections.deque(busnr)
        sens = []
        for _ in range(n):
            sens.append(MonsterPssPy.sensitivity_flow_to_mw(
                busnr[0],
                busnr[1],
                mainsys,
                dfxfile,
                busnr[2],
                self.identificator,
                netmod=netmod,
                brnflowtyp=brnflowtyp,
                transfertyp=transfertyp,
                dispmod=dispmod,
                toln=toln
            ))
            if n == 3:
                busnr.rotate(-1)
            else:
                sens = sens[0]

        return sens
