"""
Parameter loading utilities for phenology and infection models.

Loads parameters from CSV files:
- octoPusParameters.csv: phenology, BBCH, and infection model parameters
- hostSusceptibilityParameters.csv: BBCH susceptibility mapping
"""

import os
import pandas as pd
from peronospora.data.phenology.data_structures import (
    Parameters, BBCHParameter, BBCHSusceptibilityParameter,
    Rule310Parameters, LaoreParameters, MisfitsParameters,
    DMCastParameters, EPIParameters, IPIParameters,
    MagareyParameters, UCSCParameters
)


def load_parameters(parameters_dir: str) -> Parameters:
    """
    Load all parameters from CSV files.

    Parameters:
    -----------
    parameters_dir : str
        Path to directory containing parameter CSV files

    Returns:
    --------
    Parameters
        Populated Parameters object
    """
    parameters = Parameters()

    # Load octoPus parameters (phenology, BBCH, and infection models)
    octopus_file = os.path.join(parameters_dir, "octoPusParameters.csv")
    if os.path.exists(octopus_file):
        load_octopus_parameters(octopus_file, parameters)
    else:
        print(f"Warning: octoPusParameters.csv not found at {octopus_file}")

    # Load host susceptibility parameters
    susceptibility_file = os.path.join(parameters_dir, "hostSusceptibilityParameters.csv")
    if os.path.exists(susceptibility_file):
        load_susceptibility_parameters(susceptibility_file, parameters)
    else:
        print(f"Warning: hostSusceptibilityParameters.csv not found at {susceptibility_file}")

    return parameters


def load_octopus_parameters(filepath: str, parameters: Parameters) -> None:
    """
    Load phenology, BBCH, and infection model parameters from octoPusParameters.csv.

    CSV format:
    class,parameter,min,max,value,units
    Phenology,TminPlant,8,5,10,°C
    BBCH,bbch10,0,4,0,BBCH code
    Rule310,baseTemperature,8,12,10,°C
    """
    df = pd.read_csv(filepath)

    for _, row in df.iterrows():
        param_class = row['class']
        param_name = row['parameter']
        param_value = row['value']

        if param_class == 'Phenology':
            _load_phenology_param(parameters, param_name, param_value)

        elif param_class == 'BBCH':
            _load_bbch_param(parameters, param_name, param_value)

        elif param_class == 'Rule310':
            _load_rule310_param(parameters, param_name, param_value)

        elif param_class == 'Laore':
            _load_laore_param(parameters, param_name, param_value)

        elif param_class == 'Misfits':
            _load_misfits_param(parameters, param_name, param_value)

        elif param_class == 'DMCast':
            _load_dmcast_param(parameters, param_name, param_value)

        elif param_class == 'EPI':
            _load_epi_param(parameters, param_name, param_value)

        elif param_class == 'IPI':
            _load_ipi_param(parameters, param_name, param_value)

        elif param_class == 'Magarey':
            _load_magarey_param(parameters, param_name, param_value)

        elif param_class == 'UCSC':
            _load_ucsc_param(parameters, param_name, param_value)


def _load_phenology_param(parameters: Parameters, param_name: str, param_value) -> None:
    """Load phenology parameters."""
    if param_name == 'TminPlant':
        parameters.phenology_parameters.tmin_plant = float(param_value)
    elif param_name == 'ToptPlant':
        parameters.phenology_parameters.topt_plant = float(param_value)
    elif param_name == 'TmaxPlant':
        parameters.phenology_parameters.tmax_plant = float(param_value)
    elif param_name == 'ChillThreshold':
        parameters.phenology_parameters.chill_threshold = float(param_value)
    elif param_name == 'ChillingRequirement':
        parameters.phenology_parameters.chilling_requirement = float(param_value)
    elif param_name == 'CycleLength':
        parameters.phenology_parameters.cycle_length = float(param_value)


def _load_bbch_param(parameters: Parameters, param_name: str, param_value) -> None:
    """Load BBCH parameters."""
    bbch_code_str = param_name.replace('bbch', '')
    try:
        bbch_code = int(bbch_code_str)
        bbch_param = BBCHParameter(bbch_code, float(param_value))
        parameters.bbch_parameters[bbch_code] = bbch_param
    except ValueError:
        print(f"Warning: Could not parse BBCH code from '{param_name}'")


def _load_rule310_param(parameters: Parameters, param_name: str, param_value) -> None:
    """Load Rule310 parameters."""
    if param_name == 'baseTemperature':
        parameters.rule310_parameters.base_temperature = float(param_value)
    elif param_name == 'precipitationThreshold':
        parameters.rule310_parameters.precipitation_threshold = float(param_value)
    elif param_name == 'numberOfHoursToConsider':
        parameters.rule310_parameters.number_of_hours_to_consider = int(float(param_value))
    elif param_name == 'bbchThreshold':
        parameters.rule310_parameters.bbch_threshold = float(param_value)


def _load_laore_param(parameters: Parameters, param_name: str, param_value) -> None:
    """Load Laore parameters."""
    if param_name == 'infectionThresholdRisk':
        parameters.laore_parameters.infection_threshold_risk = float(param_value)


def _load_misfits_param(parameters: Parameters, param_name: str, param_value) -> None:
    """Load Misfits parameters."""
    if param_name == 'LWminMacrosporangiaFormation':
        parameters.misfits_parameters.lw_min_macrosporangia_formation = float(param_value)
    elif param_name == 'LWoptMacrosporangiaFormation':
        parameters.misfits_parameters.lw_opt_macrosporangia_formation = float(param_value)
    elif param_name == 'TminMacrosporangiaInfection':
        parameters.misfits_parameters.tmin_macrosporangia_infection = float(param_value)
    elif param_name == 'ToptMacrosporangiaInfection':
        parameters.misfits_parameters.topt_macrosporangia_infection = float(param_value)
    elif param_name == 'TmaxMacrosporangiaInfection':
        parameters.misfits_parameters.tmax_macrosporangia_infection = float(param_value)
    elif param_name == 'LWminMacrosporangiaInfection':
        parameters.misfits_parameters.lw_min_macrosporangia_infection = float(param_value)
    elif param_name == 'RainStartMacrosporangiaSpread':
        parameters.misfits_parameters.rain_start_macrosporangia_spread = float(param_value)
    elif param_name == 'RHminMacrosporangiaFormation':
        parameters.misfits_parameters.rh_min_macrosporangia_formation = float(param_value)
    elif param_name == 'TminMacrosporangiaFormation':
        parameters.misfits_parameters.tmin_macrosporangia_formation = float(param_value)
    elif param_name == 'ToptMacrosporangiaFormation':
        parameters.misfits_parameters.topt_macrosporangia_formation = float(param_value)
    elif param_name == 'TmaxMacrosporangiaFormation':
        parameters.misfits_parameters.tmax_macrosporangia_formation = float(param_value)


def _load_dmcast_param(parameters: Parameters, param_name: str, param_value) -> None:
    """Load DMCast parameters."""
    if param_name == 'muK1':
        parameters.dmcast_parameters.mu_k1 = float(param_value)
    elif param_name == 'sigmaK1':
        parameters.dmcast_parameters.sigma_k1 = float(param_value)
    elif param_name == 'thresholdPOM':
        parameters.dmcast_parameters.threshold_pom = float(param_value)
    elif param_name == 'precThresholdOosporeGerm':
        parameters.dmcast_parameters.prec_threshold_oospore_germ = float(param_value)
    elif param_name == 'tempThresholdOosporeGerm':
        parameters.dmcast_parameters.temp_threshold_oospore_germ = float(param_value)
    elif param_name == 'tempThresholdSporangiaGerm':
        parameters.dmcast_parameters.temp_threshold_sporangia_germ = float(param_value)
    elif param_name == 'daysForSporangiaGerm':
        parameters.dmcast_parameters.days_for_sporangia_germ = float(param_value)
    elif param_name == 'precThresholdInf':
        parameters.dmcast_parameters.prec_threshold_inf = float(param_value)
    elif param_name == 'tempThresholdInf':
        parameters.dmcast_parameters.temp_threshold_inf = float(param_value)
    elif param_name == 'bbchThreshold':
        parameters.dmcast_parameters.bbch_threshold = float(param_value)
    elif param_name == 'daysForInfection':
        parameters.dmcast_parameters.days_for_infection = float(param_value)


def _load_epi_param(parameters: Parameters, param_name: str, param_value) -> None:
    """Load EPI parameters."""
    if param_name == 'keConstant':
        parameters.epi_parameters.ke_constant = float(param_value)
    elif param_name == 'urUpperThreshold':
        parameters.epi_parameters.ur_upper_threshold = float(param_value)
    elif param_name == 'urLowerThreshold':
        parameters.epi_parameters.ur_lower_threshold = float(param_value)
    elif param_name == 'peConstant':
        parameters.epi_parameters.pe_constant = float(param_value)
    elif param_name == 'alertThreshold':
        parameters.epi_parameters.alert_threshold = float(param_value)
    elif param_name == 'tempThresholdInf':
        parameters.epi_parameters.temp_threshold_inf = float(param_value)
    elif param_name == 'precThresholdInf':
        parameters.epi_parameters.prec_threshold_inf = float(param_value)
    elif param_name == 'bbchThreshold':
        parameters.epi_parameters.bbch_threshold = float(param_value)


def _load_ipi_param(parameters: Parameters, param_name: str, param_value) -> None:
    """Load IPI parameters."""
    if param_name == 'riUpperThreshold':
        parameters.ipi_parameters.ri_upper_threshold = float(param_value)
    elif param_name == 'tmeaniTminThreshold':
        parameters.ipi_parameters.tmeani_tmin_threshold = float(param_value)
    elif param_name == 'tmeaniUpperThreshold':
        parameters.ipi_parameters.tmeani_upper_threshold = float(param_value)
    elif param_name == 'lwiLowerThreshold':
        parameters.ipi_parameters.lwi_lower_threshold = float(param_value)
    elif param_name == 'lwiUpperThreshold':
        parameters.ipi_parameters.lwi_upper_threshold = float(param_value)
    elif param_name == 'rhiUpperThreshold':
        parameters.ipi_parameters.rhi_upper_threshold = float(param_value)
    elif param_name == 'ipiTminThreshold':
        parameters.ipi_parameters.ipi_tmin_threshold = float(param_value)
    elif param_name == 'alertThreshold':
        parameters.ipi_parameters.alert_threshold = float(param_value)
    elif param_name == 'tempThresholdInf':
        parameters.ipi_parameters.temp_threshold_inf = float(param_value)
    elif param_name == 'precThresholdInf':
        parameters.ipi_parameters.prec_threshold_inf = float(param_value)
    elif param_name == 'bbchThreshold':
        parameters.ipi_parameters.bbch_threshold = float(param_value)


def _load_magarey_param(parameters: Parameters, param_name: str, param_value) -> None:
    """Load Magarey parameters."""
    if param_name == 'baseTemperatureRule210':
        parameters.magarey_parameters.base_temperature_rule210 = float(param_value)
    elif param_name == 'precipitationThresholdRule210':
        parameters.magarey_parameters.precipitation_threshold_rule210 = float(param_value)
    elif param_name == 'baseTemperatureInfection':
        parameters.magarey_parameters.base_temperature_infection = float(param_value)
    elif param_name == 'precipitationThresholdInfection':
        parameters.magarey_parameters.precipitation_threshold_infection = float(param_value)
    elif param_name == 'numberOfHoursToConsiderRule210':
        parameters.magarey_parameters.number_of_hours_to_consider_rule210 = float(param_value)
    elif param_name == 'numberOfHoursToConsiderGermination':
        parameters.magarey_parameters.number_of_hours_to_consider_germination = float(param_value)
    elif param_name == 'numberOfHoursToConsiderInfection':
        parameters.magarey_parameters.number_of_hours_to_consider_infection = float(param_value)
    elif param_name == 'degreeHoursThresholdInfection':
        parameters.magarey_parameters.degree_hours_threshold_infection = float(param_value)
    elif param_name == 'rainTriggeringSplash':
        parameters.magarey_parameters.rain_triggering_splash = float(param_value)


def _load_ucsc_param(parameters: Parameters, param_name: str, param_value) -> None:
    """Load UCSC parameters."""
    if param_name == 'vpdThreshold':
        parameters.ucsc_parameters.vpd_threshold = float(param_value)
    elif param_name == 'dormancyBrakingLowerThreshold':
        parameters.ucsc_parameters.dormancy_braking_lower_threshold = float(param_value)
    elif param_name == 'dormancyBrakingUpperThreshold':
        parameters.ucsc_parameters.dormancy_braking_upper_threshold = float(param_value)
    elif param_name == 'germinationThreshold':
        parameters.ucsc_parameters.germination_threshold = float(param_value)
    elif param_name == 'sporangiaSurvivalThreshold':
        parameters.ucsc_parameters.sporangia_survival_threshold = float(param_value)
    elif param_name == 'zoosporeSurvivalThreshold':
        parameters.ucsc_parameters.zoospore_survival_threshold = float(param_value)
    elif param_name == 'infectionThreshold':
        parameters.ucsc_parameters.infection_threshold = float(param_value)
    elif param_name == 'incubationLowerThreshold':
        parameters.ucsc_parameters.incubation_lower_threshold = float(param_value)
    elif param_name == 'incubationUpperThreshold':
        parameters.ucsc_parameters.incubation_upper_threshold = float(param_value)


def load_susceptibility_parameters(filepath: str, parameters: Parameters) -> None:
    """
    Load BBCH susceptibility parameters from hostSusceptibilityParameters.csv.

    CSV format:
    BBCH,susceptibility
    0,0
    12,3.33
    """
    df = pd.read_csv(filepath)

    for _, row in df.iterrows():
        bbch_code = int(row['BBCH'])
        susceptibility = float(row['susceptibility'])

        susceptibility_param = BBCHSusceptibilityParameter(bbch_code, susceptibility)
        parameters.bbch_susceptibility_parameters[bbch_code] = susceptibility_param


def print_parameters_summary(parameters: Parameters) -> None:
    """
    Print a summary of loaded parameters (for debugging).
    """
    print("\n=== Phenology Parameters ===")
    print(f"TminPlant: {parameters.phenology_parameters.tmin_plant}°C")
    print(f"ToptPlant: {parameters.phenology_parameters.topt_plant}°C")
    print(f"TmaxPlant: {parameters.phenology_parameters.tmax_plant}°C")
    print(f"ChillThreshold: {parameters.phenology_parameters.chill_threshold} hours")
    print(f"ChillingRequirement: {parameters.phenology_parameters.chilling_requirement} hours")
    print(f"CycleLength: {parameters.phenology_parameters.cycle_length}°C day")

    print(f"\n=== BBCH Parameters ({len(parameters.bbch_parameters)} stages) ===")
    for bbch_code in sorted(parameters.bbch_parameters.keys()):
        param = parameters.bbch_parameters[bbch_code]
        print(f"BBCH {bbch_code}: {param.cycle_completion}% cycle completion")

    print(f"\n=== Susceptibility Parameters ({len(parameters.bbch_susceptibility_parameters)} stages) ===")
    for bbch_code in sorted(parameters.bbch_susceptibility_parameters.keys()):
        param = parameters.bbch_susceptibility_parameters[bbch_code]
        print(f"BBCH {bbch_code}: {param.susceptibility} susceptibility")

    print(f"\n=== Infection Model Parameters ===")
    print(f"Rule310: base_temp={parameters.rule310_parameters.base_temperature}°C, "
          f"prec_threshold={parameters.rule310_parameters.precipitation_threshold}mm")
    print(f"Laore: infection_threshold={parameters.laore_parameters.infection_threshold_risk}")
    print(f"EPI: ke={parameters.epi_parameters.ke_constant}, pe={parameters.epi_parameters.pe_constant}")
    print(f"IPI: alert_threshold={parameters.ipi_parameters.alert_threshold}")
    print(f"DMCast: mu_k1={parameters.dmcast_parameters.mu_k1}, sigma_k1={parameters.dmcast_parameters.sigma_k1}")
    print(f"Magarey: base_temp_inf={parameters.magarey_parameters.base_temperature_infection}°C")
    print(f"Misfits: lw_opt_formation={parameters.misfits_parameters.lw_opt_macrosporangia_formation}h")
    print(f"UCSC: vpd_threshold={parameters.ucsc_parameters.vpd_threshold}")
