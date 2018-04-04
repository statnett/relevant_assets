import logging
import itertools
from pathlib import Path

import sys

from definitions import ROOT_DIR

from project_code.classes import Node, Branch, BranchTypeEnum


def remove_branches_with_loop_elements(branches, nodes):
    for branch in branches:
        if branch.name_from == branch.name_to:
            branch.remove(branches, nodes)


def apply_couplers_on_branches_and_generators(branches, generators, nodes):
    couplers = [b for b in branches if b.type == BranchTypeEnum.Coupler]
    noncouplers = [b for b in branches if b.type != BranchTypeEnum.Coupler]
    dict_couplers = create_coupler_mapping(couplers)
    for branch in noncouplers:
        branch.apply_couplers(dict_couplers, nodes)
    for branch in couplers:
        branch.remove(branches, nodes)
    for generator in generators:
        if generator.node_name in dict_couplers.keys():
            generator.node_name = dict_couplers[generator.node_name]


def create_coupler_mapping(couplers):
    """Purpose: make a mapping of buses between couplers that allows for merging of buses. Dict is
    used as a from --> to mapping for buses that will be combined.
    """
    dict_couplers = {}
    for coupler in couplers:
        if (coupler.name_from not in dict_couplers.values()) and \
                (coupler.name_from not in dict_couplers.keys()):
            # no buses of this coupler there yet, so add from-to pair in dict
            dict_couplers[coupler.name_from] = coupler.name_to
        elif coupler.name_from in dict_couplers.keys():
            # there is already a from-to pair with same from-bus
            if coupler.name_from in dict_couplers.values():  # if from is also in values, then error
                logging.info(f"Error with coupler {coupler.name_from} -> {coupler.name_to}")
            else:
                # make another link to existing to-bus. Example:
                # coupler = from 1 to 2. In dict already a coupler from 1 to 98
                # then, add to dict a coupling from 2 to 98, so dict now has 1 to 98 and 2 to 98
                dict_couplers[coupler.name_to] = dict_couplers[coupler.name_from]
        elif coupler.name_from in dict_couplers.values():
            # the from bus is already there in right side of the dict.
            # then, replace all of those with the to bus.
            # example: in dict we have 3 --> 1 and 4 --> 1, and our coupler has 1 --> 2. Then, set
            # dict such that it becomes 3 --> 2 and 4 --> 2.
            for key in [key for key in dict_couplers if dict_couplers[key] == coupler.name_from]:
                dict_couplers[key] = coupler.name_to
    return dict_couplers


def convert_couplers_to_lines(branches):
    for b in branches:
        if b.type == BranchTypeEnum.Coupler:
            b.type = BranchTypeEnum.Line


def merge_tie_lines(branches, nodes):
    """For branches crossing borders, it is customary to split those in two parts, one for each
    country. the node connecting those is called an X-node. This function merges such branches back
    together. """
    logging.debug(f"Merging tie-lines")

    x_nodes = [node for node in nodes if node.is_x_node()]
    for x_node in x_nodes:
        if len(x_node.branches) == 1:
            merge_tie_lines_error_handling('one_branch', x_node, branches, nodes)
            continue
        if len(x_node.branches) > 2:
            merge_tie_lines_error_handling('too_many_branches', x_node, branches, nodes)

        branch_a = x_node.branches[0]
        branch_b = x_node.branches[1]

        nodes_a = [node for node in [branch_a.node_from, branch_a.node_to] if node != x_node]
        nodes_b = [node for node in [branch_b.node_from, branch_b.node_to] if node != x_node]
        if (len(nodes_a) != 1) or (len(nodes_b) != 1):
            merge_tie_lines_error_handling('too_many_nodes', x_node)
            continue
        node_a = nodes_a[0]
        node_b = nodes_b[0]

        if branch_a.order != branch_b.order:
            merge_tie_lines_error_handling('nonmatching line orders', x_node)
            merged_order = "X"
        else:
            merged_order = branch_a.order

        PATL = min(branch_a.PATL, branch_b.PATL)
        impedance = branch_a.impedance + branch_b.impedance
        v_base = branch_a.v_base
        display_name = f"{node_a.name} ({node_a.country})-{node_b.name} ({node_b.country})" \
                       f"-{merged_order}"
        merged_branch = Branch(node_a.name, node_b.name, merged_order, impedance, PATL, v_base,
                               "Merged tie-line", display_name)
        merged_branch.node_from = node_a
        merged_branch.node_to = node_b
        merged_branch.is_tie_line = True
        merged_branch.country = 'TIE'
        branches.append(merged_branch)
        node_a.branches.append(merged_branch)
        node_b.branches.append(merged_branch)
        try:
            x_node.remove(branches, nodes)
        except ValueError:
            pass


def merge_tie_lines_error_handling(error, x_node, branches=None, nodes=None):
    if error == 'one_branch':
        logging.debug(f"     Node {x_node.name} and branch {x_node.branches[0].name_branch} "
                      f"removed.\n")
        x_node.remove(branches, nodes)
    if error == 'too_many_branches':
        logging.debug(f"     Warning: X-node {x_node.name} has incorrect number of "
                      f"branches connected, {len(x_node.branches)}. Will try to continue.")
        conn_countries = set()
        for idx, branch in enumerate(x_node.branches):
            other_node = [node for node in (branch.node_from, branch.node_to)
                          if node.name != x_node.name][0]
            if other_node.country in conn_countries:  # keep no more than one branch per country
                x_node.branches.remove(branch)
                branch.remove(branches, nodes)
            else:
                conn_countries.add(other_node.country)
    elif error == 'too_many_nodes':
        branch_a = x_node.branches[0]
        branch_b = x_node.branches[1]
        logging.debug(f"     Error while merging {x_node.name}: "
                      f"incorrect number of nodes for branch "
                      f"{branch_a.name_branch} or {branch_b.name_branch}")
    elif error == 'nonmatching line orders':
        branch_a = x_node.branches[0]
        branch_b = x_node.branches[1]
        logging.debug(f"     Warning while merging {x_node.name}: order could not be "
                      f"determined for lines {branch_a.name_branch} and {branch_b.name_branch}"
                      f", set at order 'X'.")


def assign_nodes_to_ring_0(nodes, branches, country):

    most_connected_node = get_most_connected_node(nodes, country)

    # Setting nodes from the country in 0-ring, starting from the most connected node
    most_connected_node.connected = True
    n_steps = 0
    connectable_branches = [branch for branch in branches if
                            branch.node_to.connected != branch.node_from.connected]
    # node.connected can be True or False, to the list connectable_branches contains only branches
    # that are connected on one side and disconnected on the other side.
    while len(connectable_branches) > 0:
        n_steps += 1
        for branch in connectable_branches:
            branch.node_to.connected = True
            branch.node_from.connected = True
        connectable_branches = [branch for branch in branches if
                                branch.node_to.connected != branch.node_from.connected]
    logging.info(f"Connectivity for {country} established in {n_steps} steps.")

    # The actual connection happens here below:
    # node is inserted in control area by setting ring=0. Then it goes out to all
    # branches connected to itself, and calls same function on the nodes connected to those branches
    # This stops when all branches connected are tie lines. So, all nodes connected to the most
    # connected node in a control area until we are fully blocked by tie lines will be connected.
    sys.setrecursionlimit(2000)  # default = 1000 which was limiting.
    most_connected_node.insert_in_control_area()


def get_most_connected_node(nodes, country):
    branches_in_country = [len(node.branches) for node in nodes if node.country == country]
    if not branches_in_country:
        return None
    max_nr_branches = max(branches_in_country)
    most_connected_node = [node for node in nodes
                           if node.country == country
                           and len(node.branches) == max_nr_branches][0]
    if most_connected_node is None:
        raise ValueError('Cannot find place to start ring 0')

    return most_connected_node


def assign_nodes_to_other_rings(nodes):
    ring_idx = 0
    nodes_in_ring = [node for node in nodes if node.ring == ring_idx]
    while len(nodes_in_ring) > 0:
        for node in nodes_in_ring:
            for branch in node.branches:
                branch.increase_ring(ring_idx)
        ring_idx += 1
        nodes_in_ring = [node for node in nodes if node.ring == ring_idx]
    logging.info("Rings determined. Maximum ring is #" + str(ring_idx - 1) + ".")


def connect_generators_to_nodes(nodes, generators):
    logging.debug("Attaching generators" + '\n')
    generators_to_remove = []

    for generator in generators:
        node_attached_to_generator = [node for node in nodes if node.name == generator.node_name]
        if len(node_attached_to_generator) == 1:
            generator.node = node_attached_to_generator[0]
            generator.country = node_attached_to_generator[0].country
            generator.connected = True
            node_attached_to_generator[0].generators.append(generator)
        else:
            generators_to_remove.append(generator)
            logging.debug(f"     Generator {generator.name} could not be attached to node "
                          f"{generator.node_name} : {len(node_attached_to_generator)} "
                          f"matches found.")

    for generator in generators_to_remove:
        generators.remove(generator)

    for i in range(len(generators)):
        generators[i].index = i

    logging.info(f"{len(generators)} generators are in to the system. "
                 f"{len(generators_to_remove)} generators could not be connected and are removed.")


def remove_non_connected_nodes_and_branches(nodes):
    connected_nodes = [n for n in nodes if n.connected]
    connected_branches_incl_duplicates = []

    for node in connected_nodes:
        connected_branches_incl_duplicates.extend(node.branches)

    seen_id = []
    connected_branches = []
    for branch in connected_branches_incl_duplicates:
        if branch.index in seen_id:
            continue
        seen_id.append(branch.index)
        connected_branches.append(branch)
    # The above is split in two for performance reasons - combined list comprehension is slow

    # Rebuilding index
    for i in range(len(connected_nodes)):
        connected_nodes[i].index = i
    for i in range(len(connected_branches)):
        connected_branches[i].index = i

    logging.info(f"System restricted to main connected components with "
                 f"{len(connected_nodes)} nodes and {len(connected_branches)} elements")
    return connected_nodes, connected_branches


def validate_topology(nodes, branches, generators=None):
    # check that branches are internally consistent
    for branch in branches:
        assert branch.node_from.name == branch.name_from
        assert branch.node_to.name == branch.name_to
        assert branch.name_branch == branch.name_from + " " + branch.name_to + " " + branch.order

    # check that all nodes that are mentioned in the branch list are also in the node list
    nodes_idx_per_branch = [[b.node_from.index, b.node_to.index] for b in branches]
    node_idxes_in_branches = set(list(itertools.chain(*nodes_idx_per_branch)))
    node_idxes_in_nodes = set([n.index for n in nodes])
    assert len(node_idxes_in_branches - node_idxes_in_nodes) == 0, \
        'Nodes in branches that are not in nodes!'

    # check that all branches that are mentioned in the node list are also in the branch list
    branch_idxes_in_nodes = set()
    for node in nodes:
        branch_idxes_in_nodes.update([b.index for b in node.branches])
    branch_idxes_in_branches = set([b.index for b in branches])
    assert len(branch_idxes_in_nodes - branch_idxes_in_branches) == 0, \
        'Branches in nodes that are not in branches!'


    if generators is not None:
        node_idxes_in_generators = set([gen.node.index for gen in generators])
        assert len(node_idxes_in_generators - node_idxes_in_nodes) == 0, \
            'Nodes in generators that are not in nodes!'

    logging.info('Node and branch consistency validated')


def store_topology(branches, nodes, country, settings):
    case_folder_name = f"{settings.case_name}_{settings.input_file_name.replace('.', '_')}"
    fname = "branches.csv"
    ffname = Path(ROOT_DIR) / "output_files" / case_folder_name / country / fname
    with open(ffname, "w") as fileOut:
        fileOut.write(Branch.header() + '\n')
        for branch in branches:
            fileOut.write(branch.save_to_file_str() + '\n')

    fname = "nodes.csv"
    ffname = Path(ROOT_DIR) / "output_files" / case_folder_name / country / fname
    with open(ffname, "w") as fileOut:
        fileOut.write(Node.header() + '\n')
        for node in nodes:
            fileOut.write(node.save_to_file_str() + '\n')
