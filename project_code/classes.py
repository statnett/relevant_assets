import math
import enum

BranchTypeEnum = enum.Enum(value='BranchTypeEnum',
                           names=('Line', 'Coupler', 'Transformer',
                                  'Transformer2W', 'Transformer3W3', 'Transformer3W2'))


class Branch:
    n_of_branches = 0
    IATL_max = 5000  # Threshold above which IATL are regarded as infinite.
    Sbase = 1.0  # MVA, for p.u conversion.

    def __init__(self, name_from, name_to, order, impedance, PATL, v_base,
                 branch_type, display_name):
        self.index = Branch.n_of_branches
        self.name_from = name_from
        self.name_to = name_to
        self.name_branch = name_from + " " + name_to + " " + order
        self.display_name = display_name
        self.order = order
        self.country = None
        self.node_from = None
        self.node_to = None
        self.ring = 99
        self.connected = False
        self.is_tie_line = False
        self.type = branch_type
        self.v_base = v_base  # in kV
        self.impedance = impedance  # should be given in p.u.
        if PATL > Branch.IATL_max * math.sqrt(3) * self.v_base / 1000:
            self.PATL = 0
        else:
            self.PATL = PATL  # in MW
        self.PTDF = 1.0
        Branch.n_of_branches += 1

    def __str__(self):
        return f"Branch nr {self.index}: {self.type} '{self.name_branch}', "\
               f"impedance {self.impedance:.5f} pu, max power {self.PATL:.1f} MW, " \
               f"ring {self.ring}, is a tie line: {self.is_tie_line}"

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        return self.name_branch < other.name_branch

    def set_country(self):
        if (self.node_from is None) or (self.node_to is None):
            raise ValueError('Cannot set country for branch if there are not two '
                             'nodes connected to the branch.')
        if self.node_to.country != self.node_from.country:
            self.country = 'TIE'
            self.is_tie_line = True
            if self.type == BranchTypeEnum.Coupler:
                self.type = BranchTypeEnum.Line
        else:
            self.country = self.node_from.country

    def is_branch_a_tie_line(self):
        if self.is_tie_line:
            return True
        else:
            return self.node_from.is_x_node() or self.node_to.is_x_node()

    def connect_to_grid(self):
        self.connected = True
        for node in [self.node_from, self.node_to]:
            node.connect_to_grid()

    def insert_in_control_area(self):
        if not self.is_tie_line:
            for node in [self.node_from, self.node_to]:
                # print(f'Trying to insert node {node.index}: {node.name}')
                node.insert_in_control_area()

    def increase_ring(self, ring_idx):
        self.update_ring_nr_for_connected_nodes(ring_idx)
        self.update_ring_nr_for_branch()

    def update_ring_nr_for_connected_nodes(self, ring_idx):
        for (node1, node2) in [(self.node_from, self.node_to), (self.node_to, self.node_from)]:
            if not (node1.ring == ring_idx and node2.ring == 99):
                continue
            if not node2.is_x_node():
                node2.ring = ring_idx + 1
            else:  # if x-node: set x-node to lower ring, and update branch from x-node to outside.
                node2.ring = ring_idx
                for branch in node2.branches:
                    branch.increase_ring(ring_idx)

    def update_ring_nr_for_branch(self):
        self.ring = min((self.node_from.ring, self.node_to.ring))

    def remove(self, all_branches, all_nodes):
        """Removes branch, and all nodes only connected to that branch"""

        # Case 1: if one of the nodes is only conn to branch, then calling the node remove function
        # will remove the node, the branch, and the branch from the branch list of the other node.
        if len(self.node_from.branches) == 1:
            self.node_from.remove(all_branches, all_nodes)
            return
        elif len(self.node_to.branches) == 1:
            self.node_to.remove(all_branches, all_nodes)
            return

        # Case 2: if not case 1, then just remove from branch list from both nodes and remove branch
        for node in (self.node_from, self.node_to):
            node.branches = [branch for branch in node.branches if branch != self]
        all_branches.remove(self)
        # for i in range(len(all_branches)):
        #     all_branches[i].index = i
        # for i in range(len(all_nodes)):
        #     all_nodes[i].index = i

    @staticmethod
    def header():
        return "Index,Type,Name,Node From,Node To,Impedance_pu,PATL_MW,Ring,Tie-Line"

    def save_to_file_str(self):
        return f"{self.index},{self.type},{self.name_branch},{self.name_from},{self.name_to}," \
               f"{self.impedance:.5f},{self.PATL:.1f},{self.ring},{self.is_tie_line}"

    def apply_couplers(self, dict_couplers, nodes=None):
        """Applies couplers.
        Logic: a branch X from A to B now has to go from A to C. How to do this:
        1: X needs to be removed from the branch list of B.
        2: the to_node of X needs to change from B to C (name and actual node)
        3: the branch list of C needs to be appended with X
        4: the branch name has to be re-established based on new nodes
        """
        if self.name_from in dict_couplers:
            if self.node_from is not None:
                old_node_from = [n for n in nodes if n.name == self.name_from][0]
                old_node_from.branches.remove(self)
                self.node_from = [n for n in nodes if n.name == dict_couplers[self.name_from]][0]
                self.node_from.branches.append(self)
            self.name_from = dict_couplers[self.name_from]
        if self.name_to in dict_couplers:
            if self.node_to is not None:
                old_node_to = [n for n in nodes if n.name == self.name_to][0]
                old_node_to.branches.remove(self)
                self.node_to = [n for n in nodes if n.name == dict_couplers[self.name_to]][0]
                self.node_to.branches.append(self)
            self.name_to = dict_couplers[self.name_to]
        self.name_branch = self.name_from + " " + self.name_to + " " + self.order


class Node:
    nbNodes = 0
    ring_chars = 7  # Significant characters used to determined rings : 8, one ring per node; 7,

    # one ring per voltage level; 6, one ring per substation (all voltage)

    def __init__(self, name):
        self.index = Node.nbNodes
        self.country = None
        self.name = name
        self.branches = []
        self.generators = []
        self.ring = 99
        self.connected = False
        Node.nbNodes += 1

    def __str__(self, ):
        return f"Node {self.index}: '{self.name}', ring {self.ring}, " \
               f"connected: {self.connected}, branches {[elt.index for elt in self.branches]}"

    def insert_in_control_area(self):
        if self.ring == 99:
            self.ring = 0
            for branch in self.branches:
                # print(f'trying to insert branch {branch.index} to control area '
                #       f'({branch.type} {branch.name_branch})')
                branch.insert_in_control_area()

    def connect_to_grid(self):
        if not self.connected:
            self.connected = True
            for branch in self.branches:
                branch.connect_to_grid()

    def is_x_node(self):
        return self.country == 'X'

    def is_border(self):
        if len([branch for branch in self.branches if branch.is_branch_a_tie_line()]) > 0:
            return True
        else:
            return False

    @staticmethod
    def header():
        return "Index,Name,Ring,Connected,Branches"

    def save_to_file_str(self):
        return f"{self.index},{self.name},{self.ring},{self.connected}," \
               f"{[b.index for b in self.branches]}"

    def remove(self, all_branches, all_nodes):
        """Removes node. The following consequences:
        A: if you remove a node you should also remove all branches connected to that node:
            1: remove the actual branches
            2: remove the branches from the branch list that the opposite node has.
        B: remove the node itself.
        """

        for branch in self.branches:  # all branches in branch list of this node:
            all_branches.remove(branch)  # remove from the system-wide branch list
            other_node_on_branch = [node for node in [branch.node_from, branch.node_to]
                                    if node != self][0]
            other_node_on_branch.branches.remove(branch)  # remove from the branch list of opp. node

        all_nodes.remove(self)  # remove node from system-wide node list.

    def get_equivalent_node_name(self):
        if self.is_x_node():
            return self.name
        else:
            return self.name[:Node.ring_chars]


class GenerationUnit:
    n_of_generators = 0

    def __init__(self, name, power, name_suffix):
        self.index = GenerationUnit.n_of_generators
        self.node = None
        self.node_name = name
        if name_suffix is not '':
            self.name = name + '_' + name_suffix
        else:
            self.name = name
        self.power = power
        self.country = ""
        self.connected = False
        GenerationUnit.n_of_generators += 1

    def __str__(self):
        return f"Generator nr {self.index}: '{self.name}', max power {self.power:.1f} MW"

    def apply_couplers(self, dict_of_couplers):
        if self.node_name in dict_of_couplers:
            self.node_name = dict_of_couplers[self.node_name]


class Result_IF:
    def __init__(self, eltR, IFN1, nIFN1, IFN2, nIFN2, eltI, eltT, eltIn, eltTn, LODFit, LODFti):
        """
            Generates a result with :
            -eltR the element whose influence is assessed
            -IFN1 : the N-1 IF
            -nIFN1 : the normalized N-1 IF
            -IFN2 : the N-2 IF (according to CSAM)
            -nIFN2 : the normalized N-2 IF
            -eltI : a contingency i for which IFN2 is reached
            -eltT : an element from the CA for which IFN2 is reached
            -eltIn : a contingency i for which nIFN2 is reached
            -eltTn : an element from the CA for which nIFN2 is reached
        """
        self.eltR = eltR
        self.IFN1 = IFN1
        self.nIFN1 = nIFN1
        self.IFN2 = IFN2
        self.nIFN2 = nIFN2
        self.eltI = eltI
        self.eltT = eltT
        self.eltIn = eltIn
        self.eltTn = eltTn
        self.LODFit = LODFit
        self.LODFti = LODFti

    @staticmethod
    def header(country):
        sep = ','
        return f"List of R from {country} perspective" \
               f"{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}\n\n" \
               f"R{sep}Voltage level [kV]{sep}Country{sep}" \
               f"Type{sep}Normalized IF{sep}IF{sep}" \
               f"PATL R [MW]{sep}Ring R{sep}" \
               f"I for norm.IF{sep}" \
               f"T for norm.IF{sep}" \
               f"I IF{sep}" \
               f"T IF{sep}" \
               f"PATL for T norm.IF [MW]\n"

    def __str__(self):
        sep = ','
        return f"{self.eltR.display_name}{sep}{self.eltR.v_base:.0f}{sep}{self.eltR.country}{sep}" \
               f"{self.eltR.type}{sep}{self.nIFN2:.4f}{sep}{self.IFN2:.4f}{sep}" \
               f"{self.eltR.PATL:.0f}{sep}{self.eltR.ring}{sep}" \
               f"{self.eltIn.display_name} {self.eltIn.v_base:.0f} {self.eltIn.country}{sep}" \
               f"{self.eltTn.display_name} {self.eltTn.v_base:.0f} {self.eltTn.country}{sep}" \
               f"{self.eltI.display_name} {self.eltI.v_base:.0f} {self.eltI.country}{sep}" \
               f"{self.eltT.display_name} {self.eltT.v_base:.0f} {self.eltT.country}{sep}" \
               f"{self.eltTn.PATL:.0f}\n"


class Result_IF_generators:
    def __init__(self, name, power, IF, IF_branches_i, IF_branches_t,
                 IF_norm, IF_norm_branches_i, IF_norm_branches_t):
        """
            Generates a result with :
            -name: the element whose influence is assessed
            -power: the generator power
            -IF: the influence factor for this generator
            -IF_branches_i: branches i that have this IF for this generator
            -IF_branches_t: branches t that have this IF for this generator
            -IF_norm: normalized influence factor
            -IF_norm_branches_i: branches i that have this norm IF for this generator
            -IF_norm_branches_t: branches t that have this norm IF for this generator
        """
        self.name = name
        self.power = power
        self.IF = IF
        self.IF_branches_i = IF_branches_i
        self.IF_branches_t = IF_branches_t
        self.IF_norm = IF_norm
        self.IF_norm_branches_i = IF_norm_branches_i
        self.IF_norm_branches_t = IF_norm_branches_t

    @staticmethod
    def header(country):
        sep = ','
        return f"List of R for generators from {country} perspective" \
               f"{sep}{sep}{sep}{sep}{sep}{sep}{sep}{sep}\n\n" \
               f"R generator{sep}Power [MW]{sep}IF{sep}" \
               f"I for IF{sep}T for IF{sep}Normalized IF{sep}" \
               f"I for norm.IF{sep}" \
               f"T for norm.IF{sep}\n"

    def __str__(self):
        sep = ','
        return f"{self.name}{sep}"\
               f"{self.power:.1f}{sep}"\
               f"{self.IF:.4f}{sep}"\
               f"{str(self.IF_branches_i).replace('[', '').replace(']', '').replace(',',';')}{sep}"\
               f"{str(self.IF_branches_t).replace('[', '').replace(']', '').replace(',',';')}{sep}"\
               f"{self.IF_norm:.4f}{sep}"\
               f"{str(self.IF_norm_branches_i).replace('[', '').replace(']', '').replace(',',';')}{sep}"\
               f"{str(self.IF_norm_branches_t).replace('[', '').replace(']', '').replace(',',';')}{sep}\n"\


class FinalResult:
    def __init__(self, branches, nodes, generators, results, results_generators):
        self.branches = branches
        self.nodes = nodes
        self.generators = generators
        self.results = results
        self.results_generators = results_generators
