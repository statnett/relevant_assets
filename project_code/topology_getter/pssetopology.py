from pickle import dumps

import pickle
from enum import Enum

from monsterexceptions import PsseNxtMslException, PsseIniMslException
from monsterpsspy import MonsterPssPy
from monster_topology import MonsterTopology
from sharedconstantsandenums import RATE_NAME
import component, component_busdetails, component_base


def get_full_topology(case_path_dict):
    MonsterPssPy.case(case_path_dict.values()[0])
    monster_topology = extract_components_from_case(
        case_path_dict
    )
    return monster_topology


def extract_components_from_case(case_path_dict):
        """ Call upon the :class:`PsseTopology`instance and extract all
        the PSSE data from the current case.

        This includes data for

        * buses
        * lines
        * two- and three winding transformes
        * machines

        For buses and lines and two winding transformers the data is stored both
        in a list and a dict.

        """
        monster_topology = MonsterTopology()

        sid = -1

        bus_dict = get_buses(sid)
        monster_topology.bus_dict = bus_dict
        monster_topology.line_dict = get_lines(sid=sid, bus_dict=bus_dict)
        msl_parents, msl_children = get_msl_components(sid=sid, bus_dict=bus_dict,
                                                       line_dict=monster_topology.line_dict)
        monster_topology.msl_parents = msl_parents
        monster_topology.msl_children = msl_children
        monster_topology.two_winding_transformer_dict = get_two_winding_transformers(
            sid=sid,
            bus_dict=bus_dict
        )
        monster_topology.three_winding_transformer_dict = get_three_winding_transformers(
            sid=sid,
            bus_dict=bus_dict
        )

        monster_topology.machine_dict = get_machines(sid=sid, bus_dict=bus_dict)
        monster_topology.load_dict = get_loads(sid=sid, bus_dict=bus_dict)

        all_components = monster_topology.get_all_components(None)
        monster_topology.all_components = all_components
        for case_id, case in case_path_dict.items():
            MonsterPssPy.case(case)
            for this_component in all_components:
                this_component.add_inital_status(case_id, this_component.status())
        return monster_topology


class IncludeStatus(Enum):
    AddStepAndInService = 3
    AddStepOnly = 4
    InServiceOnly = 1
    NotAddStepAndNotInService = 2


def get_buses(sid):
    """ Extract bus data from the PSSE case

    Parameters
    ==========
    include_only_in_service: Bool (optional=True)
        whether to include only in service buses or not

    """
    flag = IncludeStatus.NotAddStepAndNotInService.value

    bus_names = [
        name.strip() for name in MonsterPssPy.abuschar(
            sid, flag=flag, string='NAME'
        )[0]
    ]

    (bus_voltages,) = MonsterPssPy.abusreal(sid, flag=flag, string='BASE')
    (bus_numbers, bus_areas, bus_zones, bus_dummies, bus_types) = MonsterPssPy.abusint(
        sid, flag=flag, string=['NUMBER', 'AREA', 'ZONE', 'DUMMY', 'TYPE']
    )
    bus_dummies = [bool(bus_dummy) for bus_dummy in bus_dummies]
    bus_dict = dict()
    for bus_number, bus_name, bus_voltage, bus_area, bus_zone, bus_dummy, bus_type in \
            zip(bus_numbers, bus_names, bus_voltages, bus_areas, bus_zones, bus_dummies, bus_types):
        bus_details = component_busdetails.BusDetails(
            bus_number=bus_number,
            bus_name=bus_name,
            base_voltage=bus_voltage,
            areanum=bus_area,
            zonenum=bus_zone,
            dummy=bus_dummy,
            bus_type=bus_type
        )
        bus = component_base.Bus(from_bus=bus_details)
        bus_dict[bus_number] = bus
    return bus_dict


def get_lines(sid, bus_dict):
    """ Extract line data from the PSSE case

    Parameters
    ==========
    include_only_in_service: Bool (optional=True)
        whether to include only in service line or not

    """
    flag = IncludeStatus.NotAddStepAndNotInService.value
    ties = 3
    (from_buses, to_buses) = MonsterPssPy.abrnint(
        sid, flag=flag, ties=ties, string=['FROMNUMBER', 'TONUMBER']
    )

    line_ids = [
        name.strip() for name in MonsterPssPy.abrnchar(
            sid, flag=flag, ties=ties, string='ID'
        )[0]
    ]

    (line_length, rates, ) = MonsterPssPy.abrnreal(
        sid, flag=flag, ties=ties, string=['LENGTH', RATE_NAME]
    )

    rxes = MonsterPssPy.abrncplx(
        sid, flag=flag, ties=ties, string='RX'
    )

    line_dict = dict()
    for from_bus, to_bus, line_id, length, rate_c, rx in zip(
            from_buses, to_buses, line_ids, line_length, rates, rxes[0]
    ):
        comp_func = _classify_branch(from_bus, to_bus, line_id)
        line = comp_func(
            from_bus=bus_dict[from_bus].from_bus,
            to_bus=bus_dict[to_bus].from_bus,
            identificator=line_id,
            length=length,
            rate_c=rate_c,
            rx=rx,
        )
        if not (line.from_bus.dummy or line.to_bus.dummy):
            line_dict[line.get_sorted_short_tuple()] = line
    return line_dict


def _classify_branch(from_bus, to_bus, line_id):
    if isinstance(from_bus, component_busdetails.BusDetails):
        if from_bus.base_voltage > 100:
            if from_bus.name[:3] == 'MF.' and to_bus.name[:3] == 'MF.':
                return component.Cable
            else:
                from_bus = from_bus.number
                to_bus = to_bus.number
        else:
            return component.Line

    if MonsterPssPy.busdat(from_bus, 'KV')[1] > 100.0:
        length = MonsterPssPy.brndat(from_bus, to_bus, line_id, 'LENGTH')
        charging = MonsterPssPy.brndat(from_bus, to_bus, line_id, 'CHARG')
        from_bus_name = MonsterPssPy.notona(from_bus)
        to_bus_name = MonsterPssPy.notona(to_bus)
        if from_bus_name[:3] == 'MF.' and to_bus_name[:3] == 'MF.':
            return component.Cable

        if length > 0.0:
            normed_charging = charging / length
        else:
            normed_charging = 0.0
        tol = 0.005
        if normed_charging > tol:
            return component.Cable
        else:
            return component.Line
    else:
        return component.Line


def get_msl_components(sid, bus_dict, line_dict):
    msl_parents = dict()
    msl_children = dict()
    flag = IncludeStatus.NotAddStepAndNotInService.value
    for from_bus, to_bus, identificator in MonsterPssPy.find_multisections(sid, flag=flag):
        try:
            MonsterPssPy.inimsl(from_bus, to_bus, identificator)
            msl_lines = []
            line = component.Line(
                from_bus=bus_dict[from_bus].from_bus,
                to_bus=bus_dict[to_bus].from_bus,
                identificator=identificator.strip(),
                length=0,
                rate_a=-1,
                msl_lines=msl_lines
            )
            msl_parents[line.get_sorted_short_tuple()] = line
            while True:
                try:
                    ibus, jbus, ickt = MonsterPssPy.nxtmsl()
                    from_bus = bus_dict[ibus].from_bus
                    to_bus = bus_dict[jbus].from_bus
                    component_func = _classify_branch(from_bus, to_bus, ickt)
                    elem_rate_a = MonsterPssPy.brndat(
                        ibus=ibus, jbus=jbus, ickt=ickt, string=RATE_NAME)
                    elem_length = MonsterPssPy.brndat(
                        ibus=ibus, jbus=jbus, ickt=ickt, string='LENGTH')
                    rx = MonsterPssPy.brndt2(
                        ibus=ibus, jbus=jbus, ickt=ickt, string='RX')
                    line = component_func(
                        from_bus=from_bus,
                        to_bus=to_bus,
                        identificator=ickt.strip(),
                        length=elem_length,
                        rate_a=elem_rate_a,
                        rx=rx,
                        msl_component=True
                    )
                    msl_lines.append(line)
                    msl_children[line.get_sorted_short_tuple()] = line
                except PsseNxtMslException:
                    break
        except PsseIniMslException:
            pass
    return msl_parents, msl_children


def get_two_winding_transformers(sid, bus_dict):
    """ Extract two winding transformer data from the PSSE case

    Parameters
    ==========
    include_only_in_service: Bool (optional=True)
        whether to include only in service line or not

    """
    flag = IncludeStatus.NotAddStepAndNotInService.value + 4
    ties = 3
    (from_buses, to_buses) = MonsterPssPy.abrnint(
        sid, flag=flag, ties=ties, string=['FROMNUMBER', 'TONUMBER']
    )
    two_winding_transformer_id = [
        name.strip() for name in MonsterPssPy.abrnchar(
            sid, flag=flag, ties=ties, string='ID'
        )[0]
    ]
    rxes = MonsterPssPy.atrncplx(
        sid, ties=ties, flag=2, string='RXACT'
    )

    two_winding_transformer_dict = dict()
    for from_bus, to_bus, two_winding_transformer_id, rx in zip(
            from_buses, to_buses, two_winding_transformer_id, rxes[0]
    ):
        two_winding_transformer = component.TwoWindingTransformer(
            from_bus=bus_dict[from_bus].from_bus,
            to_bus=bus_dict[to_bus].from_bus,
            identificator=two_winding_transformer_id,
            rx=rx
        )
        two_winding_transformer_dict[
            two_winding_transformer.get_sorted_short_tuple()
        ] = two_winding_transformer
    return two_winding_transformer_dict


def get_three_winding_transformers(sid, bus_dict):
    """ Extract three winding transformer data from the PSSE case

    Parameters
    ==========
    include_only_in_service: Bool (optional=True)
        whether to include only in service line or not

    """
    flag = IncludeStatus.NotAddStepAndNotInService.value
    ties = 3
    (from_buses, to_buses, other_bus) = MonsterPssPy.atr3int(
        sid, flag=flag, ties=ties, string=['WIND1NUMBER', 'WIND2NUMBER', 'WIND3NUMBER']
    )
    three_winding_transformer_id = [
        name.strip() for name in MonsterPssPy.atr3char(sid, flag=flag, ties=ties, string='ID')[0]
    ]

    three_winding_transformer_dict = dict()
    for from_bus, to_bus, other_bus, three_winding_transformer_id in \
            zip(from_buses, to_buses, other_bus, three_winding_transformer_id):
        three_winding_transformer = component.ThreeWindingTransformer(
            from_bus=bus_dict[from_bus].from_bus,
            to_bus=bus_dict[to_bus].from_bus,
            other_bus=bus_dict[other_bus].from_bus,
            identificator=three_winding_transformer_id
        )
        three_winding_transformer.set_rx()
        three_winding_transformer_dict[
            three_winding_transformer.get_sorted_short_tuple()] = three_winding_transformer


    return three_winding_transformer_dict


def get_machines(sid, bus_dict):
    """ Extract machine data from the PSSE case

    Parameters
    ==========
    include_only_in_service: Bool (optional=True)
        whether to include only in service machines or not

    """
    flag = IncludeStatus.NotAddStepAndNotInService.value
    bus_numbers = MonsterPssPy.amachint(sid, flag=flag, string='NUMBER')[0]

    machine_ids = [
        name.strip() for name in MonsterPssPy.amachchar(sid, flag=flag, string='ID')[0]
    ]
    machine_dict = dict()
    for bus_number, machine_id in zip(bus_numbers, machine_ids):
        machine = component.Machine(bus_dict[bus_number].from_bus, machine_id)
        machine_dict[machine.get_sorted_short_tuple()] = machine
    return machine_dict


def get_loads(sid, bus_dict):
    flag = IncludeStatus.NotAddStepAndNotInService.value
    (bus_numbers,) = MonsterPssPy.aloadint(sid, flag=flag, string='NUMBER')
    load_ids = [
        name.strip() for name in MonsterPssPy.aloadchar(sid, flag=flag, string='ID')[0]
    ]
    load_dict = dict()
    for bus_number, load_id in zip(bus_numbers, load_ids):
        load = component.Load(
            load_bus=bus_dict[bus_number].from_bus,
            load_id=load_id
        )
        load_dict[load.get_sorted_short_tuple()] = load
    return load_dict


class ContingencyDataError(Exception):
    """ Error class for the ContingencyData initialization

    """
    pass


if __name__ == '__main__':
    # topology = get_full_topology(
    #     {0: r'P:\PSS-Data\norge\norge_d08h.sav'}
    # )
    topology = get_full_topology(
        {0: r'C:\code\relevant_assets\source_files\Norden2018_tunglast_01A.sav'}
    )
    pass

if __name__ == '__channelexec__':
    (
        case_path_dict
    ) = channel.receive()  # noqa: F821

    topology = get_full_topology(
        case_path_dict
    )
    with open("temp", 'wb') as f:
        pickle.dump(topology, f, protocol=2)
    channel.send('done')  # noqa: F821
