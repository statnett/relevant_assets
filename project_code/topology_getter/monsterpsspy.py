import os
import sys
# must be here to support hdf5 combined with psse even when not used in file
import tables  # noqa: F401

# must be here to avoid "Invalid Floating-Point number"
import pandas  # noqa: F401


import monsterexceptions
from monsterpsspymodels import (
    AcccSummary, max_psse_int, max_psse_float, AcccSolution, Sensitivity, CaspyModel,
    SubTempFile, MonTempFile, ConTempFile
)
from serviceenumsandcontants import BusType


class RedirectStdStreams(object):
    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush()
        self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush()
        self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr


if not sys.maxsize > 2 ** 32:
    retries = 100
    while retries > 0:
        retries -= 1
        try:
            VER = 33

            psseloc = 'c:\\Program Files (x86)\\PTI\\PSSE{VER:d}'.format(
                VER=VER
            )
            pssepath = psseloc + os.sep + 'PSSBIN'
            pythonpath = []

            if VER == 34:
                pythonpath = [psseloc + os.sep + 'PSSPY27']

            sys.path = [
                pat for pat in sys.path if 'PTI' not in pat
            ] + [pssepath] + pythonpath + os.environ['PATH'].split(';')

            os.environ['PATH'] += ';' + pssepath
            # ############################
            #
            import psspy  # noqa:  E402
            import caspy  # noqa:  E402
            import pssarrays  # noqa:  E402
            import redirect  # noqa: E402
            from sharedconstantsandenums import psse_size, SolvedStatusEnum  # noqa:  E402

            redirect.psse2py()
            devnull = open(os.devnull, 'w')
            with RedirectStdStreams(stdout=devnull, stderr=devnull):
                psspy.psseinit(psse_size)
            break
        except:
            pass


class MonsterPssPy:
    @staticmethod
    def ping(stuff):  # used in tests
        return "ping_back " + stuff

    @staticmethod
    def _f():
        return max_psse_float

    @staticmethod
    def _i():
        return max_psse_int

    @staticmethod
    def savecase(fname):
        return CaspyModel(caspy.Savecase(fname))

    @staticmethod
    def newcase(options=None, basemva=None, basefreq=50, titl1=None, titl2=None):
        """Initialize a new power flow case. All existing working case data will be lost
        newcase(options, basemva, basefreq, titl1, titl2)

        OPTIONS - Is an array of two elements specifying units for ratings (used to set the percent
                  loading program option settings) (input; present program option setting by
                  default). The values are as follows:

        OPTIONS(1) - units for transformer ratings:
              > 0 current expressed as MVA.
              < 0 MVA.

        OPTIONS(2) - units for ratings of non-transformer branches:
              > 0 current expressed as MVA.
              < 0 MVA.

        BASEMVA - Is the system base MVA. Valid base MVA values range from greater than 0.0 to
                  10,000.0 (input; 100.0 by default).

        BASEFREQ - Is the system base frequency. Valid base frequency values range from greater than
                0.0 to less than 100.0 (input; present base frequency option setting by default).

        TITL1*60 - Is the first line of the new case title (input; blank by default).
        TITL2*60 - Is the second line of the new case title (input; blank by default).
        """
        ierr = psspy.newcase_2(options, basemva, basefreq, titl1, titl2)
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseNewcaseException(ierr, None)

    @staticmethod
    def transformer_percent_units(ival=None):
        """Set the transformer percent units option setting to either MVA or current expressed as MVA
         transformer_percent_units(ival)

         or:

         ival = transformer_percent_units()

         IVAL Value of the option setting

         IVAL = 0 MVA.
         IVAL = 1 current expressed as MVA

        """
        return_value = psspy.transformer_percent_units(ival=ival)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        if isinstance(return_value, int):
            ierr = return_value
            val = None
        else:
            (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseTransformerUnitsException(ierr, val)
        return val

    @staticmethod
    def systot(string, **kwds):
        """Return complex system-wide values
        cmpval = systot(string)

        STRING - indicating  the system total desired (input):
          'LOAD'   System load (net of load plus in-service distributed generation on
                   load feeder).
          'LDGN'   Distributed generation on load feeder.
          'GEN'    System generation.
          'LOSS'   System losses.
          'INDMAC' System induction machine powers.
          'INDGEN' System induction generator powers.
          'INDMOT' System induction motor powers.
          'FACTSH' FACTS device shunt elements.
          'BSSHNT' bus fixed and switched shunt elements.
          'LNSHNT' line shunts and transformer magnetizing shunt elements.
          'ALSHNT' FACTS device, fixed, switched, line, and transformer magnetizing
                   shunt elements..
        """
        return_value = psspy.systot(string=string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseSystotException(ierr, val)
        return val

    @staticmethod
    def accc_summary(fname):
        """AC Contingency monitored element labels
        rlst = pssarrays.accc_summary(accfile)
        where:

        Returned object 'rlst' contains the following attributes:

        accfile - Contingency Solution Output file (input, no default allowed)

        rlst.ierr Is the error code
            = 0 no error occurred
            = 4 error opening accfile
            = 5 error reading accfile
            = 6 prerequisite requirements for function not met

        rls.acccsize

          .nmline      - Number of monitored branches
          .ninter      - Number of monitored interfaces
          .ncase       - Number of contingencies + 1 (for base case)
          .nmvbus      - Number of voltage monitored buses
          .nmvrec      - Number of voltage monitored records
          .nmvbusrec   - Number of voltage monitored bus records
          .nbus        - Number of buses in the case
          .ncntlshed   - Number of load sheds due to dispatch and contingency
          .ntrplshed   - Number of load sheds due to tripping
          .ncactlshed  - Number of load sheds due to corrective actions
          .ncactgdisp  - Number of generation dispatched due to corrective actions
          .ncactphsftr - Number of phase shifter changed due to corrective actions

        rlst.casetitle
          .line1 Is the case short title line 1
          .line2 Is the case short title line 2

        rlst.file
          .acc - Name of contingency output (.acc) file
          .sav - Name of saved case (.sav) file
          .dfx - Name of distribution factor data (.dfx) file
          .sub - Name of subsystem definition data (.sub) file
          .mon - Name of monitored element data (.mon) file
          .con - Name of contingency description data (.con) file
          .thr - Name of load throwover data (.thr) file
          .inl - Name of unit inertia and governor data (.inl) file
          .trp - Name of tripping element data (.trp) file

        (list of length nmline + ninter)
        rlst.melement - of monitored branch and interface names
        rlst.rating.a - of monitored element rating A
        rlst.rating.b - of monitored element rating B
        rlst.rating.c - of monitored element rating C

        (list of length nmvbusrec)
        rlst.mvbuslabel -  of monitored voltage bus label
        rlst.mvreclabel -  of monitored voltage record label
        rlst.mvrecmax   -  of monitored voltage bus maximum
        rlst.mvrecmin   -  of monitored voltage bus minimum
        rlst.mvrectype  -  of monitored voltage record type (RANGE / DEVIATION)

        rlst.colabel - list of length (ncase) of contingency labels
        rlst.busname - list of length (nbus) of extended bus names

        """
        return AcccSummary(pssarrays.accc_summary(fname))

    @staticmethod
    def dscn(bus):
        """Electrcially disconnect a bus
        dscn(bus)

        BUS The number of the bus to disconnect
        """
        ierr = psspy.dscn(bus=bus)
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseDscnException(ierr, None)

    @staticmethod
    def dfax(options=None, subfile=None, monfile=None, confile=None, dfxfile=None, **kwds):
        """Construct a Distribution Factor Data File (activity DFAX).

        dfax(options, subfile, monfile, confile, dfxfile)
        where:

        OPTIONS - Is an array of three elements specifying calculation options (input).
        The value of each element is as follows.

        OPTIONS(1) distribution factor option flag (1 by default).
          = 0 do not calculate distribution factors (i.e., DFAX,AC).
          = 1 calculate distribution factors.

        OPTIONS(2) monitored element sorting flag (0 by default).
          = 0 do not sort (i.e., leave in Monitored Element Description File order).
          = 1 sort.

        OPTIONS(3) out-of-service monitored branch flag (0 by default).
          = 0 eliminate out-of-service branch from monitored branches.
          = 1 keep out-of-service branch in monitored branches.

        SUBFILE*260 - Subsystem Description File; blank for none (input; blank by default).
        MONFILE*260 - Monitored Element Description File (input; no default allowed).
        CONFILE*260 - Contingency Description Data File (input; no default allowed).
        DFXFILE*260 - Distribution Factor Data File (input; no default allowed).
        """
        ierr = psspy.dfax_2(options, subfile, monfile, confile, dfxfile)
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseDfaxException(ierr, None)

    @staticmethod
    def brnflo(ibus=None, jbus=None, ickt=None):
        """Return the complex branch flow (P+jQ) as calculated at IBUS.
         cmpval = brnflo(ibus, jbus, ickt)

        IBUS - From bus number

        JBUS - To bus number

        ICKT - Circuit or multisection line identifier

        cmpval - Complex branch flow
        """
        return_value = psspy.brnflo(ibus, jbus, ickt)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseBrnfloException(ierr, val)
        return val

    @staticmethod
    def sensitivity_flow_to_mw(
            ibus, jbus, mainsys, dfxfile, kbus=0, ckt=1, netmod=None, brnflowtyp=None,
            transfertyp=None, oppsystyp=None, dispmod=1, toln=None, oppsys=None
    ):
        """Calculate sensitivity factors of a branch flow to MW power at generator buses and MW power at
                load buses.
        """
        return Sensitivity(pssarrays.sensitivity_flow_to_mw(
            ibus, jbus, mainsys, dfxfile, kbus, ckt, netmod, brnflowtyp,
            transfertyp, oppsystyp, dispmod, toln, oppsys
        ))

    @staticmethod
    def aareaint(sid=None, flag=None, string=None, **kwds):
        """Return an array of integer values for subsystem areas
        iarray = aareaint(sid, flag, string)

        SID Defines the area subsystem to be used (input; -1 by default).
          SID = a negative value, to instruct the API to assume a subsystem containing all areas in
                the working case.
          SID = a valid area subsystem identifier. Valid subsystem identifiers range from 0 to
                11. Subsystem SID must have been previously defined.

        FLAG Is a flag indicating which subsystem areas to include (input; 1 by default).
          FLAG = 1 for only subsystem areas with at least one ac bus assigned to them.
          FLAG = 2 for subsystem areas with any equipment (ac buses, loads, induction machines,
                   and/or dc buses) assigned to them.

        NSTR Is the number of elements in STRING (1 < NSTR < 50 ) (input; no default allowed).

        STRING(NSTR) Is an array of NSTR elements specifying NSTR of the following strings
                     indicating the area quantities desired (input; no default allowed):
          'NUMBER' Area number.
          'SWING' Number of the area swing bus used for area interchange control purposes.
          'BUSES' Number of ac buses assigned to the area.
          'LOADS' Number of loads assigned to the area.
          'INDMACS' Number of induction machines assigned to the area.
          'DCBUSES' Number of dc buses assigned to the area.
        """
        return_value = psspy.aareaint(sid, flag, string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAareaException(ierr, array)
        return array

    @staticmethod
    def accc_solution(accfile=None, colabel=None, stype=None, busmsm=0.5, sysmsm=5.0):
        """Returns ACCC post-contingency, post-tripping or post-corrective action solution monitored MVA
                   flows, ampere flows and bus voltages for one contingency.
        rlst = pssarrays.accc_solution(accfile, colabel, stype, busmsm, sysmsm)

        where:

          accfile Is the name of Contingency Solution Output file (input, no default allowed),
                  maximum string length=260

          colabel Is the name of contingency label to get ACCC solution for, only one label allowed
                  (input, no default allowed), maximum string length=12

          stype Is the name of solution type to get (input, contingency by default), allowed values:
                contingency, con, tripping, trp, caction, contingency action, cor

          busmsm Is the value of bus mismatch tolerance in MVA (input, 0.5 MVA by default)
          sysmsm Is the value of system mismatch tolerance in MVA (input, 5.0 MVA by default)

        Returned object 'rlst' contains the following attributes:

          rlst.ierr Is the error code
              - 0 no error occurred
              - 4 error opening accfile
              - 5 error reading accfile
              - 6 prerequisite requirements for function not met

          rlst.codesc Is the list of length (up to 16) of contingency events description, maximum
                      string length=152

          rlst.cnvflag Is the convergence status (True when converged)
          rlst.cnvcond Is the convergence condition description, maximum string length=34
          rlst.island Is the number of islands
          rlst.mvaworst Is the worst MVA mismatch
          rlst.mvatotal Is the total MVA mismatch
          rlst.volts Is a list of length (nmvbusrec) of monitored bus voltage in pu
          rlst.mvaflow Is a list of length (nmline+ninter) of monitored branch and interface MVA
                       flow
          rlst.ampflow Is a list of length (nmline) of monitored branch ampere flow

          rlst.lshedbus Is a list of extended bus names of the load shed buses, maximum string
                        length=25, list length:
               - ncntlshed, for post-contingency solution
               - ntrplshed, for post-tripping solution
               - ncactlshed, for post-corrective action solution
        """
        return AcccSolution(pssarrays.accc_solution(accfile, colabel, stype, busmsm, sysmsm))

    @staticmethod
    def accc_parallel(
            tol=None, options=None, label=None, dfxfile=None,
            accfile=None, thrfile=None, inlfile=None, zipfile=None
    ):
        """Run parallel implementation of the AC contingency calculation function
        accc_parallel_2(tol, options, label, dfxfile, accfile, thrfile, inlfile, zipfile)

        TOL - The mismatch tolerance (input; Newton solution convergence tolerance, TOLN, by
             default).

        OPTIONS - Array of eleven elements specifying solution options (input). The values are as
                 follows:

        OPTIONS(1) tap adjustment flag (tap adjustment option setting by default).
          = 0 disable.
          = 1 enable stepping adjustment.
          = 2 enable direct adjustment.

        OPTIONS(2) area interchange adjustment flag (area interchange adjustment option setting by
                  default).
          = 0 disable.
          = 1 enable using tie line flows only in calculating area interchange.
          = 2 enable using tie line flows and loads in calculating area interchange.

        OPTIONS(3) phase shift adjustment flag (phase shift adjustment option setting by default).
          = 0 disable.
          = 1 enable.

        OPTIONS(4) dc tap adjustment flag (dc tap adjustment option setting by default).
          = 0 disable.
          = 1 enable.

        OPTIONS(5) switched shunt adjustment flag (switched shunt adjustment option setting by
                  default).
          = 0 disable.
          = 1 enable.
          = 2 enable continuous mode, disable discrete mode.

        OPTIONS(6) solution method flag (0 by default).
          = 0 FDNS.
          = 1 FNSL.
          = 2 optimized FDNS.

        OPTIONS(7) non-divergent solution flag (non-divergent solution option setting by default).
          = 0 disable.
          = 1 enable.

        OPTIONS(8) induction motor treatment flag (applied when an induction motor fails to solve
                  due to low terminal bus voltage, 0 by default)
          = 0 stall.
          = 1 trip.

        OPTIONS(9) induction machine failure flag( 0 by default)
          = 0 treat contingency as non-converged if any induction machines are placed in the
              "stalled" or "tripped" state.
          = 1 treat contingency as solved if it converges, even if any induction machines are
            placed in the "stalled" or "tripped" state.

        OPTIONS(10) dispatch mode (0 by default)
          = 0 disable.
          = 1 subsystem machines (reserve).
          = 2 subsystem machines (pmax).
          = 3 subsystem machines (inertia).
          = 4 subsystem machines (governor droop).

        OPTIONS(11) ZIP archive flag (0 by default)
          = 0 do not write a ZIP archive file.
          = 1 write a ZIP archive using the file specified as ZIPFILE.

        LABEL*12 Is the name of the generation dispatch subsystem (blank by default, no default
                allowed if OPTIONS(10) is not 0).
        DFXFILE*260 - Distribution Factor Data file (input; no default allowed).
        ACCFILE*260 - Contingency Solution Output file (input; no default allowed).
        THRFILE*260 - Load Throwover Data file (input; blank by default).
        INLFILE*260 - Unit Inertia and Governor Data File (input; blank by default).
        ZIPFILE*260 - ZIP Archive Output File (input; blank by default).
        """
        ierr = psspy.accc_parallel_2(
            tol, options, label, dfxfile, accfile, thrfile, inlfile, zipfile
        )
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseAcccParallelException(ierr, None)

    @staticmethod
    def accc_with_dsp(
            tol=None, options=None, label=None, dfxfile=None,
            accfile=None, thrfile=None, inlfile=None, zipfile=None
    ):
        """Run the AC contingency calculation function
        accc_parallel_2(tol, options, label, dfxfile, accfile, thrfile, inlfile, zipfile)

        TOL - The mismatch tolerance (input; Newton solution convergence tolerance, TOLN, by
              default).

        OPTIONS - Array of eleven elements specifying solution options (input). The values are as
                  follows:

        OPTIONS(1) tap adjustment flag (tap adjustment option setting by default).
           = 0 disable.
           = 1 enable stepping adjustment.
           = 2 enable direct adjustment.

        OPTIONS(2) area interchange adjustment flag (area interchange adjustment option setting by
                   default).
           = 0 disable.
           = 1 enable using tie line flows only in calculating area interchange.
           = 2 enable using tie line flows and loads in calculating area interchange.

        OPTIONS(3) phase shift adjustment flag (phase shift adjustment option setting by default).
           = 0 disable.
           = 1 enable.

        OPTIONS(4) dc tap adjustment flag (dc tap adjustment option setting by default).
           = 0 disable.
           = 1 enable.

        OPTIONS(5) switched shunt adjustment flag (switched shunt adjustment option setting by
                   default).
           = 0 disable.
           = 1 enable.
           = 2 enable continuous mode, disable discrete mode.

        OPTIONS(6) solution method flag (0 by default).
           = 0 FDNS.
           = 1 FNSL.
           = 2 optimized FDNS.

        OPTIONS(7) non-divergent solution flag (non-divergent solution option setting by default).
           = 0 disable.
           = 1 enable.

        OPTIONS(8) induction motor treatment flag (applied when an induction motor fails to solve
                   due to low terminal bus voltage, 0 by default)
           = 0 stall.
           = 1 trip.

        OPTIONS(9) induction machine failure flag( 0 by default)
           = 0 treat contingency as non-converged if any induction machines are placed in the
               "stalled" or "tripped" state.
           = 1 treat contingency as solved if it converges, even if any induction machines are
             placed in the "stalled" or "tripped" state.

        OPTIONS(10) dispatch mode (0 by default)
           = 0 disable.
           = 1 subsystem machines (reserve).
           = 2 subsystem machines (pmax).
           = 3 subsystem machines (inertia).
           = 4 subsystem machines (governor droop).

        OPTIONS(11) ZIP archive flag (0 by default)
           = 0 do not write a ZIP archive file.
           = 1 write a ZIP archive using the file specified as ZIPFILE.

        LABEL*12 Is the name of the generation dispatch subsystem (blank by default, no default
                 allowed if OPTIONS(10) is not 0).
        DFXFILE*260 - Distribution Factor Data file (input; no default allowed).
        ACCFILE*260 - Contingency Solution Output file (input; no default allowed).
        THRFILE*260 - Load Throwover Data file (input; blank by default).
        INLFILE*260 - Unit Inertia and Governor Data File (input; blank by default).
        ZIPFILE*260 - ZIP Archive Output File (input; blank by default).
        """
        ierr = psspy.accc_with_dsp_3(
            tol, options, label, dfxfile, accfile, thrfile, inlfile, zipfile
        )
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseAcccParallelException(ierr, None)

    @staticmethod
    def inlf(options=None, ifile=None, **kwds):
        """Run the inertial and governor response power flow calculation
        inlf(options, ifile)

        OPTIONS - Is an array of eight elements specifying solution options (input). The values are
                 as follows:
        OPTIONS(1) solution type (0 by default).
           = 0 inertial.
           = 1 governor response.
        OPTIONS(2) tap adjustment flag (tap adjustment option setting by default).
           = 0 disable.
           = 1 enable stepping adjustment.
           = 2 enable direct adjustment.
           = -1 solution type default (inertial => disable; governor => stepping).
        OPTIONS(3) phase shift adjustment flag (phase shift adjustment option setting by default).
           = 0 disable.
           = 1 enable.
           = -1 solution type default (inertial => disable; governor => enable).
        OPTIONS(4) dc tap adjustment flag (dc tap adjustment option setting by default).
           = 0 disable.
           = 1 enable.
           = -1 solution type default (inertial => disable; governor => enable).
        OPTIONS(5) switched shunt adjustment flag (switched shunt adjustment option setting by
                  default).
           = 0 disable.
           = 1 enable.
           = 2 enable continuous mode, disable discrete mode.
           = -1 solution type default (inertial => enable; governor => enable).
        OPTIONS(6) generator var limit flag (-1 (inertial) or 99 (governor) by default).
           = 0 apply var limits immediately.
           = >0 apply var limits on iteration n (or sooner if mismatch gets small).
           = -1 ignore var limits.
        OPTIONS(7) induction motor treatment flag; applied when an induction motor fails to solve
                  due to low terminal voltage (0 by default).
           = 0 stall.
           = 1 trip.
        OPTIONS(8) missing active power limits flag (only used in governor response power flow) (0
                  by default).
           = 0 pre-PSSE-29 approach (0.0 to 1.0 pu for machines with no Unit Inertia and Governor
               Data File record read; working case values for machines with PMAX defaulted on ECDI
               data record).
           = 1 0.0 to 1.0 pu for both categories of machines.
           = 2 working case values for both categories ofmachines.

        IFILE*260 Is the name of Unit Inertia and Governor Data File; blank for none (input; blank
                 by default).
        """
        ierr = psspy.inlf(options, ifile, **kwds)
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseInlfException(ierr, None)

    @staticmethod
    def diff(sid=None, all=None, apiopt=None, status=None, thrsh=None, cfile=None, **kwds):
        return psspy.diff(
            sid=sid, all=all, apiopt=apiopt, status=status, thrsh=thrsh, cfile=cfile, **kwds
        )

    @staticmethod
    def gdif(sid=None, all=None, apiopt=None, namarg=None, filarg=None, **kwds):
        return psspy.gdif(sid=sid, all=all, apiopt=apiopt, namarg=namarg, filarg=filarg, **kwds)

    @staticmethod
    def inimsl(ibus=None, jbus=None, ickt=None, **kwds):
        ierr = psspy.inimsl(ibus=ibus, jbus=jbus, ickt=ickt, **kwds)
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseIniMslException(ierr, None)

    @staticmethod
    def find_multisections(sid, flag):
        (buslist,) = MonsterPssPy.abusint(
            sid=sid, flag=flag, string='NUMBER'
        )
        multisections = []

        def nxtbrn_append(ibus, multisections):
            while True:
                try:
                    jbus, ickt = MonsterPssPy.nxtbrn(ibus)
                    if '&' in ickt:
                        multisections.append((ibus, jbus, ickt))
                except monsterexceptions.PsseNxtBrnException:
                    break

        for ibus in buslist:
            try:
                MonsterPssPy.inibrx(ibus, 1)
                nxtbrn_append(ibus, multisections)
            except monsterexceptions.PsseIniBrxException:
                pass
        return multisections

    @staticmethod
    def get_sfiles():
        return psspy.sfiles()

    @staticmethod
    def getcontingencysavedcase(pathzip=None, isvfile=None):
        """Place the working case in the form of a specified system condition as calculated during a
        previous run of one of the members of the the AC contingency calculation family. This
        function retrieves data from a ZIP Archive Ouptut File that was created during the
        contingency calculation.

        getcontingencysavedcase(pathzip, isvfile)

        PATHZIP*260 - ZIP Archive Output File (input; no default allowed).

        ISVFILE*260 - Incremental Saved Case File (.isv file) contained in PATHZIP (input; no
                      default allowed).
        """
        ierr = psspy.getcontingencysavedcase(pathzip, isvfile)
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseGetContingencySavedCaseException(ierr, None)

    @staticmethod
    def save(sfile=None):

        return psspy.save(sfile=sfile)

    @staticmethod
    def case(sfile=None):
        ierr = psspy.case(sfile=sfile)
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseInitializationException(ierr, None, sfile)

    @staticmethod
    def number_threads(ival=None):

        if ival is None:
            return psspy.number_threads()
        else:
            return psspy.number_threads(ival)

    @staticmethod
    def agenbusreal(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.agenbusreal(sid=sid, flag=flag, string=string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAgenbusException(ierr, array)
        return array

    @staticmethod
    def agenbusint(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.agenbusint(sid=sid, flag=flag, string=string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAgenbusException(ierr, array)
        return array

    @staticmethod
    def aloadint(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.aloadint(sid=sid, flag=flag, string=string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAloadException(ierr, array)
        return array

    @staticmethod
    def aloadchar(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.aloadchar(sid=sid, flag=flag, string=string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAloadException(ierr, array)
        return array

    @staticmethod
    def alodbusint(sid=None, flag=None, string=None, **kwds):
        ierr, intval = psspy.alodbusint(sid=sid, flag=flag, string=string, **kwds)
        if string == 'TYPE':
            intval[0] = [BusType.get_enum(val) for val in intval[0]]
        elif isinstance(string, list) and 'TYPE' in string:
            loc = string.index('TYPE')
            intval[loc] = [BusType.get_enum(val) for val in intval[loc]]
        if ierr:
            raise monsterexceptions.PsseAlodBusException(ierr, intval)
        return intval

    @staticmethod
    def aloadcplx(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.aloadcplx(sid=sid, flag=flag, string=string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAloadException(ierr, array)
        return array

    @staticmethod
    def alodbuscplx(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.alodbuscplx(sid=sid, flag=flag, string=string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAlodBusException(ierr, array)
        return array

    @staticmethod
    def conl(sid=None, all=None, apiopt=None, status=None, loadin=None, **kwds):

        return psspy.conl(sid=sid, all=all, apiopt=apiopt, status=status, loadin=loadin, **kwds)

    @staticmethod
    def load_chng(i=None, id=None, intgar=None, realar=None, **kwds):
        """Modify the data of an existing load in the working case
        load_data(i, id, intgar, realar)

        i  - Is the bus number (input; no default allowed).
        id - (char*2) Is the load data identifier (input; '1' by default).

        INTGAR(6):
          INTGAR(1) STATUS, load status (1 by default).
          INTGAR(2) AREA, area number (area of bus I by default).
          INTGAR(3) ZONE, zone number (zone of bus I by default).
          INTGAR(4) OWNER, owner number (owner of bus I by default).
          INTGAR(5) SCALE, load scaling flag (0 = fixed, non-conforming;
                           1 = scalable, conforming) (1 by default).
          INTGAR(6) INTRPT, interruptible load flag (0 = non-interruptible;
                           1 = interruptible) (0 by default).
          INTGAR(7) DgenM, load distributed generation (Dgen) flag
                           (0 = Dgen is OFF; 1 = Dgen is ON) (0 by default).

        REALAR(6):
          REALAR(1) PL, constant power active load (0.0 by default).
          REALAR(2) QL, constant power reactive load (0.0 by default).
          REALAR(3) IP, constant current active load (0.0 by default).
          REALAR(4) IQ, constant current reactive load (0.0 by default).
          REALAR(5) YP, constant admittance active load (0.0 by default).
          REALAR(6) YQ, constant admittance reactive load (0.0 by default).
          REALAR(7) DgenP, Ditributed Generation active power (0.0 by default).
          REALAR(8) DgenQ, Ditributed Generation reactive power (0.0 by default)
        """
        ierr = psspy.load_chng_4(i=i, id=id, intgar=intgar, realar=realar, **kwds)
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseLoadDataException(ierr, None, i, id)

    @staticmethod
    def bsys(
            sid=None, usekv=None, basekv=None, numarea=None, areas=None, numbus=None,
            buses=None, numowner=None, owners=None, numzone=None, zones=None, **kwds
    ):
        """Define a bus sybsystem
        bsys(sid, usekv, basekv, numarea, areas, numbus, buses, numowner, owners, numzone, zone)

        SID Valid bus system ID, Valid bus subsystem IDS range from 0 to 11

        USEKV
          0 - Do not use BASEKV values
          1 - Use BASEKV values

        BASEKV array of two elements
          BASEKV(1) is the minimum basekV limit
          BASEKV(2) is the maximum basekV limit

        NUM<OBJECT> number of <OBJECT> to set where <OBJECT> in area, bus (can also be bus names),
        owner and zone

        <OBJECT>(NUM<OBJECT>) is an array that contains the <objects> to set.
        """

        ierr = psspy.bsys(
            sid=sid, usekv=usekv, basekv=basekv, numarea=numarea, areas=areas, numbus=numbus,
            buses=buses, numowner=numowner, owners=owners, numzone=numzone, zones=zones, **kwds
        )
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseBsysException(ierr, None)

    @staticmethod
    def load_data(i=None, id=None, intgar=None, realar=None, **kwds):
        """Modify the data of an existing load in the working case
        load_data(i, id, intgar, realar)


        i  - Is the bus number (input; no default allowed).
        id - (char*2) Is the load data identifier (input; '1' by default).

        INTGAR(6):
          INTGAR(1) STATUS, load status (1 by default).
          INTGAR(2) AREA, area number (area of bus I by default).
          INTGAR(3) ZONE, zone number (zone of bus I by default).
          INTGAR(4) OWNER, owner number (owner of bus I by default).
          INTGAR(5) SCALE, load scaling flag (0 = fixed, non-conforming;
                           1 = scalable, conforming) (1 by default).
          INTGAR(6) INTRPT, interruptible load flag (0 = non-interruptible;
                           1 = interruptible) (0 by default).
          INTGAR(7) DgenM, load distributed generation (Dgen) flag
                           (0 = Dgen is OFF; 1 = Dgen is ON) (0 by default).

        REALAR(6):
          REALAR(1) PL, constant power active load (0.0 by default).
          REALAR(2) QL, constant power reactive load (0.0 by default).
          REALAR(3) IP, constant current active load (0.0 by default).
          REALAR(4) IQ, constant current reactive load (0.0 by default).
          REALAR(5) YP, constant admittance active load (0.0 by default).
          REALAR(6) YQ, constant admittance reactive load (0.0 by default).
          REALAR(7) DgenP, Ditributed Generation active power (0.0 by default).
          REALAR(8) DgenQ, Ditributed Generation reactive power (0.0 by default)
        """
        ierr = psspy.load_data_4(i=i, id=id, intgar=intgar, realar=realar, **kwds)
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseLoadDataException(ierr, None, i, id)

    @staticmethod
    def brnmsc(ibus=None, jbus=None, ickt=None, string=None):
        return_value = psspy.brnmsc(ibus=ibus, jbus=jbus, ickt=ickt, string=string)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr and ierr != 6:
            raise monsterexceptions.PsseBrnmscException(ierr, val)
        return val

    @staticmethod
    def brnint(ibus=None, jbus=None, ickt=None, string=None):
        return_value = psspy.brnint(ibus=ibus, jbus=jbus, ickt=ickt, string=string)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseBrnintException(ierr, val)
        return val

    @staticmethod
    def busint(ibus=None, string=None):
        ierr, ival = psspy.busint(ibus=ibus, string=string)
        if string == 'TYPE':
            ival = BusType.get_enum(ival)
        if ierr:
            raise monsterexceptions.PsseBusintException(ierr, ival)
        return ival

    @staticmethod
    def branch_data(i=None, j=None, ckt=None, intgar=None, realar=None, **kwds):
        """
        Modify the data of an existing non-transformer branch in the working case or to add a new
        non-transformer branch to the working case

        branch_data(i, j, ckt, intgar, realer, ratings, namear)

        I     - Bus number of from bus (input; no default allowed).
        J     - Bus number of to bus (input; no default allowed).
        CKT*2 - Circuit identifier (input; '1' by default).

        INTGAR(6) Is an array of six elements (input).
          INTGAR(1) ST, branch status (1 by default).
          INTGAR(2) METBUS, metered end bus number (I or J) (I by default).
          INTGAR(3) O1, first owner number (owner of bus I by default).
          INTGAR(4) O2, second owner number (0 by default).
          INTGAR(5) O3, third owner number (0 by default).
          INTGAR(6) O4, fourth owner number (0 by default).

        REALAR(12) Is an array of twelve elements (input).
          REALAR(1)  R, nominal branch resistance (0.0 by default).
          REALAR(2)  X, nominal branch reactance (THRSHZ by default; 0.0001 if THRSHZ = 0.0).
          REALAR(3)  B, total line charging (0.0 by default).
          REALAR(4)  GI, real line shunt at bus I end. (0.0 by default)
          REALAR(5)  BI, reactive line shunt at bus I end (0.0 by default).
          REALAR(6)  GJ, real line shunt at bus J end (0.0 by default).
          REALAR(7)  BJ, reactive line shunt at bus J end (0.0 by default).
          REALAR(8)  LEN, line length (0.0 by default).
          REALAR(9)  F1, first owner fraction (1.0 by default).
          REALAR(10) F2, second owner fraction (1.0 by default).
          REALAR(11) F3, third owner fraction (1.0 by default).
          REALAR(12) F4, fourth owner fraction (1.0 by default).

        RATINGS(12) Is an array of twelve elements (input).
          RATINGS(1)  RATE1, rating set 1 line rating (0.0 by default).
          RATINGS(2)  RATE2, rating set 2 line rating (0.0 by default).
          RATINGS(3)  RATE3, rating set 3 line rating (0.0 by default).
          RATINGS(4)  RATE4, rating set 4 line rating (0.0 by default).
          RATINGS(5)  RATE5, rating set 5 line rating (0.0 by default).
          RATINGS(6)  RATE6, rating set 6 line rating (0.0 by default).
          RATINGS(7)  RATE7, rating set 7 line rating (0.0 by default).
          RATINGS(8)  RATE8, rating set 8 line rating (0.0 by default).
          RATINGS(9)  RATE9, rating set 9 line rating (0.0 by default).
          RATINGS(10) RATE10, rating set 10 line rating (0.0 by default).
          RATINGS(11) RATE11, rating set 11 line rating (0.0 by default).
          RATINGS(12) RATE12, rating set 12 line rating (0.0 by default).

        NAMEAR*40 - branch name (input, blank by default).
        """
        ierr = psspy.branch_data(i=i, j=j, ckt=ckt, intgar=intgar, realar=realar, **kwds)

        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseBranchDataException(ierr, None)

    @staticmethod
    def two_winding_data(i=None, j=None, ckt=None, intgar=None, realari=None, charar=None, **kwds):
        return psspy.two_winding_data_4(
            i=i, j=j, ckt=ckt, intgar=intgar, realari=realari, charar=charar, **kwds
        )

    @staticmethod
    def tr3int(ibus=None, jbus=None, kbus=None, ickt=None, string=None):
        return_value = psspy.tr3int(ibus=ibus, jbus=jbus, kbus=kbus, ickt=ickt, string=string)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseTr3intException(ierr, val)
        return val

    @staticmethod
    def inilod(ibus=None):
        """Initializes load fetching routine 'NXTLOD' for returning loads attached to IBUS.

        ierr = inilod(ibus)

        where:
        IBUS - Bus number (input).

        """
        ierr = psspy.inilod(ibus=ibus)
        if ierr:
            raise monsterexceptions.PsseIniLodException(ierr)

    @staticmethod
    def nxtlod(ibus=None):
        """Use this API to return the identifier of the next load connected to a bus.
        Each time 'NXTLOD' is called it returns the next load identifier in ascending order.
        'INILOD' must first be called to establish the load bus number.

         id = nxtlod(ibus)

         IBUS - Bus number (input).
         ID   - Load identifier (output).

        """
        return_value = psspy.nxtlod(ibus=ibus)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseNxtLodException(ierr, val)
        return val

    @staticmethod
    def loddt2(ibus=None, id=None, string1=None, string2=None):
        """Complex load quantities.

        rval = loddt1(ibus, id ,string1, string2)

        When STRNG1 is one of the following: 'MVA', 'IL', 'YL', 'TOTAL', the values returned are the
        net load values (i.e., value includes load plus contribution from any in-service distributed
        generation on the load feeder at that bus)

        IBUS - Bus number (input).

        ID - Load identifier (input).

        STRING1 - String indicating the load characteristic desired (input):
          'MVA'   Net in-service constant MVA load.
          'IL'    Net in-service constant current load.
          'YL'    Net in-service constant admittance load.
          'TOTAL' Net in-service total load (total of constant MVA, constant current and constant
                  admittance portions).
          'LDDGN' Total in-service distributed generation on the load feeder.
          'YNEG'  Exceptional nominal negative sequence load.
          'YZERO' Exceptional nominal zero sequence load. Character STRING2 String indicating the
                  units to be used (input):
          'ACT'   Actual load (nominal load for STRING1 = 'YNEG' or 'YZERO'). 'P', 'Q' returned in
                  MW, Mvar.
          'O_ACT' Actual load (nominal load for STRING1 = 'YNEG' or 'YZERO'). 'P', 'Q' in units
                  determined by the power output option setting.
          'NOM'   Nominal load (at 1.0 pu voltage). 'RVAL' returned in MVA.
          'O_NOM' Nominal load (at 1.0 pu voltage). 'RVAL' in units determined by the power output
                  option setting.

        RVAL - Magnitude of the complex value indicated by STRING1 in the units indicated by STRING2
               (output).
        """
        return_value = psspy.loddt2(ibus=ibus, id=id, string1=string1, string2=string2)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseLoddtException(ierr, val)
        return val

    @staticmethod
    def lodint(ibus=None, id=None, string=None):
        return_value = psspy.lodint(ibus=ibus, id=id, string=string)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseLoddtException(ierr, val)
        return val

    @staticmethod
    def macint(ibus=None, id=None, string=None):
        """Return integer machine quantities.

        ival = macint(ibus, id, string)

        where:

        IBUS - Bus number (input).

        ID - Machine identifier (input).

        STRING - String indicating the machine quantity desired (input):
           'STATUS'  Machine status; 1 (one) for in-service, else 0 (zero).
           'IREG'    Bus number of remote regulated bus; zero for none.
           'OWNERS'  Number of owners.
           'WMOD'    Wind machine reactive power limits mode; 0 if this
                     machine is not a wind machine.
           'OWN1'    Owner number of the first owner.
           'OWN2'    Owner number of the second owner.
           'OWN3'    Owner number of the third owner.
           'OWN4'    Owner number of the fourth owner.
           'PERCENT' MVA loading of the machines as a percentage of
                     machine base.
           'CZG'     Grounding impedance data input/output code.

        IVAL - Value indicated by STRING (output).
        """
        return_value = psspy.macint(ibus=ibus, id=id, string=string)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseMacintException(ierr, val)
        return val

    @staticmethod
    def machine_data(i=None, id=None, intgar=None, realar=None, **kwds):
        """Modify (or add) the data of an existing (or new) machine in the working case
        machine_chng(i, id, intgar, realar)

        i  - Is the bus number (input; no default allowed).
        id - (char*2) Is the machine identifier (input; '1' by default).

        INTGAR(6):
          INTGAR(1) STAT, machine status (1 by default).
          INTGAR(2) O1, first owner number (owner of bus I by default).
          INTGAR(3) O2, second owner number (0 by default).
          INTGAR(4) O3, third owner number (0 by default).
          INTGAR(5) O4, fourth owner number (0 by default).
          INTGAR(6) WMOD, machine reactive power limits mode (
                  0 if this machine is a conventional machine,
                  1, 2, or 3 if machine is a renewable machine,
                  4 if it is an infeed machine) (0 by default).

        REALAR(17):
          REALAR(1) PG, machine active power output (0.0 by default).
          REALAR(2) QG, machine reactive power output (0.0 by default).
          REALAR(3) QT, machine reactive power upper limit (9999.0 by default).
          REALAR(4) QB, machine reactive power lower limit (-9999.0 by default).
          REALAR(5) PT, machine active power upper limit (9999.0 by default).
          REALAR(6) PB, machine active power lower limit (-9999.0 by default).
          REALAR(7) MBASE, machine MVA base (SBASE by default).
          REALAR(8) ZR, machine resistance (0.0 by default).
          REALAR(9) ZX, machine reactance (1.0 by default).
          REALAR(10) RT, step-up transformer resistance (0.0 by default).
          REALAR(11) XT, step-up transformer reactance (0.0 by default).
          REALAR(12) GTAP, step-up transformer tap ratio (1.0 by default).
          REALAR(13) F1, first owner fraction (1.0 by default).
          REALAR(14) F2, second owner fraction (1.0 by default).
          REALAR(15) F3, third owner fraction (1.0 by default).
          REALAR(16) F4, fourth owner fraction (1.0 by default).
          REALAR(17) WPF, renewable machine power factor (1.0 by default).
        """
        ierr = psspy.machine_data_2(i=i, id=id, intgar=intgar, realar=realar, **kwds)
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseMachineDataException(ierr, None)

    @staticmethod
    def macdt2(ibus=None, id=None, string=None):
        """Complex machine quantities.

        cmpval = macdt2(ibus, id, string)

        where:

        IBUS   - Bus number (input).
        ID     - Machine identifier (input).
        STRING - The machine quantity desired (input):
          'PQ'      Actual generator power output, in MW/Mvar.
          'O_PQ'    Same as 'PQ', in units determined by the power output option setting.
          'ZSORCE'  Machine impedance.
          'XTRAN'   Step-up transformer impedance.
          'ZPOS'    Positive sequence fault analysis machine impedance (Rpos + j X").
          'ZNEG'    Negative sequence machine impedance.
          'ZZERO'   Zero sequence machine impedance.
          'ZGRND'   Zero sequence grounding impedance, in per unit or ohms, according to the
                    machine's grounding impedance data input/output code.
          'ZGRNDPU' Zero sequence grounding impedance in per unit.
        """
        return_value = psspy.macdt2(ibus=ibus, id=id, string=string)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr == 4:
            return 0
        if ierr:
            raise monsterexceptions.PsseMacdtException(ierr, val)
        return val

    @staticmethod
    def macdat(ibus=None, id=None, string=None):
        """Real machine quantities

        rval = macdat(ibus, id, string)

        IBUS   - Bus number (input).
        ID     - Machine identifier (input).
        STRING - String indicating the machine quantity desired (input):
          'QMAX'    - Maximum generator reactive output, in Mvar.
          'O_QMAX'  - Same as 'QMAX', in units determined by the power output option setting.
          'QMIN'    - Minimum generator reactive output, in Mvar.
          'O_QMIN'  - Same as 'QMIN', in units determined by the power output option setting.
          'PMAX'    - Maximum generator active output, in MW.
          'O_PMAX'  - Same as 'PMAX', in units determined by the power output option setting.
          'PMIN'    - Minimum generator real active, in MW.
          'O_PMIN'  - Same as 'PMIN', in units determined by the power output option setting.
          'MBASE'   - Total MVA base.
          'MVA'     - Machine loading, in MVA.
          'O_MVA'   - Same as 'MVA', in units determined by the power output option setting.
          'P'       - Machine loading, in MW.
          'O_P'     - Same as 'P', in units determined by the power output option setting.
          'Q'       - Machine loading, in Mvar.
          'O_Q'     - Same as 'Q', in units determined by the power output option setting.
          'PERCENT' - MVA loading of the machines as a percentage of machine base.
          'GENTAP'  - Step-up transformer off-nominal turns ratio.
          'VSCHED'  - Regulated voltage setpoint.
          'WPF'     - Power factor used in setting reactive power limits for this wind machine when
                      WMOD is 2 or 3.
          'FRACT1'  - Fraction of total ownership assigned to the first owner.
          'FRACT2'  - Fraction of total ownership assigned to the second owner.
          'FRACT3'  - Fraction of total ownership assigned to the third owner.
          'FRACT4'  - Fraction of total ownership assigned to the fourth owner.
          'RMPCT'   - Percentage of total MVAR required to regulate remote bus voltage.
          'RPOS'    - Positive sequence fault analysis machine resistance.
          'XSUBTR'  - Positive sequence fault analysis machine subtransient reactance.
          'XTRANS'  - Positive sequence fault analysis machine transient reactance.
          'XSYNCH'  - Positive sequence fault analysis machine synchronous reactance.
        """
        return_value = psspy.macdat(ibus=ibus, id=id, string=string)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseMacdatdException(ierr, val)
        return val

    @staticmethod
    def machine_chng(i=None, id=None, intgar=None, realar=None, **kwds):
        """Modify the data of an existing machine in the working case

        machine_chng(i, id, intgar, realar)

        i  - Is the bus number (input; no default allowed).
        id - (char*2) Is the machine identifier (input; '1' by default).

        INTGAR(6):
          INTGAR(1) STAT, machine status (1 by default).
          INTGAR(2) O1, first owner number (owner of bus I by default).
          INTGAR(3) O2, second owner number (0 by default).
          INTGAR(4) O3, third owner number (0 by default).
          INTGAR(5) O4, fourth owner number (0 by default).
          INTGAR(6) WMOD, machine reactive power limits mode (0 if this
                          machine is a conventional machine, 1, 2, or 3 if
                          machine is a renewable machine, 4 if it is an
                          infeed machine) (0 by default).

        REALAR(17)
          REALAR(1) PG, machine active power output (0.0 by default).
          REALAR(2) QG, machine reactive power output (0.0 by default).
          REALAR(3) QT, machine reactive power upper limit (9999.0 by default).
          REALAR(4) QB, machine reactive power lower limit (-9999.0 by default).
          REALAR(5) PT, machine active power upper limit (9999.0 by default).
          REALAR(6) PB, machine active power lower limit (-9999.0 by default).
          REALAR(7) MBASE, machine MVA base (SBASE by default).
          REALAR(8) ZR, machine resistance (0.0 by default).
          REALAR(9) ZX, machine reactance (1.0 by default).
          REALAR(10) RT, step-up transformer resistance (0.0 by default).
          REALAR(11) XT, step-up transformer reactance (0.0 by default).
          REALAR(12) GTAP, step-up transformer tap ratio (1.0 by default).
          REALAR(13) F1, first owner fraction (1.0 by default).
          REALAR(14) F2, second owner fraction (1.0 by default).
          REALAR(15) F3, third owner fraction (1.0 by default).
          REALAR(16) F4, fourth owner fraction (1.0 by default).
          REALAR(17) WPF, renewable machine power factor (1.0 by default).

        """
        ierr = psspy.machine_chng_2(i=i, id=id, intgar=intgar, realar=realar, **kwds)

        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PsseMachineDataException(ierr, None)

    @staticmethod
    def abusreal(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.abusreal(sid=sid, flag=flag, string=string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAbusException(ierr, array)
        return array

    @staticmethod
    def abusint(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.abusint(sid=sid, flag=flag, string=string, **kwds)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAbusException(ierr, array)
        return array

    @staticmethod
    def bus_chng(i=None, intgar=None, realar=None, name=None, **kwds):
        return psspy.bus_chng_3(i=i, intgar=intgar, realar=realar, name=name, **kwds)

    @staticmethod
    def bus_number(ibus=None, newbus=None, **kwds):

        return psspy.bus_number(ibus=ibus, newbus=newbus, **kwds)

    @staticmethod
    def aswshcount(sid=None, flag=None):
        return_value = psspy.aswshcount(sid=sid, flag=flag)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAswshException(ierr, array)
        return array

    @staticmethod
    def aswshint(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.aswshint(sid=sid, flag=flag, string=string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAswshException(ierr, array)
        return array

    @staticmethod
    def aswshreal(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.aswshreal(sid=sid, flag=flag, string=string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAswshException(ierr, array)
        return array

    @staticmethod
    def switched_shunt_chng(i=None, intgar=None, realar=None, rmidnt=None, **kwds):

        return psspy.switched_shunt_chng_3(i=i, intgar=intgar, realar=realar, rmidnt=rmidnt, **kwds)

    @staticmethod
    def atrncount(sid=None, owner=None, ties=None, flag=None, entry=None):
        return_value = psspy.atrncount(sid=sid, owner=owner, ties=ties, flag=flag, entry=entry)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAtrnException(ierr, array)
        return array

    @staticmethod
    def atrnint(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        return_value = psspy.atrnint(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAtrnException(ierr, array)
        return array

    @staticmethod
    def atrnreal(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        return_value = psspy.atrnreal(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAtrnException(ierr, array)
        return array

    @staticmethod
    def atrnchar(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        return_value = psspy.atrnchar(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAtrnException(ierr, array)
        return array

    @staticmethod
    def two_winding_chng(i=None, j=None, ckt=None, intgar=None, realari=None, charar=None, **kwds):

        return psspy.two_winding_chng_4(
            i=i, j=j, ckt=ckt, intgar=intgar, realari=realari, charar=charar, **kwds
        )

    @staticmethod
    def atr3count(sid=None, owner=None, ties=None, flag=None, entry=None):
        return_value = psspy.atr3count(sid=sid, owner=owner, ties=ties, flag=flag, entry=entry)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAtr3Exception(ierr, array)
        return array

    @staticmethod
    def atr3int(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        return_value = psspy.atr3int(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAtr3Exception(ierr, array)
        return array

    @staticmethod
    def atr3char(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        return_value = psspy.atr3char(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAtr3Exception(ierr, array)
        return array

    @staticmethod
    def atr3real(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        return_value = psspy.atr3real(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAtr3Exception(ierr, array)
        return array

    @staticmethod
    def three_wnd_imped_chng(
            i=None, j=None, k=None, ckt=None, intgar=None, realari=None, charar=None, **kwds
    ):

        return psspy.three_wnd_imped_chng_3(
            i=i, j=j, k=k, ckt=ckt, intgar=intgar, realari=realari, charar=charar, **kwds
        )

    @staticmethod
    def three_wnd_imped_data(
            i=None, j=None, k=None, ckt=None, intgar=None, realari=None, charar=None, **kwds
    ):

        return psspy.three_wnd_imped_data_3(
            i=i, j=j, k=k, ckt=ckt, intgar=intgar, realari=realari, charar=charar, **kwds
        )

    @staticmethod
    def amachchar(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.amachchar(sid=sid, flag=flag, string=string, **kwds)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAmachException(ierr, array)
        return array

    @staticmethod
    def amachcplx(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.amachcplx(sid=sid, flag=flag, string=string, **kwds)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAmachException(ierr, array)
        return array

    @staticmethod
    def fdns(options=None, **kwds):
        """Apply the fixed slope decoupled Newton-Raphson power flow calculation

        fnsl(options)

        OPTIONS - Array of eight elements specifying solution options (input). The values are as
                  follows

        OPTIONS(1) tap adjustment flag (use tap adjustment option setting by default).
           = 0 disable.
           = 1 enable stepping adjustment.
           = 2 enable direct adjustment.

        OPTIONS(2) area interchange adjustment flag (use area interchange adjustment option setting
                   by default).
           = 0 disable.
           = 1 enable using tie line flows only in calculating area interchange.
           = 2 enable using tie line flows and loads in calculating area interchange.

        OPTIONS(3) phase shift adjustment flag (use phase shift adjustment option setting by
                   default).
           = 0 disable.
           = 1 enable.

        OPTIONS(4) dc tap adjustment flag (use dc tap adjustment option setting by default).
           = 0 disable.
           = 1 enable.

        OPTIONS(5) switched shunt adjustment flag (use switched shunt adjustment option setting by
                   default).
           = 0 disable.
           = 1 enable.
           = 2 enable continuous mode, disable discrete mode.

        OPTIONS(6) flat start flag (0 by default).
           = 0 do not flat start.
           = 1 flat start.

        OPTIONS(7) var limit flag (99 by default).
           = 0 apply var limits immediately.
           = >0 apply var limits on iteration n (or sooner if mismatch gets small).
           = -1 ignore var limits.

        OPTIONS(8) non-divergent solution flag (use non-divergent solution option setting by
                   default).
           = 0 disable.
           = 1 enable.

        """
        ierr = psspy.fdns(options=options, **kwds)

        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PssePowerFlowException(ierr, None)
        return ierr

    @staticmethod
    def fnsl(options=None, **kwds):
        """Apply the Newton-Raphson power flow calculation

        fnsl(options)

        OPTIONS - Array of eight elements specifying solution options (input). The values are as
                  follows

        OPTIONS(1) tap adjustment flag (use tap adjustment option setting by default).
           = 0 disable.
           = 1 enable stepping adjustment.
           = 2 enable direct adjustment.

        OPTIONS(2) area interchange adjustment flag (use area interchange adjustment option setting
                   by default).
           = 0 disable.
           = 1 enable using tie line flows only in calculating area interchange.
           = 2 enable using tie line flows and loads in calculating area interchange.

        OPTIONS(3) phase shift adjustment flag (use phase shift adjustment option setting by
                   default).
           = 0 disable.
           = 1 enable.

        OPTIONS(4) dc tap adjustment flag (use dc tap adjustment option setting by default).
           = 0 disable.
           = 1 enable.

        OPTIONS(5) switched shunt adjustment flag (use switched shunt adjustment option setting by
                   default).
           = 0 disable.
           = 1 enable.
           = 2 enable continuous mode, disable discrete mode.

        OPTIONS(6) flat start flag (0 by default).
           = 0 do not flat start.
           = 1 flat start.

        OPTIONS(7) var limit flag (99 by default).
           = 0 apply var limits immediately.
           = >0 apply var limits on iteration n (or sooner if mismatch gets small).
           = -1 ignore var limits.

        OPTIONS(8) non-divergent solution flag (use non-divergent solution option setting by
                   default).
           = 0 disable.
           = 1 enable.

        """
        ierr = psspy.fnsl(options=options, **kwds)
        if isinstance(ierr, str):
            raise monsterexceptions.PsseBaseException(ierr, None)
        if ierr:
            raise monsterexceptions.PssePowerFlowException(ierr, None)
        return ierr

    @staticmethod
    def nsol(options=None, **kwds):

        return psspy.nsol(options=options, **kwds)

    @staticmethod
    def solved():
        enum = psspy.solved()

        if isinstance(enum, str):
            raise Exception(enum)
        return SolvedStatusEnum.get_enum(enum)

    @staticmethod
    def tree(apiopt=None, option=None):
        """Check for the existence of in-service ac islands that do not contain a swing bus.

        Following each successful call, it returns BUSES as the number of buses in a swingless
        island (0 for no more swingless islands). When a BUSES value of 0 is returned, no further
        calls are needed.  The API must be called once with APIOPT set to 1. If BUSES is returned as
        0 (i.e., there are no swingless islands), no further calls are needed. Otherwise, if BUSES
        is greater than zero, it must be called one or more times with APIOPT set to 2 and OPTION
        set to indicate the disposition of the current swingless island.  APIOPT 2 calls are
        required until either BUSES is returned as zero or an APIOPT 2 call is made with OPTION set
        to a negative value.

        ierr, buses = tree(apiopt, option)

        Where:

        APIOPT mode of operation (input; no default allowed).

         - 1 initialize and check for the presence of a swingless island

         - 2 process previously detected island as dictated by OPTION; then check for the presence
             of another swingless island

        OPTION option for the handling of previously detected swingless island (input; used only
        when APIOPT is 2; -1).

           < 0 leave this island alone and terminate activity TREE
           = 0 leave this island alone and check for another swingless island
           > 0 disconnect this island, then check for another swingless island

        BUSES returned as the number of buses in this swingless island; 0 if no more swingless
           islands (output).

        """

        return_value = psspy.tree(apiopt=apiopt, option=option)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseTreeException(ierr, val)
        return val

    @staticmethod
    def sysmsm():

        return psspy.sysmsm()

    @staticmethod
    def newton_tolerance(rval=None):
        return_value = psspy.newton_tolerance(rval=rval)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseNewtonToleranceException(ierr, val)
        return val

    @staticmethod
    def abrnint(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):

        """Return an array of integer values for subsystem branches

        iarray = abrnint(sid, owner, ties, flag, entry, string)

        where:

        Integer SID Defines the bus subsystem to be used (input; -1 by default).

           SID = a negative value, to instruct the API to assume a subsystem containing
                 all buses in the working case.
           SID = a valid bus subsystem identifier. Valid subsystem identifiers range
                 from 0 to 11. Subsystem SID must have been previously defined.

        Integer OWNER Is a flag indicating owner usage if ownership is a subsystem selection
        criterion (ignored if SID is negative) (input; 1 by default).

           OWNER = 1 to use bus ownership.
           OWNER = 2 to use branch ownership.

        Integer TIES Is a flag indicating which subsystem branches to include (ignored if SID
        is negative) (input; 1 by default).

           TIES = 1 for interior subsystem branches only.
           TIES = 2 for subsystem tie branches only.
           TIES = 3 for both interior subsystem branches and tie branches.

        Integer FLAG Is a flag indicating which subsystem branches to include (input; 1 by
        default).

           FLAG = 1 for only in-service non-transformer branches.
           FLAG = 2 for all non-transformer branches.
           FLAG = 3 for only in-service non-transformer branches and two-winding transformers.
           FLAG = 4 for all non-transformer branches and two-winding transformers.
           FLAG = 5 for only in-service two-winding transformers.
           FLAG = 6 for all two-winding transformers.

        Integer ENTRY Is a flag indicating output organization (input; 1 by default).

           ENTRY = 1 for single entry (each branch once).
           ENTRY = 2 for double entry (each branch in both directions).

        Integer NSTR Is the number of elements in STRING (1 < NSTR < 50 ) (input; no
        default allowed). STRING(NSTR)

        Is an array of NSTR elements specifying NSTR of the following strings
        indicating the branch quantities desired (input; no default allowed):

           'FROMNUMBER'   - From bus number.
           'TONUMBER'     - To bus number.
           'STATUS'       - Branch status.
           'METERNUMBER'  - Metered end bus number.
           'NMETERNUMBER' - Non-metered end bus number.
           'OWNERS'       - Number of owners.
           'OWN1'         - First owner.
           'OWN2'         - Second owner.
           'OWN3'         - Third owner.
           'OWN4'         - Fourth owner.
           'MOVTYPE'      - MOV protection mode.

        """
        return_value = psspy.abrnint(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAbrnException(ierr, array)
        return array

    @staticmethod
    def abrnchar(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        """Return an array of character values for subsystem branches

        carray = abrnchar(sid, owner, ties, flag, entry, string)

        where:

        Integer SID Defines the bus subsystem to be used (input; -1 by default).

           SID = a negative value, to instruct the API to assume a subsystem containing
                 all buses in the working case.
           SID = a valid bus subsystem identifier. Valid subsystem identifiers range
                 from 0 to 11. Subsystem SID must have been previously defined.

        Integer OWNER Is a flag indicating owner usage if ownership is a subsystem selection
        criterion (ignored if SID is negative) (input; 1 by default).

           OWNER = 1 to use bus ownership.
           OWNER = 2 to use branch ownership.

        Integer TIES Is a flag indicating which subsystem branches to include (ignored if SID
        is negative) (input; 1 by default).

           TIES = 1 for interior subsystem branches only.
           TIES = 2 for subsystem tie branches only.
           TIES = 3 for both interior subsystem branches and tie branches.

        Integer FLAG Is a flag indicating which subsystem branches to include (input; 1 by
        default).

           FLAG = 1 for only in-service non-transformer branches.
           FLAG = 2 for all non-transformer branches.
           FLAG = 3 for only in-service non-transformer branches and two-winding transformers.
           FLAG = 4 for all non-transformer branches and two-winding transformers.
           FLAG = 5 for only in-service two-winding transformers.
           FLAG = 6 for all two-winding transformers.

        Integer ENTRY Is a flag indicating output organization (input; 1 by default).

           ENTRY = 1 for single entry (each branch once).
           ENTRY = 2 for double entry (each branch in both directions).

        Integer NSTR Is the number of elements in STRING (1 < NSTR < 50 ) (input; no
        default allowed). STRING(NSTR)

        Is an array of NSTR elements specifying NSTR of the following strings
        indicating the branch quantities desired (input; no default allowed):

           'ID'           - Circuit identifier (2 characters).
           'FROMNAME'     - From bus name (12 characters).
           'FROMEXNAME'   - From bus extended bus name (18 characters).
           'TONAME'       - To bus name (three-winding transformer name for a three-winding
                            transformer winding) (12 characters).
           'TOEXNAME'     - To bus extended bus name (three-winding transformer name and winding
                            number for a threewinding transformer winding) (18 characters).
           'METERNAME'    - Metered bus name (12 characters).
           'METEREXNAME'  - Metered bus extended bus name (18 characters).
           'NMETERNAME'   - Non-metered bus name (12 characters).
           'NMETEREXNAME' - Non-metered bus extended bus name (18 characters).

        """
        return_value = psspy.abrnchar(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAbrnException(ierr, array)
        return array

    @staticmethod
    def abrncount(sid=None, owner=None, ties=None, flag=None, entry=None, **kwds):
        """Return the number of array entries required to accommodate the data to be returned by the
        remaining members of the branch data family.

        brnchs = abrncount(sid, owner, ties, flag, entry)

        where:

        Integer SID Defines the bus subsystem to be used (input; -1 by default).

           SID = a negative value, to instruct the API to assume a subsystem containing
                 all buses in the working case.
           SID = a valid bus subsystem identifier. Valid subsystem identifiers range
                 from 0 to 11. Subsystem SID must have been previously defined.

        Integer OWNER Is a flag indicating owner usage if ownership is a subsystem selection
        criterion (ignored if SID is negative) (input; 1 by default).

           OWNER = 1 to use bus ownership.
           OWNER = 2 to use branch ownership.

        Integer TIES Is a flag indicating which subsystem branches to include (ignored if SID
        is negative) (input; 1 by default).

           TIES = 1 for interior subsystem branches only.
           TIES = 2 for subsystem tie branches only.
           TIES = 3 for both interior subsystem branches and tie branches.

        Integer FLAG Is a flag indicating which subsystem branches to include (input; 1 by
        default).

           FLAG = 1 for only in-service non-transformer branches.
           FLAG = 2 for all non-transformer branches.
           FLAG = 3 for only in-service non-transformer branches and two-winding transformers.
           FLAG = 4 for all non-transformer branches and two-winding transformers.
           FLAG = 5 for only in-service two-winding transformers.
           FLAG = 6 for all two-winding transformers.

        Integer ENTRY Is a flag indicating output organization (input; 1 by default).

           ENTRY = 1 for single entry (each branch once).
           ENTRY = 2 for double entry (each branch in both directions).

        BRNCHS Is the number of array entries required for the subsystem indicated by SID and OWNER
               that meet the editing criteria indicated by TIES, FLAG and ENTRY (output).
        """
        return_value = psspy.abrncount(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, **kwds
        )

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAbrnException(ierr, array)
        return array

    @staticmethod
    def awndint(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        return_value = psspy.awndint(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAwndException(ierr, array)
        return array

    @staticmethod
    def awndreal(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        return_value = psspy.awndreal(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAwndException(ierr, array)
        return array

    @staticmethod
    def awndcplx(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        return_value = psspy.awndcplx(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAwndException(ierr, array)
        return array

    @staticmethod
    def awndcount(sid=None, owner=None, ties=None, flag=None, entry=None, **kwds):
        return_value = psspy.awndcount(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, **kwds
        )

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAwndException(ierr, array)
        return array

    @staticmethod
    def awndchar(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        return_value = psspy.awndchar(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAwndException(ierr, array)
        return array

    @staticmethod
    def busdt1(ibus=None, string1=None, string2=None):
        return_value = psspy.busdt1(ibus=ibus, string1=string1, string2=string2)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseBusdtException(ierr, val)
        return val

    @staticmethod
    def busdt2(ibus=None, string1=None, string2=None):
        return_value = psspy.busdt2(ibus=ibus, string1=string1, string2=string2)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseBusdtException(ierr, val)
        return val

    @staticmethod
    def inimac(ibus=None):

        return psspy.inimac(ibus=ibus)

    @staticmethod
    def nxtmac(ibus=None):
        return_value = psspy.nxtmac(ibus=ibus)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseNxtMacException(ierr, val)
        return val

    @staticmethod
    def nxtbus():
        return psspy.nxtbus()

    @staticmethod
    def inibrx(ibus, single):
        ierr = psspy.inibrx(ibus, single)
        if ierr:
            raise monsterexceptions.PsseIniBrxException(ierr, None)
        return None

    @staticmethod
    def notona(ibus):
        return_value = psspy.notona(ibus)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseBusdtException(ierr, val)

        return val

    @staticmethod
    def nxtbrn(ibus):
        return_value = psspy.nxtbrn(ibus)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, jbus, ickt) = return_value
        if ierr:
            raise monsterexceptions.PsseNxtBrnException(ierr, (jbus, ickt))
        return jbus, ickt

    @staticmethod
    def nxtmsl():
        return_value = psspy.nxtmsl()
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, ibus, jbus, ickt) = return_value
        if ierr:
            raise monsterexceptions.PsseNxtMslException(ierr, (ibus, jbus, ickt))
        return ibus, jbus, ickt

    @staticmethod
    def branch_chng(i=None, j=None, ckt=None, intgar=None, realar=None, **kwds):

        return psspy.branch_chng(i=i, j=j, ckt=ckt, intgar=intgar, realar=realar, **kwds)

    @staticmethod
    def abrnreal(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        """Return an array of integer values for subsystem branches

        rarray = abrnreal(sid, owner, ties, flag, entry, string)

        where:

        Integer SID Defines the bus subsystem to be used (input; -1 by default).

           SID = a negative value, to instruct the API to assume a subsystem containing
                 all buses in the working case.
           SID = a valid bus subsystem identifier. Valid subsystem identifiers range
                 from 0 to 11. Subsystem SID must have been previously defined.

        Integer OWNER Is a flag indicating owner usage if ownership is a subsystem selection
        criterion (ignored if SID is negative) (input; 1 by default).

           OWNER = 1 to use bus ownership.
           OWNER = 2 to use branch ownership.

        Integer TIES Is a flag indicating which subsystem branches to include (ignored if SID
        is negative) (input; 1 by default).

           TIES = 1 for interior subsystem branches only.
           TIES = 2 for subsystem tie branches only.
           TIES = 3 for both interior subsystem branches and tie branches.

        Integer FLAG Is a flag indicating which subsystem branches to include (input; 1 by
        default).

           FLAG = 1 for only in-service non-transformer branches.
           FLAG = 2 for all non-transformer branches.
           FLAG = 3 for only in-service non-transformer branches and two-winding transformers.
           FLAG = 4 for all non-transformer branches and two-winding transformers.
           FLAG = 5 for only in-service two-winding transformers.
           FLAG = 6 for all two-winding transformers.

        Integer ENTRY Is a flag indicating output organization (input; 1 by default).

           ENTRY = 1 for single entry (each branch once).
           ENTRY = 2 for double entry (each branch in both directions).

        Integer NSTR Is the number of elements in STRING (1 < NSTR < 50 ) (input; no
        default allowed). STRING(NSTR)

        Is an array of NSTR elements specifying NSTR of the following strings
        indicating the branch quantities desired (input; no default allowed):

        'AMPS'  - Branch current in amps (0.0 if bus base voltage is 0.0).
        'PUCUR' - Branch current in pu.

        'PCTRATE'        - Percent from bus current of default rating set.
        'PCTRATE{A|B|C}' - Percent from bus current of rating set {A|B|C}.
        'PCTMVARATE'     - Percent from bus MVA of default rating set.
        'PCTMVARATE{A|B|C}'  - Percent from bus MVA of rating set {A|B|C}.
        'PCTCORPRATE'        - Percent from bus current or MVA loading
            (according to the appropriate percent loading units program
            option setting) of default rating set.
        'PCTCORPRATE{A|B|C}' - Percent from bus current or MVA loading
            (according to the appropriate percent loading units program option
            setting) of rating set {A|B|C}.
        'MAXPCTRATE' - Larger of percent from/to bus current of default rating set.
        'MAXPCTRATE{A|B|C}' - Larger of percent from/to bus current of rating set {A|B|C}.
        'MXPCTMVARAT' - Larger of percent from/to bus MVA of default rating set.
        'MXPCTMVARAT{A|B|C}' - Larger of percent from/to bus MVA of rating set {A|B|C}.
        'MXPCTCRPRAT' - Larger of percent from/to bus current or MVA loading
            (according to the appropriate percent loading units program option setting)
            of default rating set.
        'MXPCTCRPRAT{A|B|C}' - Larger of percent from/to bus current or MVA loading
            (according to the appropriate percent loading units program option setting)
            of rating set {A|B|C}.

        'FRACT{1|2|3|4}' - {First|second|third|fourth} owner fraction.
        'RATE'           - Rating from default rating set.
        'RATE{A|B|C}'    - Rating from rating set {A|B|C}.
        'LENGTH'         - Line length.
        'CHARGING'       - Total charging capacitance in pu.
        'CHARGINGZER0'   - Zero sequence total charging capacitance in pu.
        'MOVIRATED'      - MOV rated current in kA. For the following, values are
                           returned  in MW, Mvar, or MVA
        'P'              - Active power flow at from bus end.
        'Q'              - Reactive power flow at from bus end.
        'MVA'            - |P + j Q| at from bus end.
        'MAXMVA'         - |P + j Q| at from bus or to bus end, whichever is larger.
        'PLOSS'          - Active power losses.
        'QLOSS'          - Reactive power losses.

        For the following, values are returned in units determined by the power
        output option setting:

        'O_P'      - Active power flow at from bus end.
        'O_Q'      - Reactive power flow at from bus end.
        'O_MVA'    - |P + j Q| at from bus end.
        'O_MAXMVA' - ||P + j Q| at from bus or to bus end, whichever is larger.
        'O_PLOSS'  - Active power losses.
        'O_QLOSS'  - Reactive power losses
        """
        return_value = psspy.abrnreal(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAbrnException(ierr, array)
        return array

    @staticmethod
    def psseinit(buses=None):
        ierr = psspy.psseinit(buses=buses)
        return ierr

    @staticmethod
    def progress_output(islct=None, filarg=None, options=None, **kwds):

        return psspy.progress_output(islct=islct, filarg=filarg, options=options, **kwds)

    @staticmethod
    def report_output(islct=None, filarg=None, options=None, **kwds):

        return psspy.report_output(islct=islct, filarg=filarg, options=options, **kwds)

    @staticmethod
    def alert_output(islct=None, filarg=None, options=None, **kwds):

        return psspy.alert_output(islct=islct, filarg=filarg, options=options, **kwds)

    @staticmethod
    def solution_parameters(intgar=None, realar=None, **kwds):

        return psspy.solution_parameters_3(intgar=intgar, realar=realar, **kwds)

    @staticmethod
    def close_powerflow():

        return psspy.close_powerflow()

    @staticmethod
    def sfiles():
        return psspy.sfiles()

    @staticmethod
    def wnddt2(ibus=None, jbus=None, kbus=None, ickt=None, string=None):
        return_value = psspy.wnddt2(ibus=ibus, jbus=jbus, kbus=kbus, ickt=ickt, string=string)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseWnddtException(ierr, val)
        return val

    @staticmethod
    def wnddat(ibus=None, jbus=None, kbus=None, ickt=None, string=None):
        return_value = psspy.wnddat(ibus=ibus, jbus=jbus, kbus=kbus, ickt=ickt, string=string)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseWnddtException(ierr, val)
        return val

    @staticmethod
    def wndint(ibus=None, jbus=None, kbus=None, ickt=None, string=None):
        return_value = psspy.wndint(ibus=ibus, jbus=jbus, kbus=kbus, ickt=ickt, string=string)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseWnddtException(ierr, val)
        return val

    @staticmethod
    def tr3dat(ibus=None, jbus=None, kbus=None, ickt=None, string=None):
        return_value = psspy.tr3dat(ibus=ibus, jbus=jbus, kbus=kbus, ickt=ickt, string=string)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseTr3datException(ierr, val)
        return val

    @staticmethod
    def bus_data(i=None, intgar=None, realar=None, name=None, **kwds):

        return psspy.bus_data_3(i=i, intgar=intgar, realar=realar, name=name, **kwds)

    @staticmethod
    def purg3wnd(frmbus=None, tobus1=None, tobus2=None, ckt=None):

        return psspy.purg3wnd(frmbus=frmbus, tobus1=tobus1, tobus2=tobus2, ckt=ckt)

    @staticmethod
    def busexs(ibus=None):

        return psspy.busexs(ibus=ibus)

    @staticmethod
    def abuschar(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.abuschar(sid=sid, flag=flag, string=string, **kwds)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAbusException(ierr, array)
        return array

    @staticmethod
    def amachint(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.amachint(sid=sid, flag=flag, string=string, **kwds)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAmachException(ierr, array)
        return array

    @staticmethod
    def abrncplx(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        """Return an array of complex values for subsystem branches

        carray = abrncplx(sid, owner, ties, flag, entry, string)

        where:

        Integer SID Defines the bus subsystem to be used (input; -1 by default).

           SID = a negative value, to instruct the API to assume a subsystem containing
                 all buses in the working case.
           SID = a valid bus subsystem identifier. Valid subsystem identifiers range
                 from 0 to 11. Subsystem SID must have been previously defined.

        Integer OWNER Is a flag indicating owner usage if ownership is a subsystem selection
        criterion (ignored if SID is negative) (input; 1 by default).

           OWNER = 1 to use bus ownership.
           OWNER = 2 to use branch ownership.

        Integer TIES Is a flag indicating which subsystem branches to include (ignored if SID
        is negative) (input; 1 by default).

           TIES = 1 for interior subsystem branches only.
           TIES = 2 for subsystem tie branches only.
           TIES = 3 for both interior subsystem branches and tie branches.

        Integer FLAG Is a flag indicating which subsystem branches to include (input; 1 by
        default).

           FLAG = 1 for only in-service non-transformer branches.
           FLAG = 2 for all non-transformer branches.
           FLAG = 3 for only in-service non-transformer branches and two-winding transformers.
           FLAG = 4 for all non-transformer branches and two-winding transformers.
           FLAG = 5 for only in-service two-winding transformers.
           FLAG = 6 for all two-winding transformers.

        Integer ENTRY Is a flag indicating output organization (input; 1 by default).

           ENTRY = 1 for single entry (each branch once).
           ENTRY = 2 for double entry (each branch in both directions).

        Integer NSTR Is the number of elements in STRING (1 < NSTR < 50 ) (input; no
        default allowed). STRING(NSTR)

        Is an array of NSTR elements specifying NSTR of the following strings
        indicating the branch quantities desired (input; no default allowed):

           'RX'           - Branch impedance in pu.
           'FROMSHNT'     - Line shunt at from bus end in pu.
           'TOSHNT'       - Line shunt at to bus end in pu.
           'RXZERO'       - Zero sequence branch impedance in pu.
           'FROMSHNTZERO' - Zero sequence line shunt at from bus end in pu.
           'TOSHNTZERO'   - Zero sequence line shunt at to bus end in pu. For the following values
                            are returned in MW and Mvar:
           'PQ'           - P + j Q flow at from bus end.
           'PQLOSS'       - Losses. For the following, values are returned in units determined by
                            the power output option setting:
           'O_PQ'         - P + j Q flow at from bus end.
           'O_PQLOSS'     - Losses.
        """
        return_value = psspy.abrncplx(
            sid=sid, owner=owner, ties=ties, flag=flag, entry=entry, string=string, **kwds
        )

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAbrnException(ierr, array)
        return array

    @staticmethod
    def atrncplx(sid=None, owner=None, ties=None, flag=None, entry=None, string=None, **kwds):
        return_value = psspy.atrncplx(sid, owner, ties, flag, entry, string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAtrnException(ierr, array)
        return array

    @staticmethod
    def alodbuschar(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.alodbuschar(sid=sid, flag=flag, string=string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAlodBusException(ierr, array)
        return array

    @staticmethod
    def alodbusreal(sid=None, flag=None, string=None, **kwds):
        return_value = psspy.alodbusreal(sid=sid, flag=flag, string=string, **kwds)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, array) = return_value
        if ierr:
            raise monsterexceptions.PsseAlodBusException(ierr, array)
        return array

    @staticmethod
    def getdefaultint():

        return psspy.getdefaultint()

    @staticmethod
    def getdefaultreal():

        return psspy.getdefaultreal()

    @staticmethod
    def getdefaultchar():

        return psspy.getdefaultchar()

    @staticmethod
    def busdat(ibus=None, string=None):

        return psspy.busdat(ibus=ibus, string=string)

    @staticmethod
    def extr(sid=None, all=None, status=None, **kwds):

        return psspy.extr(sid=sid, all=all, status=status, **kwds)

    @staticmethod
    def purgload(frmbus=None, id=None):

        return psspy.purgload(frmbus=frmbus, id=id)

    @staticmethod
    def fxsint(ibus=None, id=None, string=None):

        return psspy.fxsint(ibus=ibus, id=id, string=string)

    @staticmethod
    def shunt_data(i=None, id=None, intgar=None, realar=None, **kwds):

        return psspy.shunt_data(i=i, id=id, intgar=intgar, realar=realar, **kwds)

    @staticmethod
    def purgshunt(frmbus=None, id=None):

        return psspy.purgshunt(frmbus=frmbus, id=id)

    @staticmethod
    def swsint(ibus=None, string=None):

        return psspy.swsint(ibus=ibus, string=string)

    @staticmethod
    def switched_shunt_data(i=None, intgar=None, realar=None, rmidnt=None, **kwds):

        return psspy.switched_shunt_data_3(i=i, intgar=intgar, realar=realar, rmidnt=rmidnt, **kwds)

    @staticmethod
    def swsblk(ibus=None, iblk=None):

        return psspy.swsblk(ibus=ibus, iblk=iblk)

    @staticmethod
    def swsdt1(ibus=None, string=None):

        return psspy.swsdt1(ibus=ibus, string=string)

    @staticmethod
    def purgsws(frmbus=None):

        return psspy.purgsws(frmbus=frmbus)

    @staticmethod
    def gendat(ibus=None):

        return psspy.gendat(ibus=ibus)

    @staticmethod
    def plant_data(i=None, intgar=None, realar=None, **kwds):

        return psspy.plant_data(i=i, intgar=intgar, realar=realar, **kwds)

    @staticmethod
    def purgmac(frmbus=None, id=None):

        return psspy.purgmac(frmbus=frmbus, id=id)

    @staticmethod
    def transmission_line_units(ival=None):
        """Set the transmission line units option setting to either per unit or ohms

        transmission_line_units(ival)

        or:

        ival = transmission_line_units()

        IVAL Value of the option setting

        IVAL = 0 per units.
        IVAL = 1 ohms and microfarad
        """
        return_value = psspy.transmission_line_units(ival=ival)

        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        if isinstance(return_value, int):
            ierr = return_value
            val = None
        else:
            (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PsseTransformerUnitsException(ierr, val)

    @staticmethod
    def scal(sid=None, all=None, apiopt=None, status=None, scalval=None, **kwds):
        """Uniformly increase or decrease any or all specified bus quantities for a
        specified group of buses

        - One reference with APIOPT=1, followed by one reference with APIOPT=2.
        - One reference with APIOPT=0. This automatically combines the processing of one

        totals, moto = scal(sid, all, apiopt, status, scalval)

        where:

           SID Is a valid subsystem identifier. Valid subsystem identifiers range from 0 to
           11. Subsystem SID must have been previously defined (input; 0 by default).

           ALL Is the all buses or specified subsystem flag (input; 1 by default).

            ALL = 1 process all buses.
            ALL = 0 process only buses in subsystem SID.

           APIOPT Is the mode of operation in the API (input; 0 by default).

            APIOPT = 0 initialize for scaling, then run the scaling and post-processing
                       housekeeping.
            APIOPT = 1 initialize for scaling.
            APIOPT = 2 run the scaling and post-processing housekeeping.

           TOTALS(11) Is an array of eleven elements returned when APIOPT = 0 or 1.  They are as
           follows.

            TOTALS(1) load Mvar total.
            TOTALS(2) load MW total.
            TOTALS(3) generation MW total.
            TOTALS(4) shunt MW total.
            TOTALS(5) reactor Mvar total.
            TOTALS(6) capacitor Mvar total.
            TOTALS(7) motor load MW total.
            TOTALS(8) generator PMAX.
            TOTALS(9) generator PMIN.
            TOTALS(10) motor load PMIN.
            TOTALS(11) motor load PMAX.

           MOTO Is returned when APIOPT = 0 or 1. It indicates the presence of motors that are
           modeled as conventional generators with negative active power settings.

            MOTO = 0 no motors in the specified subsystem.
            MOTO = 1 motors present in the specified subsystem.

           STATUS(5) Is an array of five elements that are used to control scaling (input). The
           first and fifth elements are checked and saved when APIOPT = 0 or 1; the second, third
           and fourth elements are checked and used when APIOPT = 0 or 2. They are as follows.

            STATUS(1) interruptible load scaling option (0 by default).

               = 0 scale both interruptible and non-interruptible scalable loads.
               = 1 scale only non-interruptible scalable loads.
               = 2 scale only interruptible scalable loads.

            STATUS(2) method used to scale active power load, generation and motor data, and
                      bus shunt data (0 by default).
               = 0 no scaling.
               = 1 specify new total powers.
               = 2 specify percent changes.
               = 3 specify incremental powers.

            STATUS(3) flag to enforce machine power limits (0 by default).

               = 0 ignore machine power limits.
               = 1 enforce machine power limits.

            STATUS(4) flag to specify the scaling rule to be enforced when changing the reactive
                      power load (0 by default).

               = 0 no change.
               = 1 constant P/Q ratio.
               = 2 new total Q load.
               = 3 percent change.
               = 4 new power factor.
               = 5 incremental Q load.

            STATUS(5) is the bus type code flag for load scaling; normally defaulted except when
                      used by OPF (0 by default).

               = 0 all buses in subsystem.
               = 1 only Type 1 buses in subsystem.
               = 2 only Type 2 and 3 buses in subsystem

            SCALVAL(7) Is an array of seven elements used as scaling targets (input). Based on the
            value of STATUS(1), entries (1) through (6) are either total powers (present total power
            by default), percent changes (0.0 by default), or incremental changes (0.0 by default).

               SCALVAL(1) load MW total/percent/increment.
               SCALVAL(2) generation MW total/percent/increment.
               SCALVAL(3) shunt MW total/percent/increment.
               SCALVAL(4) reactor Mvar total/percent/increment.
               SCALVAL(5) capacitor Mvar total/percent/increment.
               SCALVAL(6) motor load MW total/percent/increment.
               SCALVAL(7) reactive load scaling parameter.
                 If STATUS(3) = 2, SCALVAL(7) = new total Mvar load.
                 If STATUS(3) = 3, SCALVAL(7) = percent change (0.0 by default).
                 If STATUS(3) = 4, SCALVAL(7) = new power factor (1.0 by default).
                 If STATUS(3) = 5, SCALVAL(7) = incremental Mvar load change.
        """
        return_value = psspy.scal_2(sid, all, apiopt, status, scalval)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, total, moto) = return_value
        if ierr:
            raise monsterexceptions.PsseScalException(ierr, (total, moto))
        return total, moto

    @staticmethod
    def sysmva():

        return psspy.sysmva()

    @staticmethod
    def base_frequency(rval=None):

        return psspy.base_frequency(rval=rval)

    @staticmethod
    def brndat(ibus=None, jbus=None, ickt=None, string=None):
        return_value = psspy.brndat(ibus=ibus, jbus=jbus, ickt=ickt, string=string)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, rval) = return_value
        if ierr:
            raise monsterexceptions.PsseBrndatException(ierr, rval)
        return rval

    @staticmethod
    def brndt2(ibus=None, jbus=None, ickt=None, string=None):

        return psspy.brndt2(ibus=ibus, jbus=jbus, ickt=ickt, string=string)

    @staticmethod
    def seq_branch_data(i=None, j=None, ickt=None, realar=None, **kwds):

        return psspy.seq_branch_data(i=i, j=j, ickt=ickt, realar=realar, **kwds)

    @staticmethod
    def multi_section_line_edit(i=None, j=None, id=None, intgar=None, **kwds):

        return psspy.multi_section_line_edit(i=i, j=j, id=id, intgar=intgar, **kwds)

    @staticmethod
    def prmdat(string):
        return_value = psspy.prmdat(string)
        if isinstance(return_value, str):
            raise monsterexceptions.PsseBaseException(return_value, None)
        (ierr, val) = return_value
        if ierr:
            raise monsterexceptions.PssePrmdatException(ierr, val)
        return val

    @staticmethod
    def purgbrn(frmbus=None, tobus=None, ckt=None):

        return psspy.purgbrn(frmbus=frmbus, tobus=tobus, ckt=ckt)

    @staticmethod
    def xfrdat(ibus=None, jbus=None, ickt=None, string=None):

        return psspy.xfrdat(ibus=ibus, jbus=jbus, ickt=ickt, string=string)

    @staticmethod
    def xfrint(ibus=None, jbus=None, ickt=None, string=None):

        return psspy.xfrint(ibus=ibus, jbus=jbus, ickt=ickt, string=string)

    @staticmethod
    def psseversion():

        return psspy.psseversion()

    @staticmethod
    def seq_two_winding_data(i=None, j=None, ickt=None, intgar=None, realar=None, **kwds):

        return psspy.seq_two_winding_data(i=i, j=j, ickt=ickt, intgar=intgar, realar=realar, **kwds)

    @staticmethod
    def titldt():

        return psspy.titldt()

    @staticmethod
    def case_title_data(line1=None, line2=None):

        return psspy.case_title_data(line1=line1, line2=line2)


def make_dfx(
        dfxfile,
        subfile=None,
        monfile=None,
        confile=None,
        areas=[],
        buses=[],
        jbuses={},
        monarea=[],
        conarea=[],
        con_voltage_lim=[0, 9E3],
        contypes=None
):
    # Create tempfiles if they don't exists
    subfile = SubTempFile(
        name=subfile,
        areas=areas,
        buses=buses,
        jbuses=jbuses,
        con_areas=conarea,
        mon_areas=monarea,
        con_voltage_lim=con_voltage_lim
    )

    if len(monarea) == 0:
        monsystem = None
    else:
        monsystem = 'MONITOR_SYSTEM'
    monfile = MonTempFile(name=monfile, system=monsystem)
    confile = ConTempFile(name=confile, contypes=contypes)

    try:
        MonsterPssPy.dfax([1, 1, 1], str(subfile), str(monfile), str(confile), dfxfile)
    finally:
        # Remove temporary files
        for fn in [subfile, monfile, confile]:
            fn.cleanup()


if __name__ == '__channelexec__':
    from cPickle import dumps
    while 1:
        x = channel.receive()  # noqa: F821
        if x is None:
            break
        channel.send(dumps(eval('MonsterPssPy' + '.' + x)))  # noqa: F821
