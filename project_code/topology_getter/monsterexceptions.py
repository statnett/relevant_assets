class PsseBaseException(BaseException):

    def __init__(self, ierr, value, *args, **kwds):
        super(PsseBaseException, self).__init__()
        self._ierr = ierr
        self._args = args
        self._value = value

    def __str__(self):
        if isinstance(self._ierr, str):
            return self._ierr
        try:
            return self._msg_string[self._ierr].format(*self._args)
        except KeyError as e:
            raise KeyError(e + self.__class__)


class PsseNxtLodException(PsseBaseException):
    _msg_string = {
        1: 'No more loads at \'IBUS\'',
        2: '\'INILOD\' was not called for bus \'IBUS\', \'ID\' unchanged.'
    }


class PsseIniLodException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found',
        2: 'Bus has no load entries'
    }


class PsseGetContingencySavedCaseException(PsseBaseException):
    _msg_string = {
        1: 'unable to pick up the base Saved Case File from the ZIP Archive File.',
        2: 'error opening the Incremental Saved Case File.',
        3: 'error closing the Incremental Saved Case File.',
        4: 'prerequisite requirements for API are not met.'
    }


class PssePowerFlowException(PsseBaseException):
    _msg_string = {
        1: 'invalid OPTIONS value.',
        2: 'generators are converted.',
        3: 'buses in island(s) without a swing bus; use activity TREE.',
        4: 'bus type code and series element statusinconsistencies.',
        5: 'prerequisite requirements for API are not met'
    }


class PsseTransformerUnitsException(PsseBaseException):
    _msg_string = {
        1: 'invalid IVAL value',
        2: 'invalid IOCODE value',
        3: 'prerequisite requirements for API are not met'
    }


class PsseBranchDataException(PsseBaseException):
    _msg_string = {
        -1: '\n'.join(
            [
                'data error with one or more of:',
                ' - branch reactance is 0.0',
                ' - line length is negative',
                ' - zero impedance line table is full; branch is treated as a normal line',
                ' - invalid metered end bus',
                ' - invalid branch status',
                ' - invalid owner number',
                ' - invalid ownership fraction',
                ' - no ownership data is specified',
                ' - multi-section line grouping deleted',
                ' - branch ownership table is full--only first n owners re-tained',
                ' - branch is no longer treated as a zero impedance line',
                ' - owner table is full.',
                ' - RATEn is negative.',
                ' - name NAMEAR is assigned to another ac branch.',
            ]
        ),
        1: 'bus not found',
        2: 'circuit identifier is more than two characters',
        3: 'branch exists but it is a two-winding transformer',
        4: 'branch from a bus to itself',
        5: 'blank circuit identifier is invalid',
        6: 'circuit identifier may not start with &',
        7: 'branch table is full',
        8: 'branch ownership table is full',
        10: 'prerequisite requirements for API are not met',
        26: 'branch exists but it is a system switching device',
    }


class PsseInlfException(PsseBaseException):
    _msg_string = {
        1: 'invalid OPTIONS value.',
        2: 'generators are converted.',
        3: 'bus type code and series element status inconsistencies.',
        4: 'error opening IFILE.',
        5: 'prerequisite requirements for API are not met.        '
    }


class PsseDscnException(PsseBaseException):
    _msg_string = {
        1: 'bus not found',
        2: 'prerequisite requirements for API are not met'
    }


class PsseNewcaseException(PsseBaseException):
    _msg_string = {
        1: 'invalid BASEMVA value.',
        2: 'invalid BASEFREQ value.',
        3: 'prerequisite requirements for API are not met.'
    }


class PsseAcccParallelException(PsseBaseException):
    _msg_string = {
        1: 'invalid TOL value.',
        2: 'invalid OPTIONS value.',
        3: 'generators are converted.',
        4: 'buses in island(s) without a swing bus; use activity TREE.',
        5: 'largest mismatch exceeds mismatch tolerance.',
        6: 'generation dispatch subsystem is not defined.',
        7: 'too many islands in base case.',
        8: 'no Distribution Factor Data File specified.',
        9: 'no Contingency Solution Output File specified.',
        10: 'in-service induction machines are in the "stalled" or "tripped" state.',
        11: 'buses with bus type code and series element status inconsistencies.',
        12: 'no ZIP Archive Output File specified.',
        21: 'file DFXFILE is not in the form of a PSSE-25 or later DFAX file; run DFAX.',
        22: 'monitored elements exceed limit when adding multisection line members.',
        51: 'error opening Contingency Solution Output File.',
        52: 'error opening Distribution Factor Data File.',
        53: 'error opening Load Throwover Data File.',
        54: 'error opening Unit Inertia and Governor Data File.',
        55: 'error opening ZIP Archive Output File.',
        56: 'prerequisite requirements for API are not met.',
    }


class PsseMachineDataException(PsseBaseException):
    _msg_string = {
        -1: '\n'.join(
            [
                'data error with one or more of:',
                ' - invalid machine status',
                ' - invalid non-conventional (renewable and infeed type) machine control mode',
                ' - invalid renewable machine power factor',
                ' - invalid ZSORCE: reactance',
                ' - invalid owner number',
                ' - invalid ownership fraction',
                ' - no ownership data is specified',
                ' - QMAX is less than QMIN',
                ' - PMAX is less than PMIN',
                ' - MBASE is not positive',
                ' - non-conventional (renewable and infeed type) machine has negative active power',
                ' - machine is no longer treated as a non-conventional (renewable and infeed type)',
                '   machine'
                ' - non-conventional (renewable and infeed type) machine table is full',
                '    -- retained as a conventional machine',
                ' - machine ownership table is full--only first n owners retained',
                ' - owner table is full.',
                ' - infeed machine Qgen is greater than Qmax -- QGEN set equal to QMAX',
                ' - infeed machine Qgen is less than Qmin -- QGEN set equal to QMIN.',
            ]
        ),
        1: 'bus not found',
        2: 'machine identifier is more than two characters',
        3: 'no plant data at this bus',
        4: 'blank machine identifier is invalid',
        5: 'machine table is full',
        6: 'machine ownership table is full',
        8: 'prerequisite requirements for API are not met',
    }


class PsseBusintException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found; \'VAL\' returned',
        2: 'Bad value of \'STRING\'; \'VAL\' unchanged'
    }


class PsseNewtonToleranceException(PsseBaseException):
    _msg_string = {
        1: 'invalid RVAL value.',
        2: 'invalid IOCODE value.',
        3: 'prerequisite requirements for API are not met.'
    }


class PsseTreeException(PsseBaseException):
    _msg_string = {
        1: 'invalid APIOPT value.',
        2: 'unexpected APIOPT value.',
        3: 'prerequisite requirements for API are not met.'
    }


class PsseSystotException(PsseBaseException):
    _msg_string = {
        1: 'Bad \'STRING\' value; \'P\' and \'Q\' or \'CMPVAL\' unchanged.',
        2: 'No corresponding in-service elements in the case;'
    }


class PsseScalException(PsseBaseException):
    _msg_string = {
        1: 'invalid SID value or subsystem SID is not defined.',
        2: 'invalid ALL value.',
        3: 'invalid APIOPT value.',
        4: 'invalid STATUS value.',
        5: 'unexpected APIOPT value.',
        6: 'invalid power factor in SCALVAL(7).',
        7: 'generator or motor totals beyond limits.',
        8: 'prerequisite requirements for API are not met.'
    }


class PsseBrndatException(PsseBaseException):
    _msg_string = {
        0: 'No error; \'VAL\' returned.',
        1: 'Bus not found; \'VAL\' unchanged.',
        2: 'Branch not found; \'VAL\' unchanged.',
        3: 'Invalid value of \'STRING\'; \'VAL\' unchanged.',
        4: '\'BRNDAT\' invalid with multisection line identifier; \'VAL\' unchanged.',
        5: 'Sequence data not in case; \'VAL\' unchanged.',
        6: 'For STRING = \'FRACTn\', n > number of owners; \'VAL\' unchanged.'
    }


class PsseTr3intException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found',
        2: 'Three-winding transformer not found',
        3: 'Invalid \'STRING\'',
        4: 'Error fetching transformer data',
        5: 'Sequence data not in case for \'STRING\' = \'CZ0\', \'CZG\' or \'CNXCOD\'',
        6: 'With \'STRING\' = OWNn, n > number of owners'
    }


class PsseTr3datException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found',
        2: 'Three-winding transformer not found',
        3: 'Invalid \'STRING\'',
        4: 'Error fetching transformer data',
        6: 'With \'STRING\' = FRACTn, n > number of owners'
    }


class PssePrmdatException(PsseBaseException):
    _msg_string = {
        1: 'Invalid value of \'STRING\'; \'VAL\' unchanged.'
    }


class PsseIniMslException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found; NXTMSL may not be used.',
        2: '& not the first character of \'ICKT\'; NXTMSL may not be used.',
        3: 'Multi-section line not found; NXTMSL may not be used.'
    }


class PsseNxtMslException(PsseBaseException):
    _msg_string = {
        1: 'No more branches in multi-section line; \'IBUS\',\'JBUS\', and \'ICKT\' unchanged.',
        2: '& not the first character of \'ICKT\'; NXTMSL may not be used.',
        3: 'INIMSL was not called; \'IBUS\', \'JBUS\', and \'ICKT\' unchanged.',
    }


class PsseIniBrxException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found; NXT<fun> may not be used.',
        2: 'Invalid \'SINGLE\' value; NXT<fun> may not be used.',
        3: '\'IBUS\' is a multi-section line dummy bus; NXT<fun> may not be used.'
    }


class PsseIniMacException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found; NXTMAC may not be used.',
        2: 'Bus not a generator bus; NXTMAC may not be used.',
    }


class PsseNxtBrnException(PsseBaseException):
    _msg_string = {
        1: 'No more branches from \'IBUS\';',
        2: '\'INIBRX\' was not called for bus \'IBUS\';',
    }


class PsseNxtMacException(PsseBaseException):
    _msg_string = {
        1: 'No more machines at \'IBUS\';',
        2: '\'INIMAC\' was not called for bus \'IBUS\';',
    }


class PsseInitializationException(PsseBaseException):
    _msg_string = {
        1: 'SFILE is blank',
        2: 'error reading from {}',
        3: 'error opening {}',
        4: 'prerequisit requirements for API are not met for',
    }


class PsseBrnintException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found; \'VAL\' unchanged.',
        2: 'Branch not found; \'VAL\' unchanged.',
        3: 'Invalid value of \'STRING\'; \'VAL\' unchanged.',
        5: 'Sequence data not in case; \'VAL\' unchanged.',
        6: 'For \'STRING\' = \'OWNn\', n > number of owners; \'VAL\' unchanged.',
    }


class PsseBrnfloException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found; \'P\' and \'Q\' or \'VAL\' unchanged.',
        2: 'Branch not found; \'P\' and \'Q\' or \'VAL\' unchanged.',
        3: 'Branch is out-of-service; \'P\' and \'Q\' of 0.0 or \'VAL\' of (0.0,0.0) returned.',
    }


class PsseWnddtException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found; \'VAL\' unchanged.',
        2: 'Three-winding transformer not found; \'VAL\' unchanged.',
        3: 'Invalid \'STRING\'; \'VAL\' unchanged.',
        4: 'Error fetching transformer data; \'VAL\' unchanged.',
        5: 'Sequence data not in case',
        7: 'Branch out of service; \'VAL\' returned set to zero.',
        8: 'No base kV at IBUS; \'VAL\' returned = per unit current.',
        9: 'Rating is zero; \'VAL\' returned set to zero'
    }


class PsseLoddtException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found; \'VAL\' unchanged.',
        2: 'Load not found; \'VAL\' unchanged.',
        3: 'Bus type code is not 1, 2 or 3; \'VAL\' returned.',
        4: 'Load out-of-service; \'VAL\' returned.',
        5: 'Invalid value of \'STRING1\' or \'STRING2\'; \'VAL\' unchanged.',
        6: 'Sequence data not in case '
    }


class PsseBusdtException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found; \'VAL\' unchanged.',
        2: 'Bad value of \'STRING1\' or \'STRING2\'; \'VAL\' unchanged.',
        3: 'Bus type code 4 or greater; \'VAL\' returned.',
        4: 'No loads at bus',
        5: 'No switched shunt at bus ',
        6: 'Sequence data not in case '
    }


class PsseMacdtException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found',
        2: 'Machine not found',
        3: 'Bus type code is not 2 or 3',
        4: 'Machine off-line',
        5: 'Invalid value of \'STRING\'',
        6: 'Sequence data not in case ',
    }


class PsseMacdatdException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found',
        2: 'Machine not found',
        3: 'Bus type code is not 2 or 3',
        4: 'Machine off-line',
        5: 'Invalid value of \'STRING\'',
        6: 'For STRING = \'FRACTn\', n > number of owners',
        7: 'For STRING = \'WPF\', this machine is not a wind machine',
        8: 'Sequence data not in case ',
    }


class PsseMacintException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found',
        2: 'Machine not found',
        3: 'Bus type code is not 2 or 3',
        4: 'Machine off-line',
        5: 'Invalid value of \'STRING\'',
        6: 'For STRING = \'FRACTn\', n > number of owners',
        7: 'For STRING = \'OWNn\', n>  number of owners; \'VAL\' unchanged',
        8: 'Sequence data not in case ',
    }


class PsseThreeWndImpedDataException(PsseBaseException):
    _msg_string = {
        -1: 'data error;',
        1: 'bus not found',
        2: 'circuit identifier is more than two characters',
        3: 'invalid CW, CZ and/or CM value',
        4: 'CW, CZ and/or CM >1 but at least one endpoint bus has no base voltage',
        5: 'three different buses must be specified',
        6: 'blank circuit identifier is invalid',
        7: 'transformer circuit identifier may not start with &, * or @.',
        8: 'three-winding transformer table is full',
        9: 'bus table is full',
        10: 'not enough branch table entries are available',
        11: 'not enough two-winding transformer table entries are available.',
        12: 'not enough branch ownership table entries are available.',
        14: 'prerequisite requirements for API are not met.'
    }


class PsseBrnmscException(PsseBaseException):
    _msg_string = {
        1: 'Bus not found; \'VAL\' unchanged.',
        2: 'Branch not found; \'VAL\' unchanged.',
        3: 'Branch out-of-service; \'VAL\' returned set to zero.',
        4: 'No base kV at IBUS; \'VAL\' returned = per unit current.',
        5: 'Invalid \'STRING\'; \'VAL\' unchanged.',
        6: 'Rating is zero; \'VAL\' returned set to zero.',
    }


class PsseAbusException(PsseBaseException):
    _msg_string = {
        1: 'Working case is empty',
        2: 'Invalid SID value',
        3: 'Invalid FLAG value',
        4: 'Invalid NSTR value',
        5: 'DIM, and hence the size of ARRAY, is not large enough',
        6: 'Invalid STRING Value',
        7: 'Sequence data not in case'
    }


class PsseAmachException(PsseAbusException):
    pass


class PsseAloadException(PsseAbusException):
    pass


class PsseAswshException(PsseAbusException):
    pass


class PsseAareaException(PsseAbusException):
    pass


class PsseAgenbusException(PsseAbusException):
    pass


class PsseScreeningException(PsseBaseException):
    _msg_string = {
        1: 'invalid TOL value.',
        2: 'invalid OPTIONS value.',
        3: 'generators are converted.',
        4: 'buses in island(s) without a swing bus; use activity TREE.',
        5: 'largest mismatch exceeds mismatch tolerance.',
        6: 'generation dispatch subsystem is not defined.',
        7: 'too many islands in base case.',
        8: 'no Distribution Factor Data File specified.',
        9: 'no Contingency Solution Output File specified.',
        10: 'in-service induction machines are in the "stalled" or "tripped" state.',
        11: 'buses with bus type code and series element status inconsistencies.',
        12: 'no ZIP Archive Output File specified.',
        21: 'file DFXFILE is not in the form of a PSSE-25 or later DFAX file; run DFAX.',
        22: 'monitored elements exceed limit when adding multisection line members.',
        51: 'error opening Contingency Solution Output File.',
        52: 'error opening Distribution Factor Data File.',
        53: 'error opening Load Throwover Data File.',
        54: 'error opening Unit Inertia and Governor Data File.',
        55: 'error opening ZIP Archive Output File.',
        56: 'prerequisite requirements for API are not met.',
    }


class PsseBsysException(PsseBaseException):
    _msg_string = {
        1: 'SID is not valid',
        2: 'SID is not defined'
    }


class PsseLoadDataException(PsseBaseException):
    _msg_string = {
        -1: '\n'.join([
            'data error with one or more of:',
            ' - invalid load status',
            ' - invalid area, zone or owner number',
            ' - Area table is full',
            ' - Zone table is full',
            ' - Owner table is full'
            ' - (load_chng) invalid load scaling flag.',
            ' - (load_chng) invalid interruptible load flag.',
            ' - (load_chng) invalid load distributed generation flag.',
        ]),
        1: 'bus {} not found',
        2: 'bus {} load identifier {} is more than two characters',
        3: 'blank load identifier is invalid',
        4: 'load table is full',
        5: 'prerequisit requirements for API are not met',
        6: 'prerequisit requirements for API are not met'
    }


class PsseDfaxException(PsseBaseException):
    _msg_string = {
        1: 'invalid OPTIONS value.',
        2: 'generators are converted.',
        3: 'buses in island(s) without a swing bus; useactivity TREE.',
        4: 'no Distribution Factor Data File specified.',
        5: 'no Monitored Element Data input file specified.',
        6: 'no Contingency Description Data file specified.',
        7: 'fatal error reading input file.',
        8: 'error opening output file DFXFILE.',
        9: 'error opening input file SUBFILE.',
        10: 'error opening input file MONFILE.',
        11: 'error opening input file CONFILE.',
        12: 'prerequisite requirements for API are not met.'
    }


class PsseAbrnException(PsseBaseException):
    _msg_string = {
        1: 'Working case is empty.',
        2: 'Invalid SID value.',
        3: 'Invalid OWNER value.',
        4: 'Invalid TIES value.',
        5: 'Invalid FLAG value.',
        6: 'Invalid ENTRY value.',
        7: 'Invalid NSTR value.',
        8: 'DIM, and hence the size of ARRAY, is not large enough.',
        9: 'Invalid STRING value.',
        10: 'Sequence data not in case.'
    }


class PsseAtrnException(PsseAbrnException):
    pass


class PsseAtr3Exception(PsseAbrnException):
    pass


class PsseAlodBusException(PsseBaseException):
    _msg_string = {
        1: 'Working case is empty; BUSES returned as 0.',
        2: 'Invalid SID value; BUSES returned as 0.',
        3: 'Invalid FLAG value; BUSES returned as 0.'
    }


class PsseAwndException(PsseBaseException):
    _msg_string = {
        1: 'Working case is empty; BRNCHS returned as 0.',
        2: 'Invalid SID value; BRNCHS returned as 0.',
        3: 'Invalid OWNER value; BRNCHS returned as 0.',
        4: 'Invalid TIES value; BRNCHS returned as 0.',
        5: 'Invalid FLAG value; BRNCHS returned as 0.',
        6: 'Invalid ENTRY value; BRNCHS returned as 0.'
    }
