from numba import jit
import time
from project_code.misc_functions import sub_matrix, combine_sets
from project_code.classes import Result_IF, Result_IF_generators
import numpy as np
import logging


def compute_IFs(branches, setI, setT, setR, LODF, PATL, PTDF):
    t0 = time.clock()

    results = []

    sizeI = len(setI)
    sizeT = len(setT)

    current_ring = 1
    setR_this_ring = [branch for branch in setR if branch.ring == current_ring]
    while len(setR_this_ring) > 0:
        sizeR = len(setR_this_ring)
        logging.info(f"Assessing IF for ring # {current_ring} with {sizeR} elements.")

        set_size_RIT = np.array([sizeR, sizeI, sizeT], dtype=np.int32)
        vPTDF_I = [i.PTDF for i in setI]
        vPTDF_R = [r.PTDF for r in setR_this_ring]
        mxPTDF_IR = sub_matrix(setI, setR_this_ring, PTDF)
        mxPTDF_IT = sub_matrix(setI, setT, PTDF)
        mxPTDF_RI = sub_matrix(setR_this_ring, setI, PTDF)
        mxPTDF_RT = sub_matrix(setR_this_ring, setT, PTDF)

        res_T = np.zeros((sizeI, sizeR), dtype=np.int32)  # Most influenced t element in N-i-r
        res_IF = np.zeros((sizeI, sizeR))  # IF of the most influenced t element in N-i-r situation
        set_IR = combine_sets(setI, setR_this_ring)  # elms i in R set to avoid i = r situation
        set_RT = combine_sets(setR_this_ring, setT)  # elms r in T set to avoid r = t situation
        set_TI = combine_sets(setT, setI)
        mxPATL_RT = sub_matrix(setR_this_ring, setT, PATL)

        res_norm_T = np.zeros((sizeI, sizeR), dtype=np.int32)  # same but normalized
        res_norm_IF = np.zeros((sizeI, sizeR))  # same but normalized
        res_norm_IF_non_norm = np.zeros((sizeI, sizeR))
        res_T_max = np.zeros(sizeR, dtype=np.int32)  # most influenced t element
        res_norm_T_max = np.zeros(sizeR, dtype=np.int32)  # same but normalized
        res_I_max = np.zeros(sizeR, dtype=np.int32)
        res_norm_I_max = np.zeros(sizeR, dtype=np.int32)
        res_IF_max = np.zeros(sizeR)
        res_norm_IF_max = np.zeros(sizeR)
        res_norm_IF_non_norm_max = np.zeros(sizeR)

        LODF_RT = sub_matrix(setR_this_ring, setT, LODF)
        LODFn_RT = LODF_RT * sub_matrix(setR_this_ring, setT, PATL)

        compute_IF_CPU(set_size_RIT,
                       vPTDF_I, vPTDF_R, mxPTDF_IR, mxPTDF_IT, mxPTDF_RI, mxPTDF_RT,
                       res_T, res_IF, set_IR, set_RT, set_TI,
                       mxPATL_RT, res_norm_IF, res_norm_T, res_norm_IF_non_norm)

        get_max_results(res_T, res_IF, res_norm_T, res_norm_IF, res_norm_IF_non_norm,
                        res_T_max, res_norm_T_max, res_I_max, res_norm_I_max, res_IF_max,
                        res_norm_IF_max, res_norm_IF_non_norm_max)

        for idx in range(len(setR_this_ring)):
            # Template : "name,N-1 IF, N-1 nIF,IF,i,t,nIF,i,t,NNnIF"
            r = setR_this_ring[idx]
            IF_1 = max(np.absolute(LODF_RT[:, idx]))
            norm_IF_1 = max(np.absolute(LODFn_RT[:, idx]))
            IF_2 = res_IF_max[idx]
            norm_IF_2 = res_norm_IF_max[idx]
            i = setI[res_I_max[idx]]
            t = setT[res_T_max[idx]]
            i_norm = setI[res_norm_I_max[idx]]
            t_norm = setT[res_norm_T_max[idx]]
            LODF_it = LODF[t_norm.index, i_norm.index]
            LODF_ir = LODF[r.index, i_norm.index]
            results.append(Result_IF(r, IF_1, norm_IF_1, IF_2, norm_IF_2,
                                     i, t, i_norm, t_norm, LODF_it, LODF_ir))
        current_ring += 1
        setR_this_ring = [elt for elt in branches if elt.ring == current_ring]

    logging.info("IF computed in " + str(round(time.clock() - t0, 1)) + " seconds.")
    return results


# Function defined to compute N-2 IF on CPU
@jit('void(int32[:], float64[:], float64[:], float64[:,:], float64[:,:], float64[:,:], float64[:,'
     ':], int32[:,:], float64[:,:], int32[:], int32[:], int32[:], float64[:], float64[:], '
     'int32[:], float64[:,:])')
def compute_IF_CPU(set_size_RIT, vPTDF_I, vPTDF_R, mxPTDF_IR, mxPTDF_IT, mxPTDF_RI, mxPTDF_RT,
                   res_T, res_IF, set_IR, set_RT, set_TI, mxPATL_RT, res_norm_IF, res_norm_T,
                   res_norm_IF_non_norm):
    epsilon = 0.00001
    for (r, i) in np.ndindex((set_size_RIT[0], set_size_RIT[1])):
        PTDF_ir = mxPTDF_IR[r, i]
        PTDF_ri = mxPTDF_RI[i, r]
        PTDF_i = vPTDF_I[i]
        PTDF_r = vPTDF_R[r]

        denominator = (1 - PTDF_i) * (1 - PTDF_r) - PTDF_ir * PTDF_ri

        if abs(denominator) > epsilon:
            for t in range(set_size_RIT[2]):
                if set_IR[i] != r and set_RT[r] != t and set_TI[t] != i:
                    PTDF_it = mxPTDF_IT[t, i]
                    PTDF_rt = mxPTDF_RT[t, r]
                    PATL_rt = mxPATL_RT[t, r]

                    numerator = PTDF_it * PTDF_ri + (1 - PTDF_i) * PTDF_rt
                    IF = numerator / denominator

                    if abs(IF) > res_IF[i, r]:
                        res_IF[i, r] = abs(IF)
                        res_T[i, r] = t
                    norm_IF = PATL_rt * abs(IF)
                    if norm_IF > res_norm_IF[i, r]:
                        res_norm_IF[i, r] = norm_IF
                        res_norm_IF_non_norm[i, r] = abs(IF)
                        res_norm_T[i, r] = t


# Function defined to get IF, t and i from 2-D matrices previously computed (CPU compiled)
@jit(
    'void(int32[:,:], float64[:,:], int32[:,:], float64[:,:], float64[:,:], int32[:], int32[:], '
    'int32[:], int32[:], float64[:], float64[:], float64[:])')
def get_max_results(res_T, res_IF, res_norm_T, res_norm_IF, res_norm_IF_non_norm,
                    res_T_max, res_norm_T_max, res_I_max, res_norm_I_max, res_IF_max,
                    res_norm_IF_max, res_norm_IF_non_norm_max):
    for (i, r) in np.ndindex(res_T.shape):
        if res_IF[i, r] > res_IF_max[r]:
            res_IF_max[r] = res_IF[i, r]
            res_T_max[r] = res_T[i, r]
            res_I_max[r] = i
        if res_norm_IF[i, r] > res_norm_IF_max[r]:
            res_norm_IF_max[r] = res_norm_IF[i, r]
            res_norm_T_max[r] = res_norm_T[i, r]
            res_norm_I_max[r] = i
            res_norm_IF_non_norm_max[r] = res_norm_IF_non_norm[i, r]


def compute_IFs_generators(branches, setT, setI, setR_gens, LODF, LODF_gens, PATL):
    t0 = time.clock()
    logging.info("computing IF for generators")

    LODF_gens_norm = LODF_gens * normalize_generators(branches, setR_gens)
    list_LODF_gens = []
    list_LODFnorm_gens = []
    for t in setT:
        list_LODF_gens.append(LODF_gens[t.index, :])
        list_LODFnorm_gens.append(LODF_gens_norm[t.index, :])
    mxLODF_gens_TR = np.array(list_LODF_gens)
    mxLODFnorm_gens_TR = np.array(list_LODFnorm_gens)
    mxLODF_TI = sub_matrix(setI, setT, LODF)
    mxPATL_TI = sub_matrix(setI, setT, PATL)
    mxLODFnorm_TI = mxLODF_TI * mxPATL_TI

    results = []
    for idx_r, gen_r in enumerate(setR_gens):
        IF_r = 0.0
        IF_r_branches_i = []
        IF_r_branches_t = []
        IF_norm_r = 0.0
        IF_norm_r_branches_i = []
        IF_norm_r_branches_t = []

        for idx_i, branch_i in enumerate(setI):
            vLODF_gens = mxLODF_gens_TR[:, idx_r] + mxLODF_TI[:, idx_i] * LODF_gens[idx_i, idx_r]
            IF_r_i = np.max(np.abs(vLODF_gens))
            vLODF_gens_norm = mxLODFnorm_gens_TR[:, idx_r] + mxLODFnorm_TI[:, idx_i] * \
                              LODF_gens_norm[branch_i.index, idx_r]
            IF_norm_r_i = np.max(np.abs(vLODF_gens_norm))

            if IF_r_i > IF_r:
                IF_r = IF_r_i
                IF_r_branches_i = [branch_i.name_branch]
                IF_r_branches_t = [setT[idx_t].name_branch for idx_t in range(len(setT)) if
                                   abs(vLODF_gens[idx_t]) == IF_r_i]
            elif IF_r_i == IF_r:
                IF_r_branches_i.append(branch_i.name_branch)
                IF_r_branches_t.append([setT[idx_t].name_branch for idx_t in range(len(setT)) if
                                        abs(vLODF_gens[idx_t]) == IF_r_i and not
                                        setT[idx_t].name_branch in IF_r_branches_t])
            if IF_norm_r_i > IF_norm_r:
                IF_norm_r = IF_norm_r_i
                IF_norm_r_branches_i = [branch_i.name_branch]
                IF_norm_r_branches_t = [setT[k].name_branch for k in range(len(setT)) if
                                        abs(vLODF_gens_norm[k]) == IF_norm_r_i]
            elif IF_norm_r_i == IF_norm_r:
                IF_norm_r_branches_i.append(branch_i.name_branch)
                IF_norm_r_branches_t.append([setT[idx_t].name_branch for idx_t in range(len(setT))
                                             if abs(vLODF_gens_norm[idx_t]) == IF_norm_r_i and not
                                             setT[idx_t].name_branch in IF_norm_r_branches_t])

        results.append(Result_IF_generators(gen_r.name, gen_r.power, IF_r,
                                            IF_r_branches_i, IF_r_branches_t,
                                            IF_norm_r, IF_norm_r_branches_i,
                                            IF_norm_r_branches_t))

    logging.info(f"IF determined for generators in {round(time.clock() - t0, 1)} seconds.")
    return results


def normalize_generators(branches, setR_gens):
    PATL = np.array([branch.PATL for branch in branches])

    generator_power = np.array([generator.power for generator in setR_gens])
    list_norm_generators = []
    for idx in range(len(PATL)):
        if PATL[idx] > 0:
            list_norm_generators.append(generator_power / PATL[idx])
        else:
            list_norm_generators.append(generator_power * 0)
    return np.array(list_norm_generators)
