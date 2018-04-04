"""Functions to read information from files. Supports UCTE format and PSSE format.
For more information on UCTE format, see http://cimug.ucaiug.org/Groups/Model%20Exchange/UCTE-format.pdf
For more information on PSSE format, see PSSE documentation
"""

import math
import numpy as np
import itertools
import logging

from project_code.classes import Branch, Node, GenerationUnit, BranchTypeEnum
from project_code.settings import FileTypeEnum
from project_code.topology_getter.serviceenumsandcontants import ComponentStatus


def read_lines(file_contents, settings):
    list_of_lines = []
    if settings.file_type == FileTypeEnum.uct:
        line_attributes = read_lines_uct(file_contents, settings)
    elif settings.file_type == FileTypeEnum.psse:
        line_attributes = read_lines_psse(file_contents, settings)
    else:
        raise NotImplementedError('File type provided is not supported.')
    for line in line_attributes:
        list_of_lines.append(Branch(*line))
    logging.info("Lines read")
    return list_of_lines


def read_lines_uct(file_contents, settings):
    line_attributes = []
    i = 0
    while i < len(file_contents) and file_contents[i] != "##L":
        i += 1
    if i < len(file_contents):
        i += 1  # line i is "##L"
        while i < len(file_contents) and file_contents[i][0:2] != "##":
            if int(file_contents[i][20]) < 2:  # if 0 or 1: element in operation. 8 or 9: out of op.
                node_name_from = file_contents[i][0:8]
                node_name_to = file_contents[i][9:17]
                branch_order = file_contents[i][18]
                v_base = settings.dictVbase_uct[int(node_name_from[6:7])]
                impedance = float(file_contents[i][29:35]) * Branch.Sbase / (v_base * v_base)
                IATL = float(file_contents[i][45:51])
                PATL = IATL * math.sqrt(3) * v_base / 1000
                display_name = f"{node_name_from}-{node_name_to}-{branch_order}"
                line_attributes.append([node_name_from, node_name_to, branch_order,
                                        impedance, PATL, v_base, BranchTypeEnum.Line, display_name])
            i += 1
    else:
        raise ValueError("No line ##L was found in the UCT file")
    return line_attributes


# noinspection PyProtectedMember
def read_lines_psse(file_contents, settings):
    line_attributes = []
    combi_dict = {**file_contents.line_dict, **file_contents.msl_parents}
    for (_, node_nr_from, node_nr_to, branch_order), line in combi_dict.items():
        if line._initial_status[0] == ComponentStatus.off:
            continue
        if line.from_bus.base_voltage <= settings.min_voltage_level_PSSE_kV:
            continue
        node_name_from = str(node_nr_from)
        node_name_to = str(node_nr_to)
        v_base = line.from_bus.base_voltage
        display_name = f"{line.from_bus.name} ({line.from_bus.number})-" \
                       f"{line.to_bus.name} ({line.to_bus.number})-{branch_order}"
        if not line.msl_lines:
            PATL = line._rate['']
            impedance = np.imag(line.rx)
        else:
            PATL, impedance = read_lines_psse_multi_section_PATL_and_impedance(line)
        line_attributes.append([node_name_from, node_name_to, branch_order,
                                impedance, PATL, v_base, BranchTypeEnum.Line, display_name])
    return line_attributes


# noinspection PyProtectedMember
def read_lines_psse_multi_section_PATL_and_impedance(msl_parent):
    PATL = 99999
    impedance = 0
    for section in msl_parent.msl_lines:
        if section._rate[''] < PATL:
            PATL = section._rate['']
        if isinstance(section.rx, tuple):
            impedance += np.imag(section.rx[1])
        elif isinstance(section.rx, complex):
            # noinspection PyTypeChecker
            impedance += np.imag(section.rx)
        else:
            raise TypeError('rx type of msl section not understood')
    return PATL, impedance


# noinspection PyProtectedMember
def read_transformers(file_contents, settings):
    list_of_transformers = []
    if settings.file_type == FileTypeEnum.uct:
        trafo_attributes = read_transformers_uct(file_contents, settings)
    elif settings.file_type == FileTypeEnum.psse:
        trafo_attributes, dummy_nodes = read_transformers_psse(file_contents, settings)
    else:
        raise NotImplementedError('File type provided is not supported.')
    for trafo in trafo_attributes:
        list_of_transformers.append(Branch(*trafo))
    logging.info("Transformers read")
    return list_of_transformers


def read_transformers_uct(file_contents, settings):
    list_of_attributes = []
    i = 0
    while i < len(file_contents) and file_contents[i] != "##T":
        i += 1
    if i < len(file_contents):
        i += 1  # line i is "##T"
        while i < len(file_contents) and file_contents[i][0:2] != "##":
            if int(file_contents[i][20]) < 2:  # 0,1 means in operation
                node_name_from = file_contents[i][0:8]
                node_name_to = file_contents[i][9:17]
                branch_order = file_contents[i][18]
                v_base = settings.dictVbase_uct[int(node_name_from[6:7])]
                impedance = float(file_contents[i][47:53]) * Branch.Sbase / (v_base * v_base)
                IATL = float(file_contents[i][70:76])
                PATL = IATL * math.sqrt(3) * v_base / 1000
                display_name = f"{node_name_from}-{node_name_to}-{branch_order}"
                list_of_attributes.append([node_name_from, node_name_to, branch_order,
                                           impedance, PATL, v_base, BranchTypeEnum.Transformer, display_name])
            i += 1
    else:
        raise ValueError("No line ##T was found in the UCT file")
    return list_of_attributes


def read_transformers_psse(file_contents, settings):
    list_of_attributes = []
    list_of_attributes.extend(read_transformers_psse_2w(file_contents, settings))
    trafo_attribs_3w, dummy_nodes = read_transformers_psse_3w(file_contents, settings)
    list_of_attributes.extend(trafo_attribs_3w)
    return list_of_attributes, dummy_nodes


# noinspection PyProtectedMember
def read_transformers_psse_2w(file_contents, settings):
    list_of_attributes = []
    for key, val in file_contents.two_winding_transformer_dict.items():
        if val._initial_status[0].name == 'off':
            continue
        if (val.from_bus.base_voltage < settings.min_voltage_level_PSSE_kV) and \
                (val.to_bus.base_voltage < settings.min_voltage_level_PSSE_kV):
            continue  # filtering on voltage
        _, node_nr_from, node_nr_to, branch_order = key
        node_name_from = str(node_nr_from)
        node_name_to = str(node_nr_to)
        v_base = max(val.from_bus.base_voltage, val.to_bus.base_voltage)
        PATL = val._rate['']
        impedance = np.imag(val.rx)
        display_name = f"{val.from_bus.name} ({val.from_bus.number})-" \
                       f"{val.to_bus.name} ({val.to_bus.number})-{branch_order}"
        list_of_attributes.append([node_name_from, node_name_to, branch_order,
                                   impedance, PATL, v_base, BranchTypeEnum.Transformer2W, display_name])
    return list_of_attributes


# noinspection PyProtectedMember
def read_transformers_psse_3w(file_contents, settings):
    # How to model? PSSE does with internal dummy node. My thoughts:
    # * first check how many of the nodes are relevant.
    #  * if three: do psse type dummy node
    #  * if two: make a normal two-winding transformer
    #  * if one or zero: discard.
    list_of_attributes = []
    list_of_dummy_nodes = []
    idx_new_nodes = 0
    dict_of_relevant_buses, _ = get_relevant_buses_per_3w_trafo(file_contents, settings)
    for key, val in file_contents.three_winding_transformer_dict.items():
        if val._initial_status[0].name == 'off':
            continue
        n_buses = dict_of_relevant_buses[key]
        if len(n_buses) < 2:
            continue
        elif len(n_buses) == 2:
            trafo_attribs = create_2w_trafo_from_3w_data(val, n_buses)
            list_of_attributes.append(trafo_attribs)
        elif len(n_buses) == 3:
            subtrafo_attribs, new_node = create_3w_trafo(val, idx_new_nodes)
            idx_new_nodes += 1
            list_of_attributes.extend(subtrafo_attribs)
            list_of_dummy_nodes.append(new_node)
        else:
            raise ValueError('Found a three winding trafo with >3 buses?')
    return list_of_attributes, list_of_dummy_nodes


def get_relevant_buses_per_3w_trafo(file_contents, settings):
    # step 0: get all buses that are either HV or where a generator is connected
    _, gen_buses = select_hv_generators_and_generator_buses(file_contents, settings)
    HV_buses = [bus.from_bus for bus in file_contents.bus_dict.values()
                if bus.from_bus.base_voltage > settings.min_voltage_level_PSSE_kV]
    potential_buses = set(gen_buses + HV_buses)

    # step 1: check for each 3w trafo which of its buses are relevant
    rel_buses = {}
    for key in file_contents.three_winding_transformer_dict.keys():
        bus_list = []
        for key_nr in range(3):
            if key[key_nr] in potential_buses:
                bus_list.append(key[key_nr])
        rel_buses[key] = bus_list

    # step 2: summarize results (for logging and error checking)
    summary_table = {}
    if len(rel_buses) > 0:
        for val in range(max([len(sub) for sub in rel_buses.values()]) + 1):
            summary_table[val] = [len(sub) for sub in rel_buses.values()].count(val)

    return rel_buses, summary_table


# noinspection PyProtectedMember
def create_2w_trafo_from_3w_data(trafo, n_buses):
    """This function takes a three winding trafo as input and transforms it into
    a two winding variant, as only two of the buses are relevant.
    Input: three winding trafo element, and indication of the two relevant buses.
    Output: Branch object """

    # find new buses
    new_buses = []
    new_buses_idx = []
    for idx, bus in enumerate([trafo.from_bus, trafo.to_bus, trafo.other_bus]):
        if bus.number in n_buses:
            new_buses.append(bus)
            new_buses_idx.append(idx)
    if new_buses[0].base_voltage >= new_buses[1].base_voltage:
        from_bus = new_buses[0]
        to_bus = new_buses[1]
    else:
        from_bus = new_buses[1]
        to_bus = new_buses[0]

    # set std values
    node_name_from = str(from_bus.number)
    node_name_to = str(to_bus.number)
    branch_order = f"{trafo._sorted_short_tuple[3]}_X3_2"
    v_base = max(from_bus.base_voltage, to_bus.base_voltage)

    # PATL is minimum of PATL of the relevant branches
    PATL = min([trafo._rate[''][i] for i in new_buses_idx])

    # impedance is sum of impedance of the relevant branches
    impedance = sum([np.imag(trafo.rx[i]) for i in new_buses_idx])

    display_name = f"{from_bus.name} ({from_bus.number})-" \
                   f"{to_bus.name} ({to_bus.number})-{branch_order}"

    return [node_name_from, node_name_to, branch_order, impedance, PATL, v_base,
            BranchTypeEnum.Transformer3W2, display_name]


# noinspection PyProtectedMember
def create_3w_trafo(trafo, idx):
    """Create a three winding trafo model. Decompose the three winding data into
    3 two-winding trafos that are star-connected to an internal T-bus. See PSSE
    manual figure 4-17.
    """
    new_trafo_attribs = list()
    trafo_buses = [trafo.from_bus, trafo.to_bus, trafo.other_bus]
    trafo_rxes = trafo.rx
    T_node_name = f"{trafo.from_bus.number}_T{idx}"
    T_node = Node(T_node_name)
    v_base = max([bus.base_voltage for bus in trafo_buses])
    for idx, trafo_bus in enumerate(trafo_buses):
        node_name_from = str(trafo_bus.number)
        node_name_to = T_node_name
        branch_order = f"{trafo._sorted_short_tuple[3]}_X3_3"
        impedance = np.imag(trafo_rxes[idx])
        PATL = trafo._rate[''][idx]
        display_name = f"{trafo_bus.name} ({trafo_bus.number})-T-{branch_order}"
        new_trafo_attribs.append([node_name_from, node_name_to, branch_order,
                                  impedance, PATL, v_base, BranchTypeEnum.Transformer3W3, display_name])

    return new_trafo_attribs, T_node


def read_generators(file_contents, settings):
    list_of_generators = []
    if settings.file_type == FileTypeEnum.uct:
        gen_attributes = read_generators_uct(file_contents)
    elif settings.file_type == FileTypeEnum.psse:
        gen_attributes = read_generators_psse(file_contents, settings)
    else:
        raise NotImplementedError('File type provided is not supported.')
    for generator in gen_attributes:
        list_of_generators.append(GenerationUnit(*generator))
    logging.info("Generators read")
    return list_of_generators


def read_generators_uct(file_contents):
    list_of_attributes = []
    i = 0
    while i < len(file_contents) and file_contents[i] != "##N":
        i += 1
    if i < len(file_contents):
        i += 1
        while i < len(file_contents) and (file_contents[i][0:2] != "##" or file_contents[i][0:3] == "##Z"):
            if len(file_contents[i]) > 80:
                node_name = file_contents[i][0:8]
                try:
                    generator_power = float(file_contents[i][73:80])
                    if generator_power >= 0.0:
                        logging.debug(f"     Generator {node_name} has negative or zero "
                                      f"maximum generation power \n")
                    else:
                        name_suffix = ''
                        list_of_attributes.append([node_name, -generator_power, name_suffix])
                except ValueError:
                    logging.debug(f"     Generator {node_name} maximum "
                                  f"permissible generation could not be "
                                  f"read.\n")
            i += 1
    else:
        raise ValueError("No line ##N was found in the UCT file")
    return list_of_attributes


def read_generators_psse(file_contents, settings):
    list_of_attributes = []
    selection_dict, _ = select_hv_generators_and_generator_buses(file_contents, settings)
    for machine_key, machine_val in file_contents.machine_dict.items():
        if not selection_dict[machine_key]:
            continue
        node_name = str(machine_val.from_bus.number)
        generator_power = machine_val.p_lim[1]  # set gen power at PMax
        if generator_power <= 0:
            continue
        name_suffix = machine_key[3]
        list_of_attributes.append([node_name, generator_power, name_suffix])
    return list_of_attributes


def select_hv_generators_and_generator_buses(file_contents, settings):
    """Determine per generator whether it should be part of the analysis.
    Implemented logic: generators at voltage levels higher than minumum will be
    connected. However, generators at a bus directly coupled to a transformer up
    to a voltage level higher than minimum should also be connected, as those
    are likely step-up transformers that connect generator to the grid.
    No check on generators out of operation as we assume that generators out of
    operation in the PSSE case might actually be relevant.
    """
    min_voltage = settings.min_voltage_level_PSSE_kV
    machine_dict = file_contents.machine_dict
    trafo_buses = get_buses_connected_to_hv_trafo(file_contents, settings)
    selection = dict()
    generator_buses = list()
    for key, machine in machine_dict.items():
        if machine.from_bus.base_voltage > min_voltage:
            selection[key] = True
            generator_buses.append(machine.from_bus)
        elif machine.from_bus.number in trafo_buses:
            selection[key] = True
            generator_buses.append(machine.from_bus)
        else:
            selection[key] = False
    return selection, generator_buses


def get_buses_connected_to_hv_trafo(file_contents, settings):
    two_w_dict = file_contents.two_winding_transformer_dict
    relevant_buses_2w = [(trafo.to_bus.number, trafo.from_bus.number)
                         for trafo in two_w_dict.values()
                         if (trafo.from_bus.base_voltage > settings.min_voltage_level_PSSE_kV) or
                         (trafo.to_bus.base_voltage > settings.min_voltage_level_PSSE_kV)]
    three_w_dict = file_contents.three_winding_transformer_dict
    relevant_buses_3w = [(trafo.to_bus.number, trafo.from_bus.number, trafo.other_bus.number)
                         for trafo in three_w_dict.values()
                         if (trafo.from_bus.base_voltage > settings.min_voltage_level_PSSE_kV) or
                         (trafo.to_bus.base_voltage > settings.min_voltage_level_PSSE_kV) or
                         (trafo.other_bus.base_voltage > settings.min_voltage_level_PSSE_kV)]
    relevant_buses = set(list(itertools.chain(*relevant_buses_2w)) +
                         list(itertools.chain(*relevant_buses_3w)))
    return relevant_buses


def read_couplers(file_contents, branches, settings):
    """Note: couplers are quite differently defined per file type:
     * In UCT, they are a separate list, so those we add to the branches list.
     * In PSSE, they are not separately defined. there we take all branches of
     type 'Line' with rate 0 to be couplers. In that case we redefine type of existing
     branch, and list_of_couplers will be empty.
     """
    list_of_couplers = []
    if settings.file_type == FileTypeEnum.uct:
        coupler_attributes = read_couplers_uct(file_contents, settings)
        for coupler in coupler_attributes:
            list_of_couplers.append(Branch(*coupler))
    elif settings.file_type == FileTypeEnum.psse:
        for branch in branches:
            if branch.type != BranchTypeEnum.Line:
                continue
            if branch.PATL > 1e-5:  # then line is actual line and not coupler
                continue
            branch.type = BranchTypeEnum.Coupler
    else:
        raise NotImplementedError('File type provided is not supported.')
    return list_of_couplers


def read_couplers_uct(file_contents, settings):
    coupler_attributes = []
    i = 0
    while i < len(file_contents) and file_contents[i] != "##L":
        i += 1
    if i < len(file_contents):
        i += 1  # line i is "##L"
        while i < len(file_contents) and file_contents[i][0:2] != "##":
            if int(file_contents[i][20]) == 2:
                node_name_from = file_contents[i][0:8]
                node_name_to = file_contents[i][9:17]
                branch_order = file_contents[i][18]
                v_base = settings.dictVbase_uct[int(node_name_from[6:7])]
                impedance = 0.03 * Branch.Sbase / (v_base * v_base)
                PATL = 0.0
                display_name = f"{node_name_from}-{node_name_to}-{branch_order}"
                coupler_attributes.append([node_name_from, node_name_to, branch_order,
                                           impedance, PATL, v_base, BranchTypeEnum.Coupler, display_name])
            i += 1
    return coupler_attributes


def create_nodes_and_update_branches_with_node_info(branches):
    """Based on node names in branches, do the following:
    1. create node objects for each node
    2. add node objects at each branch at 'from' and 'to' end
    3. add a list of connected branches to each node object
    4. return list of nodes (and implicitly updated branch objects)"""
    dict_of_nodes = {}
    for branch in branches:
        for node_type in ('from', 'to'):
            node_name = getattr(branch, f"name_{node_type}")
            if node_name in dict_of_nodes:
                dict_of_nodes[node_name].branches.append(branch)  # add branch to node
            else:
                new_node = Node(node_name)
                new_node.branches.append(branch)  # add branch to node
                dict_of_nodes[new_node.name] = new_node
            setattr(branch, f"node_{node_type}", dict_of_nodes[node_name])  # add node to branch

    logging.info("List of nodes built")
    return list(dict_of_nodes.values())


def set_node_country(nodes, settings):
    """The way a country is defined will vary per case and needs therefore to be hardcoded for each case and file type
    combination.
    Special cases:
    Country 'XX' is used for countries that are adjacent to the study area that will not
    be considered when computing influence factor.
    Country 'X' is used for 'X-nodes', which are artificial nodes in the model on the border
    between countries. For example, a line from country A to B is often modeled as two lines:
    One line from station in A to a virtual bus bar X at the border, with bus country X, and one
    one line from bus bar X to station in B."""
    if (settings.file_type == FileTypeEnum.uct) and (settings.case_name == 'Europe'):
        for node in nodes:
            if node.name[0:1] == "D":
                if node.name[1:2].isdigit():
                    node.country = node.name[0:2]
                else:
                    node.country = "XX"
            else:
                node.country = node.name[0:1]

            if node.country is None:
                raise ValueError(f'Node country could not be determined for node {node.name}')
    elif (settings.file_type == FileTypeEnum.psse) and (settings.case_name == 'Nordics'):
        for node in nodes:
            name = node.name
            if '_T' in name:
                name = name.split('_T')[0]
            name_int = 0
            try:
                name_int = int(name)
            except ValueError:
                pass
            if (len(name) == 6) or (len(name) == 4):
                node.country = set_node_country_exceptions_PSSE_Nordics(name)
            elif name.startswith('T_'):
                node.country = set_node_country_exceptions_PSSE_Nordics(name)
            elif (name_int >= 10_000) and (int(name) < 30_000):
                node.country = 'FI'
            elif (name_int >= 30_000) and (int(name) < 50_000):
                node.country = 'SV'
            elif (name_int >= 50_000) and (int(name) < 70_000):
                node.country = 'NO'
            elif (name_int >= 70_000) and (int(name) < 90_000):
                node.country = 'DK'
            elif (name_int >= 90_000) and (int(name) < 100_000):
                node.country = 'XX'
            else:
                node.country = None
    elif (settings.file_type == FileTypeEnum.psse) and (settings.case_name == 'Test'):

        for node in nodes:
            name_int = int(node.name)
            if (name_int >= 1) and (name_int < 115):
                node.country = 'A'
            elif (name_int >= 115) and (name_int < 189):
                node.country = 'B'
            elif (name_int >= 189) and (name_int <= 281):
                node.country = 'C'
            elif (name_int >= 319) and (name_int <= 9533):
                node.country = 'A'

            # exceptions/special cases:
            if name_int in [201, 207]:
                node.country = 'A'
            elif name_int in [1201, 7130, 7139, 7166]:
                node.country = 'B'
            elif name_int in [664, 2040]:
                node.country = 'C'
    else:
        raise ValueError(f"Could not determine how to set country for case {settings.case_name}.")


def set_node_country_exceptions_PSSE_Nordics(nodename):
    if len(nodename) == 6:
        if int(nodename[0:2]) in [32, 33, 34, 38]:
            return 'SV'
        elif nodename in ['399264', '399265']:
            return 'XX'
        else:
            return None
    if len(nodename) == 4:
        if nodename.startswith('9'):
            return 'X'  # X-nodes - artificial nodes at borders
        else:
            return None


def set_branch_country(branches):
    for branch in branches:
        if branch.node_from is None or branch.node_to is None:
            logging.debug(branch.name_branch + " has not two nodes declared")
        else:
            branch.set_country()
