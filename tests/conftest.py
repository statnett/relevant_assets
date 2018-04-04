import collections
import pytest

from project_code.main import open_file, read_branches_and_generators, read_grid
from project_code.settings import get_settings, SettingsEnum
from project_code.topology_functions import validate_topology, apply_couplers_on_branches_and_generators, \
    merge_tie_lines, remove_branches_with_loop_elements, convert_couplers_to_lines


@pytest.fixture(params=['PSSE full', 'PSSE test case', 'UCT example'], scope='session')
def settings(request):
    if request.param == 'PSSE test case':
        return get_settings(SettingsEnum.PSSETest)
    elif request.param == 'UCT example':
        return get_settings(SettingsEnum.UCT0)
    elif request.param == 'PSSE full':
        return get_settings(SettingsEnum.PSSE0)
    else:
        raise IndexError


# noinspection PyShadowingNames
@pytest.fixture(scope='session')
def name_file_settings(settings):
    NFS = collections.namedtuple('NameFileSettings', 'name file settings')
    try:
        file = open_file(settings)
    except FileNotFoundError:
        file = None
    return NFS(f'{settings.case_name}_{settings.input_file_name}', file, settings)


# noinspection PyShadowingNames
@pytest.fixture(scope='session')
def branches_generators_nodeless(name_file_settings):
    BG = collections.namedtuple('BranchesGenerators',
                                'name branches generators settings')
    name = name_file_settings.name
    file_contents = name_file_settings.file
    settings = name_file_settings.settings

    if file_contents is None:
        return BG(name, None, None, settings)

    branches, generators = read_branches_and_generators(file_contents, settings)

    return BG(name, branches, generators, settings)


# noinspection PyShadowingNames
@pytest.fixture(scope='function')
def branches_generators_nodes(name_file_settings):
    BGN = collections.namedtuple('BranchesGeneratorsNodes',
                                 'name branches generators nodes settings')

    name = name_file_settings.name
    file_contents = name_file_settings.file
    settings = name_file_settings.settings

    if file_contents is None:
        return BGN(name, None, None, None, settings)

    branches, generators, nodes = read_grid(file_contents, settings)
    validate_topology(nodes, branches)

    return BGN(name, branches, generators, nodes, settings)


# noinspection PyShadowingNames
@pytest.fixture(scope='session')
def branches_generators_nodes_preprocessed_merged(name_file_settings):
    BGN = collections.namedtuple('BranchesGeneratorsNodes',
                                 'name branches generators nodes settings')

    name = f'{name_file_settings.name}_mergedcouplers'
    file_contents = name_file_settings.file
    settings = name_file_settings.settings
    if file_contents is None:
        return BGN(name, None, None, None, settings)

    branches, generators, nodes = read_grid(file_contents, settings)
    apply_couplers_on_branches_and_generators(branches, generators, nodes)
    merge_tie_lines(branches, nodes)
    remove_branches_with_loop_elements(branches, nodes)
    validate_topology(nodes, branches)

    return BGN(name, branches, generators, nodes, settings)


# noinspection PyShadowingNames
@pytest.fixture(scope='session')
def branches_generators_nodes_preprocessed_nonmerged(name_file_settings):
    BGN = collections.namedtuple('BranchesGeneratorsNodes',
                                 'name branches generators nodes settings')

    name = f'{name_file_settings.name}_nonmergedcouplers'
    file_contents = name_file_settings.file
    settings = name_file_settings.settings
    if file_contents is None:
        return BGN(name, None, None, None, settings)

    branches, generators, nodes = read_grid(file_contents, settings)
    convert_couplers_to_lines(branches)
    merge_tie_lines(branches, nodes)
    remove_branches_with_loop_elements(branches, nodes)
    validate_topology(nodes, branches)

    return BGN(name, branches, generators, nodes, settings)
