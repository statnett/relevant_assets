import collections

import numpy as np
import pytest

from project_code.classes import BranchTypeEnum
from project_code.topology_functions import create_coupler_mapping, \
    apply_couplers_on_branches_and_generators, remove_branches_with_loop_elements, \
    merge_tie_lines, get_most_connected_node, assign_nodes_to_ring_0, assign_nodes_to_other_rings, \
    remove_non_connected_nodes_and_branches, validate_topology, convert_couplers_to_lines


def test_branches_generators(branches_generators_nodes):
    if branches_generators_nodes.branches is None:
        print('Branches None, most likely because file not found')
        return
    print_examples(branches_generators_nodes.name,
                   branches_generators_nodes.branches, 'Branch')
    print_stats([line.impedance for line in branches_generators_nodes.branches],
                "Impedance")
    print_stats([line.PATL for line in branches_generators_nodes.branches], "PATL")
    print_examples(branches_generators_nodes.name,
                   branches_generators_nodes.generators, 'Generator')
    print_stats([gen.power for gen in branches_generators_nodes.generators], "Power")


def test_apply_couplers_on_branches(branches_generators_nodes):
    if branches_generators_nodes.branches is None:
        print('Branches None, most likely because file not found')
        return

    branches_generators_nodes.settings.do_merge_couplers = True
    branches = branches_generators_nodes.branches
    generators = branches_generators_nodes.generators
    nodes = branches_generators_nodes.nodes

    validate_topology(nodes, branches)

    couplers = [b for b in branches if b.type == BranchTypeEnum.Coupler]
    n_nodes = len(nodes)
    n_couplers = len(couplers)
    n_branches = len(branches)

    dict_couplers = create_coupler_mapping(couplers)
    apply_couplers_on_branches_and_generators(branches, generators, nodes)

    validate_topology(nodes, branches)

    n_nodes_after = len(nodes)
    n_branches_after = len(branches)
    set_replaced_branches = set(dict_couplers.keys()) - set(dict_couplers.values())
    for branch in branches:
        assert branch.name_from not in set_replaced_branches
        assert branch.name_to not in set_replaced_branches
    print(f'{n_couplers} couplers applied on a total of {n_nodes} nodes and {n_branches} branches')
    print(f'After application, left with {n_nodes_after} nodes and {n_branches_after} branches')
    print_examples(branches_generators_nodes.name, couplers, 'Bus bar coupler')
    print_stats([tr.impedance for tr in couplers], "Impedance")
    print_stats([tr.PATL for tr in couplers], "PATL")


def test_merge_tie_lines(branches_generators_nodes):
    if branches_generators_nodes.branches is None:
        print('Branches None, most likely because file not found')
        return
    branches = branches_generators_nodes.branches
    nodes = branches_generators_nodes.nodes

    validate_topology(nodes, branches)

    n_x_nodes = len([node for node in nodes if node.is_x_node()])
    # to account for x_nodes with more than 2 branches:
    n_redundant_branches = sum([max(len(node.branches)-2, 0) for node in nodes if node.is_x_node()])
    if n_x_nodes > 0:
        x_node = [node for node in nodes if node.is_x_node()][0]
        branch_names = (x_node.branches[0].name_branch, x_node.branches[1].name_branch)
        branch_node_0 = [n for n in [x_node.branches[0].node_from, x_node.branches[0].node_to]
                         if n != x_node]
        branch_node_1 = [n for n in [x_node.branches[1].node_from, x_node.branches[1].node_to]
                         if n != x_node]
        branch_imps = (x_node.branches[0].impedance, x_node.branches[1].impedance)
        branch_PATLs = (x_node.branches[0].PATL, x_node.branches[1].PATL)
    n_nodes = len(nodes)
    n_branches = len(branches)

    merge_tie_lines(branches, nodes)

    assert len([node for node in nodes if node.is_x_node()]) == 0
    assert len(nodes) == n_nodes - n_x_nodes
    # for each x-node, two branches replaced by 1, and correct for redundant branches:
    assert len(branches) == n_branches - n_x_nodes - n_redundant_branches
    if n_x_nodes > 0:
        print(f"Pre merge: {x_node.name} with branches {branch_names}, impedances {branch_imps}, "
              f"and PATLs {branch_PATLs} - between nodes {branch_node_0[0].name} and "
              f"{branch_node_1[0].name}.")
        # noinspection PyUnboundLocalVariable
        new_branch = [b for b in branches
                      if (branch_node_0[0] in (b.node_from, b.node_to))
                      and (branch_node_1[0] in (b.node_from, b.node_to))][0]
        print(f"Post merge: branch {new_branch.name_branch} with impedance "
              f"{new_branch.impedance:.5} and PATL {new_branch.PATL:.5} between "
              f"{new_branch.name_from} and {new_branch.name_to}.")


def test_remove_branches_with_loop_elements(branches_generators_nodes):
    if branches_generators_nodes.branches is None:
        print('Branches None, most likely because file not found')
        return
    branches = branches_generators_nodes.branches
    nodes = branches_generators_nodes.nodes
    nbranches_org = len(branches)
    remove_branches_with_loop_elements(branches, nodes)
    for branch in branches:
        assert branch.name_from != branch.name_to
    validate_topology(nodes, branches)
    print(f'Removed {nbranches_org - len(branches)} branches, {len(branches)} branches left.')


@pytest.mark.parametrize("do_merge_couplers", [True, False])
def test_set_branch_country_onoff_merge(do_merge_couplers, branches_generators_nodes):
    if branches_generators_nodes.branches is None:
        print('Branches None, most likely because file not found')
        return
    name, branches, generators, nodes, settings = branches_generators_nodes

    if do_merge_couplers:
        apply_couplers_on_branches_and_generators(branches, generators, nodes)
    else:
        convert_couplers_to_lines(branches)

    merge_tie_lines(branches, nodes)
    remove_branches_with_loop_elements(branches, nodes)

    assert all([b.country is not None for b in branches])
    assert all([n.country is not None for n in nodes])
    neg = ' ' if do_merge_couplers else ' not '
    nxnodes = len([n for n in nodes if n.country == 'X'])
    ntiebranches = len([b for b in branches if b.country == 'TIE'])
    print(f'{nxnodes} x-nodes, {ntiebranches} tie-lines ({nxnodes/len(nodes)*100:.1f} pct of nodes, '
          f'{ntiebranches/len(branches)*100:.1f} pct of branches)')
    print_list_occurrence(f'Nodes per country when couplers are{neg}merged',
                          [n.country for n in nodes])
    print_list_occurrence(f'Branches per country when couplers are{neg}merged',
                          [b.country for b in branches])


def test_get_most_connected_node(branches_generators_nodes):
    if branches_generators_nodes.branches is None:
        print('Branches None, most likely because file not found')
        return
    branches = branches_generators_nodes.branches
    nodes = branches_generators_nodes.nodes
    merge_tie_lines(branches, nodes)
    countries = branches_generators_nodes.settings.countries
    for country in countries:
        mc_node = get_most_connected_node(nodes, country)
        if mc_node is None:
            continue
        print(f"In {country}, the most connected node is {mc_node.name} with "
              f"{len(mc_node.branches)} branches.")


def test_assign_nodes_to_ring_0(branches_generators_nodes_preprocessed_merged,
                                branches_generators_nodes_preprocessed_nonmerged):

    for switch in range(2):
        if switch == 0:
            branches_generators_nodes = branches_generators_nodes_preprocessed_merged
        else:
            branches_generators_nodes = branches_generators_nodes_preprocessed_nonmerged

        if branches_generators_nodes.branches is None:
            print('Branches None, most likely because file not found')
            return
        branches = branches_generators_nodes.branches
        nodes = branches_generators_nodes.nodes
        countries = branches_generators_nodes.settings.countries

        validate_topology(nodes, branches)

        for country in countries:
            if country == 'XX':
                continue
            n_nodes_in_country = len([n for n in nodes if n.country == country])
            n_branches_in_country = len([b for b in branches if b.country == country])
            print(f'Connecting for country {country} with {n_nodes_in_country} nodes and '
                  f'{n_branches_in_country} branches:')

            assign_nodes_to_ring_0(nodes, branches, country)

            n_nodes_in_ring_0 = len([node for node in nodes if node.ring == 0])
            print(f"Ring 0 initialised with {n_nodes_in_ring_0} nodes.")
            cntry_nodes_non_conn = [n for n in nodes if n.country == country and n.ring != 0]
            for n in cntry_nodes_non_conn:
                print(f"Warning : {n.name} is not connected to {country}")
            conn_nodes_non_cntry = [n for n in nodes if n.ring == 0 and n.country != country]
            for n in conn_nodes_non_cntry:
                print(f"Warning : {n.name} is connected to {country} but belongs to {n.country}")
            assert len(conn_nodes_non_cntry) == 0

            reset_connectivity(branches, nodes)  # only for testing


def test_assign_nodes_to_other_rings(branches_generators_nodes_preprocessed_merged,
                                     branches_generators_nodes_preprocessed_nonmerged):

    for switch in range(2):
        if switch == 0:
            branches_generators_nodes = branches_generators_nodes_preprocessed_merged
        else:
            branches_generators_nodes = branches_generators_nodes_preprocessed_nonmerged

        if branches_generators_nodes.branches is None:
            print('Branches None, most likely because file not found')
            return
        branches = branches_generators_nodes.branches
        nodes = branches_generators_nodes.nodes
        for country in branches_generators_nodes.settings.countries:
            if country == 'XX':
                continue
            n_nodes_in_country = len([n for n in nodes if n.country == country])
            n_branches_in_country = len([b for b in branches if b.country == country])
            print(f'\nConnecting for country {country} with {n_nodes_in_country} nodes and '
                  f'{n_branches_in_country} branches:')

            assign_nodes_to_ring_0(nodes, branches, country)
            assign_nodes_to_other_rings(nodes)

            # Test for consistency
            for node in [node.name for node in nodes if node.ring == 99 and node.connected]:
                print("Node " + node + " is connected but has no ring")
            assert len([node.name for node in nodes if node.ring == 99 and node.connected]) == 0
            for node in [node.name for node in nodes if node.ring < 99 and not node.connected]:
                print("Node " + node + " is in a ring but is not connected")
            assert len([node.name for node in nodes if node.ring < 99 and not node.connected]) == 0

            # Show results of first rings
            max_ring_nr_shown = 3
            for ring_idx in range(max_ring_nr_shown+1):
                data_nodes_in_ring = [(n.name, n.country) for n in nodes if n.ring == ring_idx]
                if ring_idx == 0:
                    print(f"{len(data_nodes_in_ring)} nodes in ring {ring_idx}")
                else:
                    print(f"{len(data_nodes_in_ring)} nodes in ring {ring_idx}: {data_nodes_in_ring}")

            reset_connectivity(branches, nodes)  # only for testing


def test_remove_non_connected_nodes_and_branches(branches_generators_nodes):
    if branches_generators_nodes.branches is None:
        print('Branches None, most likely because file not found')
        return
    branches = branches_generators_nodes.branches
    nodes = branches_generators_nodes.nodes
    merge_tie_lines(branches, nodes)

    # To limit time use of test, only sample first 5 countries
    countries = branches_generators_nodes.settings.countries[:5]

    for country in countries:
        if country == 'XX':
            continue
        assign_nodes_to_ring_0(nodes, branches, country)
        assign_nodes_to_other_rings(nodes)
        n_nodes = len(nodes)
        n_branches = len(branches)

        nodes_new, branches_new = remove_non_connected_nodes_and_branches(nodes)

        assert len([n for n in nodes_new if not n.connected]) == 0, \
            f"Non-connected nodes in node set for {country}."
        assert len([b for b in branches_new if not b.node_from.connected]) == 0, \
            f"Branches with non-connected nodes in node set for {country}."
        assert len([b for b in branches_new if not b.node_to.connected]) == 0, \
            f"Branches with non-connected nodes in node set for {country}."

        print(f"{(1 - len(nodes_new)/n_nodes)*100:.1f}% of nodes removed, ",
              f"{(1 - len(branches_new)/n_branches)*100:.1f}% of branches removed")

        # test for a too high (3 pct is a bit random treshold) number of elements lost
        assert (1 - len(nodes_new)/n_nodes)*100 < 3
        assert (1 - len(branches_new)/n_branches)*100 < 3
        reset_connectivity(branches, nodes)  # only for testing


def print_examples(name, lst, asset_type):
    print(f"\n {name}: {len(lst)} {asset_type}s")
    print(lst[0])
    print(lst[-1])


def print_stats(lst, title):
    print(f"{title } stats: mean {np.mean(lst)}, std {np.std(lst)}, "
          f"median {np.median(lst)}, min {np.min(lst)}, max {np.max(lst)}")


def print_list_occurrence(name, lst):
    print(f"{name}:")
    # noinspection PyArgumentList
    d = dict(collections.Counter(lst))
    for key in sorted(d, key=d.get, reverse=True):
        print(f"{key}\t{d[key]}")


def reset_connectivity(branches, nodes):
    for branch in branches:
        branch.ring = 99
    for node in nodes:
        node.ring = 99
        node.connected = False
