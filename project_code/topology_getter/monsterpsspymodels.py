import os
import tempfile


max_psse_int = 100000000
max_psse_float = 1.0000000200408773e+20


class Sensitivity():
    def __init__(self, psse_sensitivity):
        self.genvalues = self.get_bunch_dict_as_dict(psse_sensitivity.genvalues)
        self.loadvalues = self.get_bunch_dict_as_dict(psse_sensitivity.loadvalues)

    @staticmethod
    def get_bunch_dict_as_dict(bunch_dict):
        return {
            element_key:
            {
                child_element_key: child_element_value for child_element_key, child_element_value in
                element_value.iteritems()
            } for element_key, element_value in bunch_dict.iteritems()
        }

    def __contains__(self, key):
        return key in ['genvalues', 'loadvalues']

    def __getitem__(self, key):
        if key == 'genvalues':
            return self.genvalues
        elif key == 'loadvalues':
            return self.loadvalues
        else:
            raise KeyError(
                '''Don\'t have key {} in Sensitivity, only \'genvalues\'
                and \'loadvalues\''''.format(key)
            )


class AcccSolution():
    def __init__(self, psse_solution):
        self.cnvflag = psse_solution.cnvflag
        self.island = psse_solution.island
        self.lshedbus = psse_solution.lshedbus
        self.loadshed = psse_solution.loadshed
        self.ampflow = psse_solution.ampflow
        self.cnvcond = psse_solution.cnvcond
        self.ierr = psse_solution.ierr
        self.mvaflow = psse_solution.mvaflow
        self.volts = psse_solution.volts


class Rating():
    def __init__(self, rating):
        self.a = rating.a
        self.b = rating.b
        self.c = rating.c


class AcccSize():
    def __init__(self, acccsize):
        self.nmline = acccsize.nmline
        self.ninter = acccsize.ninter
        self.nmvbusrec = acccsize.nmvbusrec


class AcccSummary():
    def __init__(self, psse_summary):
        self.acccsize = AcccSize(psse_summary.acccsize)
        self.rating = Rating(psse_summary.rating)
        self.colabel = psse_summary.colabel
        self.melement = psse_summary.melement
        self.mvbuslabel = psse_summary.mvbuslabel
        self.mvrectype = psse_summary.mvrectype
        self.mvbusnum = [int(bus.split()[0]) for bus in self.mvbuslabel]


class CaspyModel():
    def __init__(self, caspy):
        self.pssbrn = CaspyBranshModel(caspy.pssbrn)
        self.pssbus = CaspyBusModel(caspy.pssbus)


class CaspyBusModel():
    def __init__(self, caspy_bus):
        self.num = caspy_bus['NUM']
        self.name = caspy_bus['NAME']
        self.baskv = caspy_bus['BASKV']
        self.area = caspy_bus['AREA']
        self.ide = caspy_bus['IDE']


# branch_data['FRMBUS'], branch_data['TOBUS'], branch_data['CKT'], branch_data['INDX2W']
class CaspyBranshModel():
    def __init__(self, caspy_branch):
        self.frmbus = caspy_branch['FRMBUS']
        self.tobus = caspy_branch['TOBUS']
        self.ckt = caspy_branch['CKT']
        self.indx2w = caspy_branch['INDX2W']
        self.stat = caspy_branch['STAT']


class LocalTemp(object):
    def __init__(self, name, suffix):
        self._name = name
        self._suffix = suffix

    def _write_to_file(self):
        if self._name is None:
            self._fid = tempfile.NamedTemporaryFile(suffix=self._suffix, delete=False)
            self._sub_str()
            self._fid.close()

    def _sub_str(self):
        pass

    def __str__(self):
        if self._name is None:
            return self._fid.name
        else:
            return self._name

    def cleanup(self):
        if self._name is None:
            os.unlink(self._fid.name)


class SubTempFile(LocalTemp):

    def __init__(
            self, name=None, areas=[], buses=[], jbuses={}, con_areas=[],
            mon_areas=[], con_voltage_lim=[], suffix='.sub'
    ):

        super(SubTempFile, self).__init__(name, suffix)

        self._areas = areas
        self._buses = buses
        self._jbuses = jbuses
        self._con_areas = con_areas
        self._mon_areas = mon_areas
        self._con_voltage_lim = con_voltage_lim

        self._write_to_file()

    def _sub_str(self):
        # Define subsystem "TotalSystem"
        self._fid.write('SUBSYSTEM \'TotalSystem\'\nAREAS 1 9000\nEND\n')
        # Define sub system areas
        for area in self._areas:
            self._fid.write('SUBSYSTEM \'AREA_{}\'\n'.format(area))
            self._fid.write('AREA {}\n'.format(area))
            self._fid.write('END\n')
        # Define subsystem buses
        for bus in self._buses:
            self._fid.write('SUBSYSTEM BUS_{}\n'.format(bus))
            self._fid.write('BUS {}\nEND\n'.format(bus))
        # Define subsystem for joined buses
        for subname in self._jbuses:
            self._fid.write('SUBSYSTEM {}\n'.format(subname))
            for bus in self._jbuses[subname]:
                self._fid.write('BUS {}\n'.format(bus))
            self._fid.write('END\n')
        # Define monitor system
        if self._mon_areas:
            self._fid.write('SUBSYSTEM \'MONITOR_SYSTEM\'\n')
            for area in self._mon_areas:
                self._fid.write('AREA {}\n'.format(area))
            self._fid.write('END\n')
        # Define contingency system
        if self._con_areas:
            self._fid.write('SUBSYSTEM \'CONTINGENCY_SYSTEM\'\n')
            for area in self._con_areas:
                self._fid.write('Join \'Group {}\'\n'.format(area))
                self._fid.write('   AREA {}\n'.format(area))
                self._fid.write('   KVRANGE {:0.2f} {:0.2f}\n'.format(*self._con_voltage_lim))
                self._fid.write('   END\n')
            self._fid.write('END\n')
        # End of file
        self._fid.write('END\n')


class MonTempFile(LocalTemp):
    def __init__(
            self, name=None, suffix='.mon', system='MONITOR_SYSTEM', voltage_range=[0.9, 1.1]
    ):
        super(type(self), self).__init__(name, suffix)
        self._mon_system = system
        self._voltage_range = voltage_range
        self._write_to_file()

    def _sub_str(self):
        if self._mon_system is not None:
            self._fid.write('MONITOR branches in subsystem \'{}\''.format(self._mon_system))
            self._fid.write(
                '\nMONITOR voltage range subsystem \'{}\''.format(self._mon_system)
            )
            for voltage in self._voltage_range:
                self._fid.write(' {}'.format(voltage))
            self._fid.write('\n')
        self._fid.write('END\n')


class ConTempFile(LocalTemp):
    def __init__(self, name=None, suffix='.con', system='CONTINGENCY_SYSTEM', contypes=None):
        super(type(self), self).__init__(name, suffix)
        self._con_system = system
        if contypes is None:
            self._contypes = ['single', 'parallel', 'busdouble']
        else:
            self._contypes = contypes
        self._write_to_file()

    def _sub_str(self):
        for contype in self._contypes:
            self._fid.write('{} branch in subsystem {}\n'.format(contype, self._con_system))
        self._fid.write('END\n')
