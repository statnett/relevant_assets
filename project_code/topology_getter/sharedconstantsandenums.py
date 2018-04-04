import logging

from tools import RaspEnum

logging_level = logging.DEBUG
python_x86_location_environ = 'PYTHON_X86'

display_width = 500

CASEFILES = r'casefiles'
CASETIMEMAPPING = r'casetimemapping'
COMPONENTMAPPING = r'componentmapping'
PROBSTORE = r'probstore'
GISGEODATA = r'gis_geodata'
DEFAULT_FAILURE_DATA = r'default_failure_data'
FAULT_HISTORY = 'fault_history'


RATE_NAME = 'RATEA'


class SolvedStatusEnum(RaspEnum):
    Success = (0, "Solved successfully")
    Iteration_limit_exeeded = (1, "Iteration limit exeeded")
    Blown_up = (2, "Blown up: Only When Non Divergent Option Disabled")
    Non_divergent = (3, "Terminated by non-divergent option")
    Console_interrupt = (4, "Terminated by console interrupt")
    Singular_Jacobian = (5, "Singular Jacobian matrix or voltage of 0.0 detected")
    Inertial_dispatch_error = (6, "Inertial power flow dispatch error (INFL)")
    OPF_success = (7, "OPF solution meter")
    Not_attempted = (9, "Solution not attempted")
    MeasureNotUsed = (999, "Measure Not Used")


class MeasureResultStatus(RaspEnum):
    CompleteSuccess = (0, "Success. No more overloads")
    PartialSuccess = (1, "Success, but not all overloads was removed")
    Failure = (2, "Some failure stopped this measure")
    CouldNotImprove = (3, "Not used. Could not improve with this measure")


class TapAdjustmentEnum(RaspEnum):
    Lock_taps = (0, "Lock taps")
    Stepping = (1, "Stepping")
    Direct = (2, "Direct")


class SwitchedShuntAdjustmentEnum(RaspEnum):
    Lock_all = (0, "Lock all")
    Enable_all = (1, "Enable all")
    Enable_continuous = (2, "Enable continuous, disable discrete")


class InitialOverloads(RaspEnum):
    Report = (0, "Report")
    Ignore = (1, "Ignore")
    Remove = (2, "Remove")


class SolverMethod(RaspEnum):
    fdns = (0, 'Fixed slope decoupled Newton-Raphson')
    fnsl = (1, 'Newon-Raphson')
    nsol = (2, 'Decoupled Newton-Rapshon')


psse_size = 80000
overload_pct_tolerance = 2
