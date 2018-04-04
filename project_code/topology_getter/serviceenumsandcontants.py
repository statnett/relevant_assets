from tools import RaspEnum

Python27Path = "C:\Python27\python.exe"
Python27_64Path = "C:\Python27_64\python.exe"
Service_Phase = float(9999)
Time_My_Code = False
number_of_contingencies_for_screening = 6


class ComponentStatusEnum(RaspEnum):
    ReconnectedService = (-2, "ReconnectedService")
    Reconnected = (-1, "Reconnected")
    Service = (1, "Service")
    Disconnected = (2, "Disconnected")


class MonsterModulesEnum(RaspEnum):
    PreProcess = (1, "Pre process")
    Rasp = (2, "Rasp")
    MonteCarlo = (3, "Monte carlo")
    ServicePlan = (4, "Service plan")
    PostProcess = (5, "Post process")


class RemedialMeasuresEnum(RaspEnum):
    ConfigModel = (0, "ConfigModel")
    InitialSolution = (1, "Initial Solution")
    LoadReduction = (2, "Load Reduction")
    LoadReductionDroop = (3, "Load Reduction Droop")
    LoadReductionSequential = (4, "Load Reduction")
    MoveLoad = (5, "Move Load")
    ChangeProduction = (6, "Change Production")
    ChangeProductionDroop = (7, "Change Production with droop")
    CombinedLoadChangeProduction = (8, "Combined load and change production")
    CombinedLoadChangeProductionDroop = (9, "Combined load and change production with droop")
    CombinedAll = (10, "Combined all")
    CombinedAllDroop = (11, "Combined all with droop")
    TripNextOverload = (12, "Tripp next overload")
    TripLine = (13, "Tripp line")


class ComponentTypeEnum(RaspEnum):
    BaseComponent = (0, 'BaseComponent')
    BusComponent = (1, 'BusComponent')
    BranchComponent = (2, 'BranchComponent')
    OverHeadLineComponent = (3, 'OverHeadLineComponent')
    TwoWindingTransformerComponent = (4, 'TwoWindingTransformerComponent')
    ThreeWindingTransformerComponent = (5, 'ThreeWindingTransformerComponent')
    LoadComponent = (6, 'LoadComponent')
    MachineComponent = (7, 'MachineComponent')
    CableComponent = (8, 'CableComponent')
    LineComponent = (9, 'LineComponent')


class ComponentStatus(RaspEnum):
    on = (1, 'on')
    off = (0, 'off')


class BusType(RaspEnum):
    PQ = (1, "PQ")
    PV = (2, "PV")
    swing = (3, "swing")
    disconnected = (4, "disconnected")


class WeatherTypeEnum(RaspEnum):
    Wind = (1, 'wind')
    Lightning = (2, 'lightning')
    Ice_Snow = (3, 'ice_snow')
    Other = (4, 'other')


class FailureSourceEnum(RaspEnum):
    Wind = (1, 'wind')
    Lightning = (2, 'lightning')
    Ice_Snow = (3, 'ice_snow')
    Other = (4, 'other')
    Maintenance = (5, 'maintenance')


class FailureTypeEnum(RaspEnum):
    Permanent = (1, 'permanent')
    Temporary = (2, 'temporary')


class FailureTypeWithMaintenanceEnum(RaspEnum):
    Permanent = (1, 'permanent')
    Temporary = (2, 'temporary')
    Maintenance = (3, 'maintenance')
