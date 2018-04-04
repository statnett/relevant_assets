from serviceenumsandcontants import BusType


def append_branch_to_dict(branch, bus_to_branch_dict):
    from_bus_number = branch.from_bus.number
    if from_bus_number not in bus_to_branch_dict:
        bus_to_branch_dict[from_bus_number] = [branch]
    else:
        bus_to_branch_dict[from_bus_number].append(branch)

    to_bus_number = branch.to_bus.number
    if to_bus_number not in bus_to_branch_dict:
        bus_to_branch_dict[to_bus_number] = [branch]
    else:
        bus_to_branch_dict[to_bus_number].append(branch)

    if branch.other_bus:
        other_bus_number = branch.other_bus.number
        if other_bus_number not in bus_to_branch_dict:
            bus_to_branch_dict[other_bus_number] = [branch]
        else:
            bus_to_branch_dict[other_bus_number].append(branch)


class MonsterTopology:
    """ Main class for storing and manipualting the underlying grid network

    The data is stored in a list and in a dict for quick access in other parts
    of the program. Especially when results are written to the database it is
    useful to have the grid data in dicts.

    """
    def __init__(self):
        self.bus_dict = {}
        self.two_winding_transformer_dict = {}
        self.three_winding_transformer_dict = {}
        self.machine_dict = {}
        self.msl_children = dict()
        self.msl_parents = dict()
        self.load_dict = {}
        self.line_dict = {}
        self.msl_and_line_dict = {}
        self.contingency_components_dict = {}

    def __str__(self):
        out = 'Number of buses: {}\n'.format(len(self.bus_dict))
        if self.line_dict:
            out += 'Number of lines: {}\n'.format(len(self.line_dict))
        if self.two_winding_transformer_dict:
            out += 'Number of two winding transformers: {}\n'.format(
                len(self.two_winding_transformer_dict)
            )
        if self.three_winding_transformer_dict:
            out += 'Number of three winding transformers: {}\n'.format(
                len(self.three_winding_transformer_dict)
            )
        return out

    def set_relay_activation(self):
        components = self.msl_and_line_dict.values() + self.two_winding_transformer_dict.values()
        for component in components:
            component.set_activation()

    def limit_topology_by_settings(self, settings):
        all_components = self.get_all_components(settings.split_msl)
        for comp in all_components:
            if _comp_in_range(comp, settings):
                self.contingency_components_dict[comp.get_sorted_short_tuple()] = comp

    @staticmethod
    def _get_branch_component(branches, from_bus, to_bus, branch_id):
        for branch in branches.values():
            if branch.identificator == branch_id and (
                    branch.from_bus == from_bus and branch.to_bus == to_bus or
                    branch.from_bus == to_bus and branch.to_bus == from_bus
            ):
                return branch

    def get_two_winding_transformer_component(self, from_bus, to_bus, branch_id):
        return self._get_branch_component(
            self.two_winding_transformer_dict, from_bus, to_bus, branch_id
        )

    def get_line_component(self, from_bus, to_bus, branch_id):
        return self._get_branch_component(
            self.line_dict, from_bus, to_bus, branch_id
        )

    def _branches_dict_values(self, split_msl=False):
        all_branches = self.line_dict.values() + self.two_winding_transformer_dict.values()
        all_branches += self.three_winding_transformer_dict.values()
        return all_branches

    def monitored_branches(self, areas):
        return [branch for branch in self._branches_dict_values() if branch.monitor_this(areas)]

    def set_up_island_finder(self, split_msl):
        bus_to_branch_dict = {}
        bus_to_branch_dict_outer_areas = {}
        self.branch_dict = bus_to_branch_dict
        self.bus_to_branch_dict_outer_areas = bus_to_branch_dict_outer_areas

        self.tie_line_buses = set()

        all_branches = self._branches_dict_values()
        if split_msl:
            all_branches += self.msl_children.values()
        else:
            all_branches += self.msl_parents.values()

        for branch in all_branches:
            append_branch_to_dict(branch, bus_to_branch_dict)
            if branch.get_sorted_short_tuple() not in self.contingency_components_dict:
                append_branch_to_dict(branch, bus_to_branch_dict_outer_areas)

        for branch in self.contingency_components_dict.values():
            for bus in branch.get_busnumbers():
                if bus in bus_to_branch_dict_outer_areas:
                    self.tie_line_buses.add(bus)
        self.find_ways_to_swingbus()

    def _swing_buses(self):
        return {bus for bus in self.bus_dict
                if self.bus_dict[bus].from_bus.bus_type == BusType.swing.get_index()}

    def find_ways_to_swingbus(self):
        self.ways_to_swingbus = self._swing_buses()

        for component in self.tie_line_buses:
            searched_buses = set()
            to_search = [component]
            swingbus_found = False
            while to_search and not swingbus_found:
                explore_from = to_search.pop()
                searched_buses.add(explore_from)
                try:
                    edges = self.bus_to_branch_dict_outer_areas[explore_from]
                except KeyError:
                    edges = []
                for edge in edges:
                    for bus in edge.get_busnumbers():
                        if bus in self.ways_to_swingbus:
                            self.ways_to_swingbus = self.ways_to_swingbus.union(searched_buses)
                            swingbus_found = True
                            break
                        elif bus not in searched_buses:
                            to_search.append(bus)
                    if swingbus_found:
                        break

    def _add_start_points(self, start_points, component):
        for bus in component.component.get_busnumbers():
            start_points.add(bus)

    def find_islands(self, contingency):
        start_points = set()
        contingency_component_ids = set()
        for component in contingency.components:
            if component.is_connection():
                self._add_start_points(start_points, component)
                contingency_component_ids.add(component.component.db_id)

        islands = list()
        for start_bus in start_points:
            found = {start_bus}
            to_search = [start_bus]
            swingbus_found = False
            while to_search and not swingbus_found:
                explore_from = to_search.pop()
                found.add(explore_from)
                edges = [branch for branch in self.branch_dict[explore_from]
                         if branch.db_id not in contingency_component_ids]
                for edge in edges:
                    for bus in edge.get_busnumbers():
                        if bus in self.ways_to_swingbus:
                            swingbus_found = True
                            break
                        elif bus not in found:
                            to_search.append(bus)
                    if swingbus_found:
                        break
            if not swingbus_found and (
                    not islands or start_bus not in {i for i_set in islands for i in i_set}
            ):
                islands.append(found)
        return islands

    def get_all_components(self, split_msl):
        self.msl_and_line_dict = dict(self.line_dict)
        if split_msl is None:
            self.msl_and_line_dict.update(self.msl_children)
            self.msl_and_line_dict.update(self.msl_parents)
        elif split_msl:
            self.msl_and_line_dict.update(self.msl_children)
        else:
            self.msl_and_line_dict.update(self.msl_parents)

        all_components = self.bus_dict.values() + \
            self.msl_and_line_dict.values() + \
            self.two_winding_transformer_dict.values() + \
            self.three_winding_transformer_dict.values() + \
            self.machine_dict.values() + \
            self.load_dict.values()

        return all_components


def _comp_in_range(comp, settings):
    area = settings.contingency_area
    low_voltage_limit = settings.contingency_low_voltage_limit
    high_voltage_limit = settings.contingency_high_voltage_limit
    zone = settings.contingency_zone
    component_types = settings.component_types
    contingency_internal_voltage = settings.contingency_internal_voltage
    contingency_internal_area = settings.contingency_internal_area

    return (
        _in_voltage_range(
            comp, low_voltage_limit, high_voltage_limit, contingency_internal_voltage
        ) and
        _in_area(comp, area, contingency_internal_area) and
        _in_zone(comp, zone) and
        (not component_types or comp.get_type() in component_types)
    )


def _in_voltage_range(comp, low_voltage_limit, high_voltage_limit, internal=False):
    """ Return True if :obj:`comp` is within the voltage limits.

    These limits are given in the settings file and is a way of
    restricting which components one puts into the contingencies.

    Parameters
    ==========
    comp: Component

    """
    if not low_voltage_limit and not high_voltage_limit:
        return True
    else:
        if internal:
            boolfun = all
        else:
            boolfun = any
        voltage = comp.get_base_voltage()
        return boolfun([low_voltage_limit <= voltage <= high_voltage_limit])


def _in_area(comp, contingency_area, internal=False):
    """ Return True if :obj:`comp` is in the specified area

    The specified area is given in the settings file and is a way of
    restricting which components one puts into the contingencies.

    Parameters
    ==========
    comp: Component

    """
    return connected(contingency_area, comp.get_area(), internal)


def _in_zone(comp, contingency_zone, internal=False):
    """ Return True if :obj:`comp` is in the specified zone

    The specified zone is given in the settings file and is a way of
    restricting which components one puts into the contingencies.

    Parameters
    ==========
    comp: Component

    """
    return connected(contingency_zone, comp.get_zone(), internal)


def connected(ar1, ar2, internal):
    if not ar1:
        return True
    else:
        if internal:
            return all([area in ar1 for area in ar2])
        else:
            return any(set(ar1).intersection(ar2))
