import time
from scipy.sparse.linalg import inv as spinv
from scipy.sparse import csr_matrix
import numpy as np
import logging
from project_code.misc_functions import sub_matrix
from pathlib import Path
from definitions import ROOT_DIR
import os


def create_inv_susceptance_matrix(branches, nodes, slack_node):
    t1 = time.clock()
    B = np.zeros((len(nodes), len(nodes)))
    for branch in branches:
        i = branch.node_from.index
        j = branch.node_to.index
        B[i, i] += -1 / branch.impedance
        B[j, j] += -1 / branch.impedance
        B[i, j] += 1 / branch.impedance
        B[j, i] += 1 / branch.impedance
    B = np.delete(B, slack_node.index, axis=0)
    B = np.delete(B, slack_node.index, axis=1)
    logging.info(f"Susceptance matrix B built in {round(time.clock() - t1, 2)} seconds.")

    t1 = time.clock()
    B2 = csr_matrix(B)
    invB2 = spinv(B2)
    inverseB = invB2.toarray()
    logging.info(f"Susceptance matrix B inverted in {round(time.clock() - t1, 2)} seconds.")
    return inverseB


def create_ISF_matrix(branches, nodes, inv_B, slack_node):
    t1 = time.clock()

    list_ISF = []
    for branch in branches:
        i = branch.node_from.index
        B_from = get_row_from_inv_B(i, inv_B, nodes, slack_node)

        j = branch.node_to.index
        B_to = get_row_from_inv_B(j, inv_B, nodes, slack_node)

        list_ISF.append(-1 / branch.impedance * np.array((B_from - B_to)))
    matrixISF = np.array(list_ISF)
    matrixISF = np.insert(matrixISF, slack_node.index, 0, axis=1)
    logging.info(f"ISF matrix computed in {round(time.clock() - t1, 1)} seconds.")
    return matrixISF


def get_row_from_inv_B(i, inv_B, nodes, slack_node):
    if i < slack_node.index:
        BFrom = inv_B[i, :]
    elif i > slack_node.index:
        BFrom = inv_B[i - 1, :]
    else:
        BFrom = np.zeros(len(nodes) - 1)
    return BFrom


def create_PTDF_matrix(branches, ISF):
    t1 = time.clock()
    list_PTDF = []
    for branch in branches:
        column = np.array((ISF[:, branch.node_from.index] - ISF[:, branch.node_to.index]))
        list_PTDF.append(column)
    PTDF = np.transpose(np.array(list_PTDF))

    logging.info(f"PTDF computed in {round(time.clock() - t1, 1)} seconds.")
    return PTDF


def set_PTDF_on_branches(PTDF, branches, epsilon):
    for branch in branches:
        branch.PTDF = PTDF[branch.index, branch.index]

    n_warnings = len([branch for branch in branches if branch.PTDF < -epsilon]) + len(
        [branch for branch in branches if branch.PTDF > 1+epsilon])
    if n_warnings > 0:
        logging.info(f"{n_warnings} out of {len(branches)} branches have suspicious PTDF, "
                     f"see log file for details.")
        for branch in branches:
            if branch.PTDF < -epsilon:
                logging.debug(f"Branch '{branch.name_branch}' has negative selfPTDF: {branch.PTDF}")
            if branch.PTDF > 1 + epsilon:
                logging.debug(f"Branch '{branch.name_branch}' has selfPTDF over 1: {branch.PTDF}")


def create_LODF_matrix(branches, PTDF, epsilon):
    """
    This function computes a LODF matrix from a PTDF matrix. It is assumed that the PTDF matrix
    is order provided by the 'index' property of each branch.
    :param branches:  a list on n branches
    :param PTDF: a square matrix of size n*n of Power Transfer Distribution Factors
    :param epsilon: sensitivity to determine == 1
    :return: a square matrix of size n*n of Line Outage Distribution Factors.
    """
    t0 = time.clock()

    list_LODF = []
    for branch in branches:
        if branch.PTDF < 1 - epsilon:
            column = np.array(PTDF[:, branch.index] / (1 - branch.PTDF))
            column[branch.index] = 0.0
        else:
            column = np.zeros(PTDF.shape[0])
        list_LODF.append(column)
    LODF = np.transpose(np.array(list_LODF))
    logging.info(f"LODF (N-1 IF) computed in {round(time.clock() - t0, 1)} seconds.")
    return LODF


def create_PATL_matrix(branches):
    t0 = time.clock()

    array_PATL = np.array([elt.PATL for elt in branches])

    sizeP = len(array_PATL)
    list_PATL = []
    for i in range(sizeP):
        if array_PATL[i] > 0:
            list_PATL.append(array_PATL / array_PATL[i])
        else:
            list_PATL.append(np.array([1.0] * sizeP))

    logging.info(f"Normalization matrix built in {round(time.clock() - t0, 3)} seconds.")
    return np.array(list_PATL)


def create_set_external_contingencies(branches, epsilon):
    setR = [branch for branch in branches if branch.ring > 0]
    setR = exclude_radial_elements(setR, epsilon)
    return setR


def create_set_external_contingencies_generators(generators, country):
    return [gen for gen in generators if gen.country != country]


def create_set_within_control_area(branches, country, epsilon, settings):
    setT = [branch for branch in branches if branch.ring == 0]
    logging.info(f"Control area contains {len(setT)} elements")
    setT = exclude_radial_elements(setT, epsilon)

    case_folder_name = f"{settings.case_name}_{settings.input_file_name.replace('.', '_')}"
    fname = f"{country}_sets_T.csv"
    folder_name = Path(ROOT_DIR) / "output_files" / case_folder_name / country
    ffname = folder_name / fname
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    with open(ffname, "w") as fileOut:
        for elt in setT:
            fileOut.write(str(elt) + '\n')

    return setT


def create_set_internal_external_maintenance(branches, LODF, PATL, setR, setT,
                                             country, epsilon, settings):
    setIext = create_set_external_maintenance(setR, setT, LODF, PATL, country, epsilon, settings)
    setIint = create_set_internal_maintenance(branches, epsilon)
    setI = setIext + setIint

    case_folder_name = f"{settings.case_name}_{settings.input_file_name.replace('.', '_')}"
    fname = f"{country}_sets_I.csv"
    ffname = Path(ROOT_DIR) / "output_files" / case_folder_name / country / fname
    with open(ffname, "w") as fileOut:
        for elt in setI:
            fileOut.write(str(elt) + '\n')

    return setI


def create_set_external_maintenance(setR, setT, inputLODF, PATL, country, epsilon, settings):
    setIext = []
    idx_ring = 1
    branches_in_ring = [branch for branch in setR if branch.ring == idx_ring]
    while len(branches_in_ring) > 0:
        for i in range(len(branches_in_ring)):
            setIext.append(branches_in_ring[i])
        idx_ring += 1
        branches_in_ring = [branch for branch in setR if branch.ring == idx_ring]
    setIext = exclude_radial_elements(setIext, epsilon)

    log_set_external_maintenance_to_file(PATL, country, inputLODF, setR, setT, settings)
    logging.info(f"External contingencies determined : {len(setIext)} elements selected "
                 f"within maximum ring # {idx_ring}")

    return setIext


def log_set_external_maintenance_to_file(PATL, country, inputLODF, setR, setT, settings):
    case_folder_name = f"{settings.case_name}_{settings.input_file_name.replace('.', '_')}"
    fname = f"{country}_sets_I_external.csv"
    ffname = Path(ROOT_DIR) / "output_files" / case_folder_name / country / fname

    fileI = open(ffname, "w")
    fileI.write("External contingencies " + '\n')
    fileI.write("Element,Ring,self-PTDF,max IF (non-normalized),max IF (normalized)" + '\n')
    idx_ring = 1
    branches_in_ring = [branch for branch in setR if branch.ring == idx_ring]
    while len(branches_in_ring) > 0:
        LODF = np.absolute(sub_matrix(branches_in_ring, setT, inputLODF))
        LODFn = LODF * sub_matrix(branches_in_ring, setT, PATL)
        for i in range(len(branches_in_ring)):
            eltI = branches_in_ring[i]
            fileI.write(f"{eltI.name_branch},{eltI.ring},{eltI.PTDF},"
                        f"{np.amax(LODF[:, i])},{np.amax(LODFn[:, i])}" + '\n')
        idx_ring += 1
        branches_in_ring = [elt for elt in setR if elt.ring == idx_ring]
    fileI.close()


def create_set_internal_maintenance(branches, epsilon):
    set_I_internal_maintenance = [branch for branch in branches if branch.ring == 0]
    set_I_internal_maintenance = exclude_radial_elements(set_I_internal_maintenance, epsilon)
    logging.info(f"Internal maintenance set contains {len(set_I_internal_maintenance)} elements")
    return set_I_internal_maintenance


def exclude_radial_elements(branch_list, epsilon):
    result = []
    for branch in branch_list:
        if branch.PTDF > 1 - epsilon:
            pass
        else:
            result.append(branch)
    logging.info(f"Radial elements which do not lead to disconnection of a "
                 f"generator are excluded : "
                 f"{len(result)}/{len(branch_list)} kept.")
    return result


def compute_LODF_for_generators(setR_generators, ISF, all_generators):
    t0 = time.clock()
    logging.info("computing LODF for generators")

    list_LODF_gens = []
    for gen_r in setR_generators:
        column = np.zeros(ISF.shape[0])
        balancing_gens = [gen for gen in all_generators if
                          gen.country == gen_r.country and gen != gen_r]
        if len(balancing_gens) == 0:
            logging.info(f"No generators found to balance the contingency of {gen_r.name_branch}")
        else:
            sum_balancing_power = sum([gen_bal.power for gen_bal in balancing_gens])
            for gen_bal in balancing_gens:
                PTDF_gen = ISF[:, gen_bal.node.index] - ISF[:, gen_r.node.index]
                column += gen_bal.power / sum_balancing_power * (np.array(PTDF_gen))
        list_LODF_gens.append(column)

    logging.info(f"LODF determined for generators in {round(time.clock() - t0, 1)} seconds.")
    return np.transpose(np.array(list_LODF_gens))
