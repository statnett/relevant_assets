import sys
import numpy as np
import logging
from pathlib import Path

from definitions import ROOT_DIR


def sub_matrix(set_columns, set_rows, matrix_in):
    """
    This function returns the values from matrix_in for
    -columns from set_columns
    -lines from set_rows
    in a new array.
    """
    list_of_rows = []
    for i in range(len(set_rows)):
        list_of_rows.append(matrix_in[set_rows[i].index, :])
    mx_of_set_rows = np.array(list_of_rows)
    list_of_columns = []
    for i in range(len(set_columns)):
        list_of_columns.append(mx_of_set_rows[:, set_columns[i].index])
    return np.transpose(np.array(list_of_columns))


def combine_sets(setA, setB):
    # Function defined to avoid computations of N-k-k, required for computation on GPU.
    results = -1 * np.ones(len(setA), dtype=np.int32)
    for i in range(len(setA)):
        try:
            results[i] = setB.index(setA[i])
        except:
            pass
    return results


def setup_logger():
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s: %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


def remove_log_file_handler(logger, country, settings):
    case_folder_name = f"{settings.case_name}_{settings.input_file_name.replace('.', '_')}"
    fname = f"{country}_log.txt"
    ffname = Path(ROOT_DIR) / "output_files" / case_folder_name / country / fname

    fhs = [fh for fh in logger.handlers if isinstance(fh, logging.FileHandler)]
    fh = [fh for fh in fhs if fh.baseFilename == str(ffname)]
    if len(fh) == 1:
        logger.removeHandler(fh[0])
    else:
        raise ValueError('Trying to remove file handler but ran into issues')


def add_log_file_handler(logger, country, settings):
    case_folder_name = f"{settings.case_name}_{settings.input_file_name.replace('.', '_')}"
    fname = f"{country}_log.txt"
    fpath = Path(ROOT_DIR) / "output_files" / case_folder_name / country
    ffname = Path(ROOT_DIR) / "output_files" / case_folder_name / country / fname
    if not fpath.exists():
        fpath.mkdir(parents=True)

    fh = logging.FileHandler(filename=ffname, mode='w')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s: %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
