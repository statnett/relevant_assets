from component_errors import BusInitError


class BusDetails(object):
    def __init__(
            self,
            bus_number,
            bus_name,
            base_voltage,
            bus_type,
            areanum,
            zonenum,
            dummy):
        """ Class for a busbar network component

        The busbar is described according to the model in PSSE.

        Parameters
        ==========
        bus_number: int
            the bus number according to PSSE model
        bus_name: str
            the bus name string according to PSSE model
        base_voltage: double
            the bus base voltage according to PSSE model
        area_number: int (optional)
            area number according to PSSE model
        zone_number: int (optional)
            zone number according to PSSE model

        Examples
        ========
            >>> mybus = BusDetails(51112, 'FURUSET3', 300, 51, 503)

        """
        super(type(self), self).__init__()
        self._validate_input(bus_number, bus_name, base_voltage)
        self.number = bus_number
        self.name = bus_name
        self.base_voltage = float(base_voltage)
        self.area_number = areanum
        self.zone_number = zonenum
        self.dummy = dummy
        self.bus_type = bus_type

    @staticmethod
    def _validate_input(bus_number, bus_name, base_voltage):
        if not isinstance(bus_number, int):
            raise BusInitError('Bus numbers must be integers!')
        if not isinstance(bus_name, str):
            raise BusInitError('Bus bus_name must be a string!')
        if isinstance(base_voltage, str):
            raise BusInitError('Base voltage cannot be string!')

    def __eq__(self, other):
        """
        Two buses are equal if and only if the bus numbers,
        names and base voltages are equal.

        Examples
        ========
        Equal if the same object:
            >>> mybus = BusDetails(51112, 'FURUSET3', 300, 51, 503)
            >>> not_mybus = BusDetails(51112, 'FURUSET3', 300, 51, 503)
            >>> mybus == not_mybus
            True

        Also equal even if the zone is altered
            >>> not_mybus_either = BusDetails(51112, 'FURUSET3', 300, 51, 504)
            >>> mybus == not_mybus_either
            True

        Not equal if name is not equal:
            >>> mybus = BusDetails(51112, 'FURUSET3', 300, 51, 503)
            >>> could_be_mybus = BusDetails(51112, 'GRANSETH3', 300, 51, 503)
            >>> mybus == could_be_mybus
            False

        """
        if self is other:
            return True

        if isinstance(other, type(self)):
            return self.number == other.number and self.name == other.name and \
                self.base_voltage == other.base_voltage
        else:
            if isinstance(other, int):
                return self.number == other
            elif other is str:
                return self.name == other
            else:
                return False

    def __str__(self):
        """ Return the string representation of a bus

        Examples
        ========
            >>> mybus = BusDetails(51112, 'FURUSET3', 300, 51, 503)
            >>> mybus.__str__()
            'Bus 51112 FURUSET3 300.0'

        """

        return 'Bus %d %s %s' % (self.number, self.name, self.base_voltage)

    def __int__(self):
        return self.number

    def get_base_voltage(self):
        """ Return the base voltage of the bus

        """
        return self.base_voltage

    def get_area(self):
        """ Return the area number of the bus reffered to the area in PSSE

        """
        return self.area_number

    def get_zone(self):
        """ Return the zone number of the bus reffered to the zone in PSSE

        """
        return self.zone_number

    def is_dummy(self):
        # TODO: find out how it is possible to get an AttributeError here. Happens in test_screen
        # when all tests are run (not when test_screen is run separately).
        try:
            return self.dummy
        except AttributeError:
            return False

    def __hash__(self):
        return hash(self.number)
