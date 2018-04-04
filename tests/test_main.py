import logging

import pytest

from project_code.classes import Branch, GenerationUnit, Node
from project_code.main import open_file, read_grid, main
from project_code.read_grid import create_nodes_and_update_branches_with_node_info, set_node_country
from project_code.settings import FileTypeEnum, SettingsEnum
from project_code.topology_functions import validate_topology, merge_tie_lines


def test_open_file(settings):
    if settings.file_type == FileTypeEnum.psse:
        try:
            topology = open_file(settings)
        except FileNotFoundError:
            print(f'\n{settings.input_file_name} not found, skipping test for that file.')
            return

        assert isinstance(topology.all_components, list)
        assert len(topology.all_components) > 1
        assert isinstance(topology.bus_dict, dict)
        assert len(topology.bus_dict) > 1
        assert isinstance(topology.line_dict, dict)
        assert len(topology.line_dict) > 1
        assert isinstance(topology.load_dict, dict)
        assert len(topology.load_dict) > 1
        assert isinstance(topology.machine_dict, dict)
        assert len(topology.machine_dict) > 1
    else:  # opening of .uct files is not tested separately
        assert True


@pytest.mark.parametrize("merge_couplers", [True, False])
def test_open_file_and_read_grid_on_off_merge_couplers(merge_couplers, settings):
    settings.do_merge_couplers = merge_couplers

    try:
        file_contents = open_file(settings)
    except FileNotFoundError:
        print(f'\n{settings.input_file_name} not found, skipping test for that file.')
        return

    branches, gens, nodes = read_grid(file_contents, settings)
    assert len(branches) > 0
    assert isinstance(branches[0], Branch)
    assert len([b.name_branch for b in branches]) == len(
        set([b.name_branch for b in branches]))  # uniqueness

    assert len(gens) > 1
    assert isinstance(gens[0], GenerationUnit)
    assert len([g.name for g in gens]) == len(set([g.name for g in gens]))  # uniqueness

    assert len(nodes) > 0
    assert isinstance(nodes[0], Node)
    assert len([n.name for n in nodes]) == len(set([n.name for n in nodes]))


def test_repeated_topology_buildup(settings):
    """Test to catch a strange bug when trying to cycle through a number of countries
    when building up did destroy the code. Disabled for full PSSE model for time reasons"""

    # noinspection PyUnusedLocal
    logger = logging.getLogger('')

    if settings.settings_name != SettingsEnum.PSSETest:
        return True

    for country in settings.countries:
        logging.debug(f'test for country {country}:')

        try:
            file_contents = open_file(settings)
        except FileNotFoundError:
            print(f'\n{settings.input_file_name} not found, skipping test for that file.')
            return

        branches, gens, nodes = read_grid(file_contents, settings)
        nodes = create_nodes_and_update_branches_with_node_info(branches)

        set_node_country(nodes, settings)
        validate_topology(nodes, branches)

        merge_tie_lines(branches, nodes)
        validate_topology(nodes, branches)


def test_open_file_psse_through_gateway(settings):
    if settings.file_type != FileTypeEnum.psse:
        return True
    try:
        topology = open_file(settings)
    except FileNotFoundError:
        print(f'\n{settings.input_file_name} not found, skipping test for that file.')
        return

    assert isinstance(topology.all_components, list)
    assert len(topology.all_components) > 1
    assert isinstance(topology.bus_dict, dict)
    assert len(topology.bus_dict) > 1
    assert isinstance(topology.line_dict, dict)
    assert len(topology.line_dict) > 1
    assert isinstance(topology.load_dict, dict)
    assert len(topology.load_dict) > 1
    assert isinstance(topology.machine_dict, dict)
    assert len(topology.machine_dict) > 1


def test_full_run_test_case(settings):
    # if settings.settings_name != SettingsEnum.PSSETest:
    #     return True
    if settings.settings_name == SettingsEnum.PSSE0:
        return True


    main(settings=settings)
