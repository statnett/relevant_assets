import logging
import time
from pathlib import Path

from definitions import ROOT_DIR
from project_code.classes import Result_IF, Result_IF_generators
from project_code.compute_influence_factors import compute_IFs, compute_IFs_generators
from project_code.matrix_and_set_functions import compute_LODF_for_generators, \
    create_inv_susceptance_matrix, create_ISF_matrix, create_PTDF_matrix, set_PTDF_on_branches, create_LODF_matrix, \
    create_PATL_matrix, create_set_external_contingencies, create_set_external_contingencies_generators, \
    create_set_within_control_area, create_set_internal_external_maintenance
from project_code.misc_functions import setup_logger, add_log_file_handler, remove_log_file_handler
from project_code.read_grid import read_lines, read_transformers, read_generators, read_couplers, \
    create_nodes_and_update_branches_with_node_info, set_node_country, set_branch_country
from project_code.settings import FileTypeEnum, get_settings, SettingsEnum
from project_code.topology_functions import store_topology, remove_branches_with_loop_elements, merge_tie_lines, \
    assign_nodes_to_ring_0, assign_nodes_to_other_rings, remove_non_connected_nodes_and_branches, \
    connect_generators_to_nodes, validate_topology, apply_couplers_on_branches_and_generators, \
    convert_couplers_to_lines, get_most_connected_node
from project_code.topology_getter.pssetopology_wrapper import get_topology


def main(settings):
    logger = setup_logger()
    ttt = time.clock()

    for country in settings.countries:
        if country == 'XX':  # used for surrounding countries of a region that are not analyzed
            continue
        tt = time.clock()
        epsilon = settings.eps
        add_log_file_handler(logger, country, settings)

        logger.info(f"Starting a full run for country '{country}':")
        logger.info(f"Required functions compiled ! Processing {settings.input_file_name}")

        file_contents = open_file(settings)
        branches, generators, nodes = read_grid(file_contents, settings)
        branches, nodes = create_and_preprocess_topology(branches, generators, nodes,
                                                         country, settings)
        store_topology(branches, nodes, country, settings)

        ISF, PTDF, LODF, PATL = create_system_matrices(branches, nodes, country, epsilon)

        setI, setT, setR, setR_gens = create_sets(branches, generators, LODF, PATL, country,
                                                  epsilon, settings)

        results_branches = compute_IFs(branches, setI, setT, setR, LODF, PATL, PTDF)
        store_results(results_branches, country, settings)

        if settings.do_calculate_generator_IF:
            LODF_gens = compute_LODF_for_generators(setR_gens, ISF, generators)
            results_generators = compute_IFs_generators(branches, setT, setI, setR_gens, LODF,
                                                        LODF_gens, PATL)
            store_results_generators(results_generators, country, settings)

        logging.info(f"Whole calculation for {country} performed in {round(time.clock() - tt, 0)} "
                     f"seconds.\n\n")
        remove_log_file_handler(logger, country, settings)

    logging.info(f"Whole calculation for data set performed in {round(time.clock() - ttt, 0)}"
                 f" seconds.\n\n")


def read_grid(file_contents, settings):
    t0 = time.clock()

    branches, generators = read_branches_and_generators(file_contents, settings)
    nodes = create_nodes_and_update_branches_with_node_info(branches)
    set_node_country(nodes, settings)
    set_branch_country(branches)

    logging.info(f"System read from {settings.input_file_name} in {round(time.clock() - t0, 3)} seconds.")
    return branches, generators, nodes


def read_branches_and_generators(file_contents, settings):
    branches = []
    branches.extend(read_lines(file_contents, settings))
    branches.extend(read_transformers(file_contents, settings))
    branches.extend(read_couplers(file_contents, branches, settings))
    generators = read_generators(file_contents, settings)
    return branches, generators


def open_file(settings):
    input_file = Path(ROOT_DIR) / "source_files" / settings.input_file_name
    if not input_file.exists():
        raise FileNotFoundError

    if settings.file_type == FileTypeEnum.uct:
        with open(input_file, "r") as file:
            file_contents = file.read().split('\n')
    elif settings.file_type == FileTypeEnum.psse:
        file_contents = get_topology({0: str(input_file)})
    else:
        raise ValueError("File type not found!")

    return file_contents


def create_and_preprocess_topology(branches, generators, nodes, country, settings):

    t0 = time.clock()

    if settings.do_merge_couplers:
        apply_couplers_on_branches_and_generators(branches, generators, nodes)
    else:
        convert_couplers_to_lines(branches)

    merge_tie_lines(branches, nodes)

    remove_branches_with_loop_elements(branches, nodes)

    validate_topology(nodes, branches)

    n_branch_with_neg_imp = len([branch for branch in branches if branch.impedance < 0])
    logging.info(f"{n_branch_with_neg_imp} branches have negative impedance.")

    assign_nodes_to_ring_0(nodes, branches, country)
    assign_nodes_to_other_rings(nodes)

    nodes, branches = remove_non_connected_nodes_and_branches(nodes)

    connect_generators_to_nodes(nodes, generators)
    validate_topology(nodes, branches, generators)

    logging.info(f"Topology determined in {round(time.clock() - t0, 3)} seconds.")
    return branches, nodes


def create_system_matrices(branches, nodes, country, epsilon):
    slack_node = get_most_connected_node(nodes, country)
    inv_B = create_inv_susceptance_matrix(branches, nodes, slack_node)
    ISF = create_ISF_matrix(branches, nodes, inv_B, slack_node)
    PTDF = create_PTDF_matrix(branches, ISF)
    set_PTDF_on_branches(PTDF, branches, epsilon)
    LODF = create_LODF_matrix(branches, PTDF, epsilon)
    PATL = create_PATL_matrix(branches)
    return ISF, PTDF, LODF, PATL


def create_sets(branches, generators, LODF, PATL, country, epsilon, settings):
    t0 = time.clock()

    setR = create_set_external_contingencies(branches, epsilon)
    setR_gens = create_set_external_contingencies_generators(generators, country)
    setT = create_set_within_control_area(branches, country, epsilon, settings)
    setI = create_set_internal_external_maintenance(branches, LODF, PATL, setR, setT,
                                                    country, epsilon, settings)
    logging.info(f"External elements R : {len(setR)}, generators: {len(setR_gens)}")
    logging.info(f"Internal elements monitored : {len(setT)}")
    logging.info(f"Contingencies : {len(setI)}")
    logging.info("Sets determined in " + str(round(time.clock() - t0, 1)) + " seconds.")
    return setI, setT, setR, setR_gens


def store_results(results, country, settings):
    case_folder_name = f"{settings.case_name}_{settings.input_file_name.replace('.', '_')}"
    fname = f"{country}_results.csv"
    fpath = Path(ROOT_DIR) / "output_files" / case_folder_name / country
    ffname = Path(ROOT_DIR) / "output_files" / case_folder_name / country / fname
    if not fpath.exists():
        fpath.mkdir(parents=True)

    with open(ffname, "w") as file_out:
        file_out.write(Result_IF.header(country))
        for result in results:
            try:
                file_out.write(str(result))
            except (UnicodeEncodeError, UnicodeDecodeError, UnicodeError):
                # work-around for unicode issues
                tmp = str(result).encode(encoding='cp856', errors='ignore')
                result_uc = str(tmp.decode(encoding='utf-8'))
                file_out.write(str(result_uc))


def store_results_generators(results, country, settings):
    case_folder_name = f"{settings.case_name}_{settings.input_file_name.replace('.', '_')}"
    fname = f"{country}_results_generators.csv"
    fpath = Path(ROOT_DIR) / "output_files" / case_folder_name / country
    ffname = Path(ROOT_DIR) / "output_files" / case_folder_name / country / fname
    if not fpath.exists():
        fpath.mkdir(parents=True)

    with open(ffname, "w") as file_out:
        file_out.write(Result_IF_generators.header(country))
        for result in results:
            file_out.write(str(result))


if __name__ == '__main__':
    """Main function. To run, it needs a set of settings, which includes a file name. See settings.py
    for details on how to set the settings."""
    main(settings=get_settings(SettingsEnum.PSSE0))
