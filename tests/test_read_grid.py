
import collections

import numpy as np
import pytest

from project_code.classes import Branch, GenerationUnit, BranchTypeEnum
from project_code.read_grid import read_lines, read_transformers, read_couplers, read_generators, \
    select_hv_generators_and_generator_buses, set_node_country, create_nodes_and_update_branches_with_node_info, \
    set_branch_country
from project_code.settings import FileTypeEnum
from project_code.topology_functions import create_coupler_mapping


def test_read_lines(name_file_settings):
    if name_file_settings.file is None:
        print(f'\n{name_file_settings.settings.input_file_name} not found, skipping test for that file.')
        return

    list_of_lines = read_lines(name_file_settings.file, name_file_settings.settings)
    assert len(list_of_lines) > 1
    lst_names = [line.name_branch for line in list_of_lines]
    assert len(set(lst_names)) == len(lst_names)  # test if unique
    for line in list_of_lines:
        assert isinstance(line, Branch)
        assert isinstance(line.name_from, str)
        assert len(line.name_from) > 0
        assert isinstance(line.name_to, str)
        assert len(line.name_to) > 0
        assert isinstance(line.impedance, float)
        assert isinstance(line.PATL, (int, float))
        assert line.PATL >= 0
        if name_file_settings.settings.file_type == FileTypeEnum.psse:
            assert line.PATL < 99999  # magic number: default value in multi-section combination
            assert line.v_base > name_file_settings.settings.min_voltage_level_PSSE_kV
    print_examples(name_file_settings.name, list_of_lines, 'Line')
    print_stats([line.impedance for line in list_of_lines], "Impedance")
    print_stats([line.PATL for line in list_of_lines], "PATL")


def test_read_transformers(name_file_settings):
    if name_file_settings.file is None:
        print(f'\n{name_file_settings.settings.input_file_name} not found, skipping test')
        return

    list_of_transformers = read_transformers(name_file_settings.file, name_file_settings.settings)
    assert len(list_of_transformers) > 1
    lst_names = [trf.name_branch for trf in list_of_transformers]
    assert len(set(lst_names)) == len(lst_names)  # test if unique
    # for trf_name in set(lst_names):
    #     lst_names.remove(trf_name)
    for transformer in list_of_transformers:
        assert isinstance(transformer, Branch)
        assert isinstance(transformer.name_from, str)
        assert len(transformer.name_from) > 0
        assert isinstance(transformer.name_to, str)
        assert len(transformer.name_to) > 0
        assert isinstance(transformer.impedance, float)
        assert isinstance(transformer.PATL, (int, float))
        assert transformer.PATL >= 0
        assert transformer.v_base > 0
        assert transformer.type in [BranchTypeEnum.Transformer, BranchTypeEnum.Transformer2W,
                                    BranchTypeEnum.Transformer3W3, BranchTypeEnum.Transformer3W2]
        if name_file_settings.settings.file_type == FileTypeEnum.psse:
            assert transformer.v_base > name_file_settings.settings.min_voltage_level_PSSE_kV
    print_examples(name_file_settings.name, list_of_transformers, 'Transformer')
    print_stats([tr.impedance for tr in list_of_transformers], "Impedance")
    print_stats([tr.PATL for tr in list_of_transformers], "PATL")


def test_read_generators(name_file_settings):
    if name_file_settings.file is None:
        print(f'\n{name_file_settings.settings.input_file_name} not found, skipping test')
        return

    list_of_generators = read_generators(name_file_settings.file, name_file_settings.settings)
    assert len(list_of_generators) > 1
    lst_names = [gen.name for gen in list_of_generators]
    assert len(set(lst_names)) == len(lst_names)  # test if unique
    for generator in list_of_generators:
        assert isinstance(generator, GenerationUnit)
        assert isinstance(generator.name, str)
        assert len(generator.name) > 0
        assert isinstance(generator.node_name, str)
        assert len(generator.node_name) > 0
        assert generator.power > 0
    print_examples(name_file_settings.name, list_of_generators, 'Generator')
    print_stats([gen.power for gen in list_of_generators], "Power")


def test_read_couplers(name_file_settings):
    if name_file_settings.file is None:
        print(f'\n{name_file_settings.settings.input_file_name} not found, skipping test')
        return

    if name_file_settings.settings.file_type == FileTypeEnum.psse:  # does not read couplers
        return True
    nfs = name_file_settings
    branches = []
    branches.extend(read_lines(nfs.file, nfs.settings))
    branches.extend(read_transformers(nfs.file, nfs.settings))
    couplers = read_couplers(nfs.file, branches, nfs.settings)
    dict_couplers = create_coupler_mapping(couplers)
    assert isinstance(dict_couplers, dict)
    assert len(dict_couplers) > 1
    for coupler_key, coupler_val in dict_couplers.items():
        assert isinstance(coupler_key, str)
        assert len(coupler_key) > 0
        assert isinstance(coupler_val, str)
        assert len(coupler_val) > 0
    assert len(couplers) > 0
    for coupler in couplers:
        assert isinstance(coupler, Branch)
        assert isinstance(coupler.name_from, str)
        assert len(coupler.name_from) > 0
        assert isinstance(coupler.name_to, str)
        assert len(coupler.name_to) > 0


def test_read_couplers_no_merge(name_file_settings):
    if name_file_settings.file is None:
        print(f'\n{name_file_settings.settings.input_file_name} not found, skipping test')
        return

    nfs = name_file_settings
    nfs.settings.do_merge_couplers = False
    branches = []
    branches.extend(read_lines(nfs.file, nfs.settings))
    branches.extend(read_transformers(nfs.file, nfs.settings))
    couplers = read_couplers(nfs.file, branches, nfs.settings)
    branches.extend(couplers)
    if nfs.settings.file_type == FileTypeEnum.uct:
        for coupler in couplers:
            assert coupler.impedance == pytest.approx(0.03 * Branch.Sbase /
                                                      (coupler.v_base * coupler.v_base))
            assert coupler.PATL == 0  # magic value in uct code
    if nfs.settings.file_type == FileTypeEnum.psse:
        assert len(couplers) == 0
        assert len([b for b in branches if b.type == BranchTypeEnum.Coupler]) > 0  # at least one coupler found
        assert len([b for b in branches if b.type == BranchTypeEnum.Line]) > 0  # not all lines cast as couplers


def test_generator_selection(name_file_settings):
    if name_file_settings.file is None:
        print(f'\n{name_file_settings.settings.input_file_name} not found, skipping test')
        return

    if name_file_settings.settings.file_type == FileTypeEnum.psse:
        file = name_file_settings.file
        settings = name_file_settings.settings
        selection, buses = select_hv_generators_and_generator_buses(file, settings)
        min_voltage = settings.min_voltage_level_PSSE_kV
        assert len(selection) == len(file.machine_dict)
        tmplist = [machine.from_bus.base_voltage
                   for key, machine in file.machine_dict.items()
                   if selection[key] is True]

        # assert some generators under cutoff voltage are in the list (through step up trafo)
        if min_voltage > 0:
            assert any([t < min_voltage for t in tmplist])

        assert any([t > min_voltage for t in tmplist])


def test_create_nodes_and_update_branches_with_node_info_sampled(branches_generators_nodeless):
    branches = branches_generators_nodeless.branches
    if branches is None:
        print('Branches None, most likely because file not found')
        return

    nodes = create_nodes_and_update_branches_with_node_info(branches)
    bnames = [b.name_branch for b in branches]
    assert len(set(bnames)) == len(bnames)  # all elements unique
    for branch in branches:
        assert branch.node_from in nodes
        assert branch.node_to in nodes
    assert len(nodes) > 1
    assert len(set([n.name for n in nodes])) == len([n.name for n in nodes])

    if len(nodes) > 350:
        np.random.seed(42)
        for idx in np.random.choice(a=len(nodes), size=100, replace=False):
            node = nodes[idx]
            assert len(node.branches) > 0
            for branch in node.branches:
                assert branch in branches
    else:
        for node in nodes:
            assert len(node.branches) > 0
            for branch in node.branches:
                assert branch in branches


def test_set_node_country(branches_generators_nodeless):
    branches = branches_generators_nodeless.branches
    if branches is None:
        print('Branches None, most likely because file not found')
        return
    nodes = create_nodes_and_update_branches_with_node_info(branches)
    set_node_country(nodes, branches_generators_nodeless.settings)
    assert all([n.country is not None for n in nodes])
    print_list_occurrence('Nodes per country', [node.country for node in nodes])


def test_set_branch_country(branches_generators_nodeless):
    branches = branches_generators_nodeless.branches
    if branches is None:
        print('Branches None, most likely because file not found')
        return
    nodes = create_nodes_and_update_branches_with_node_info(branches)
    set_node_country(nodes, branches_generators_nodeless.settings)
    set_branch_country(branches)
    assert all([b.country is not None for b in branches])
    assert all([b.is_tie_line for b in branches if b.country == 'TIE'])
    assert all([b.country == 'TIE' for b in branches if b.is_tie_line])
    print_list_occurrence('Branches per country', [b.country for b in branches])


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
