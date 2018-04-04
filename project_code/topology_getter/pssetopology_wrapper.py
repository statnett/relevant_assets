import pickle

try:
    from cPickle import loads
except:
    from pickle import loads


from uuid import uuid1

import execnet
import pssetopology

from serviceenumsandcontants import Python27Path


def add_db_id_to_all_components(topology, use_db):
    if use_db:
        topology.all_components.db_id
    else:
        for comp in topology.all_components:
            comp.db_id = uuid1()


def get_topology(case_path_dict, debug_print=True):
    gw = execnet.makegateway("popen//python={}".format(Python27Path))
    channel = gw.remote_exec("import sys; from definitions import TOPOLOGY_DIR; sys.path.append(TOPOLOGY_DIR)")
    channel = gw.remote_exec(pssetopology)
    channel.send((
        case_path_dict
    ))
    end = channel.receive()
    with open("temp", 'rb') as f:
        topology = pickle.load(f, encoding='latin-1')
    gw.exit()

    return topology


if __name__ == '__main__':
    # ffname = r'P:\PSS-Data\norge\norge_d08h.sav'
    # ffname = r'C:\code\relevant_assets\source_files\Norden2018_tunglast_01A.sav'
    ffname = r'C:\code\relevant_assets\source_files\IEEE300Bus.sav'
    topology = get_topology({0: ffname})
    pass
