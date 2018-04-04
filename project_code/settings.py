import enum

SettingsEnum = enum.Enum(value='SettingsEnum', names=('PSSE0', 'PSSE1', 'UCT0', 'PSSETest'))
FileTypeEnum = enum.Enum(value='FileTypeEnum', names=('uct', 'psse'))


def get_settings(settings_set_name):
    if settings_set_name == SettingsEnum.UCT0:
        return UCTSettings(settings_name=settings_set_name,
                           input_file_name='example.uct',
                           case_name='Europe',
                           countries=['A', 'B', 'C', 'D2', 'D4', 'D7', 'D8', 'E', 'F', 'G',
                                      'H', 'I', 'J', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S',
                                      'T', 'U', 'V', 'W', 'Y', 'Z', '0'],
                           eps=0.001,
                           do_merge_couplers=True,
                           do_calculate_generator_IF=True,
                           dictVbase_uct={0: 750.0,
                                          1: 380.0,
                                          2: 220.0,
                                          3: 150.0,
                                          4: 120.0,
                                          5: 110.0,
                                          6: 70.0,
                                          7: 27.0,
                                          8: 330.0,
                                          9: 500.0
                                          },
                           )
    elif settings_set_name == SettingsEnum.PSSE0:
        return PsseSettings(settings_name=settings_set_name,
                            input_file_name="Norden2018_tunglast_01A_FI_lines_opened.sav",
                            case_name='Nordics',
                            countries=['DK', 'FI', 'NO', 'SV', 'XX'],
                            eps=0.001,
                            do_merge_couplers=True,
                            do_calculate_generator_IF=True,
                            min_voltage_level_PSSE_kV=80,
                            )

    elif settings_set_name == SettingsEnum.PSSE1:
        return PsseSettings(settings_name=settings_set_name,
                            input_file_name="Norden2018_tunglast_01A_FI_lines_opened.sav",
                            case_name='Nordics',
                            countries=['DK', 'FI', 'NO', 'SV', 'XX'],
                            eps=0.001,
                            do_merge_couplers=True,
                            do_calculate_generator_IF=False,
                            min_voltage_level_PSSE_kV=80,
                            )
    elif settings_set_name == SettingsEnum.PSSETest:
        return PsseSettings(settings_name=settings_set_name,
                            input_file_name="IEEE300Bus.sav",
                            case_name='Test',
                            countries=['A', 'B', 'C'],
                            eps=0.001,
                            do_merge_couplers=True,
                            do_calculate_generator_IF=True,
                            min_voltage_level_PSSE_kV=0,
                            )
    else:
        raise KeyError(f'Settings set name {settings_set_name} not found in available settings.')


# noinspection PyPep8Naming
class Settings:
    """Defines a library of settings.
    input_file_name: takes PSSE .sav files and UCTE files .uct. Input file is assumed to be placed in folder
    source_files.
    case_name: used to determine which country mapping to apply. If you have an input file that is a variation on
    a file that has earlier been used in this calculation, check the case_name of this earlier file and use it.
    If you have an input file where no clear country mapping is yet available, define a new case_name and use this in
    the function set_country to set the country.
    file_type: uct or psse (as enum)
    countries: The list of control area on which the assessment is performed.
    eps: As we are working on numeric value, values below epsilon are
             rounded to 0 and values between 1 - epsilon and 1 + epsilon are
             rounded to 1
    do_merge_couplers: if True, couplers merge buses, if False, not.
    do_calculate_generator_IF: if True, influence factors for generators are also calculated. If false, this is skipped.
    dictVbase_uct: voltages for UCT file setting import - not used for other types of files.
    min_voltage_level_PSSE_kV: minimum votlage level for which file contents are taken into account.
    """

    def __init__(
            self,
            settings_name,
            input_file_name,
            case_name,
            file_type,
            countries,
            eps,
            do_merge_couplers,
            do_calculate_generator_IF,
            dictVbase_uct,
            min_voltage_level_PSSE_kV
    ):
        self.settings_name = settings_name
        self.input_file_name = input_file_name
        self.case_name = case_name
        self.file_type = file_type
        self.countries = countries
        self.eps = eps
        self.do_merge_couplers = do_merge_couplers
        self.do_calculate_generator_IF = do_calculate_generator_IF
        self.dictVbase_uct = dictVbase_uct
        self.min_voltage_level_PSSE_kV = min_voltage_level_PSSE_kV


# noinspection PyPep8Naming
class PsseSettings(Settings):
    def __init__(
            self,
            settings_name,
            input_file_name,
            case_name,
            countries,
            eps,
            do_merge_couplers,
            do_calculate_generator_IF,
            min_voltage_level_PSSE_kV
    ):
        super().__init__(
            settings_name=settings_name,
            input_file_name=input_file_name,
            case_name=case_name,
            file_type=FileTypeEnum.psse,
            countries=countries,
            eps=eps,
            do_merge_couplers=do_merge_couplers,
            do_calculate_generator_IF=do_calculate_generator_IF,
            dictVbase_uct=None,
            min_voltage_level_PSSE_kV=min_voltage_level_PSSE_kV
        )


# noinspection PyPep8Naming
class UCTSettings(Settings):
    def __init__(
            self,
            settings_name,
            input_file_name,
            case_name,
            countries,
            eps,
            do_merge_couplers,
            do_calculate_generator_IF,
            dictVbase_uct
    ):
        super().__init__(
            settings_name=settings_name,
            input_file_name=input_file_name,
            case_name=case_name,
            file_type=FileTypeEnum.uct,
            countries=countries,
            eps=eps,
            do_merge_couplers=do_merge_couplers,
            do_calculate_generator_IF=do_calculate_generator_IF,
            dictVbase_uct=dictVbase_uct,
            min_voltage_level_PSSE_kV=None
        )
