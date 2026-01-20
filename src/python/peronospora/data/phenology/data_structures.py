"""
Data structures for phenology and infection modeling.

These classes hold the input data, parameters, and output state
for dormancy, forcing, and infection model calculations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


# ============================================================================
# INPUT DATA STRUCTURES
# ============================================================================

@dataclass
class InputDaily:
    """Daily weather input data for phenology and infection models."""
    date: datetime = field(default_factory=datetime.now)
    temp_max: float = 0.0  # Maximum daily temperature (°C)
    temp_min: float = 0.0  # Minimum daily temperature (°C)
    prec: float = 0.0  # Daily precipitation sum (mm)
    lw: float = 0.0  # Daily leaf wetness sum (hours)
    rh: float = 0.0  # Daily mean relative humidity (%)
    site: str = ""


@dataclass
class Input:
    """Hourly weather input data."""
    date: datetime = field(default_factory=datetime.now)
    temp: float = 0.0  # Air temperature (°C)
    prec: float = 0.0  # Precipitation (mm)
    lw: float = 0.0  # Leaf wetness (1=wet, 0=dry)
    rh: float = 0.0  # Relative humidity (%)


# ============================================================================
# PHENOLOGY PARAMETERS
# ============================================================================

@dataclass
class PhenologyParameters:
    """Parameters for phenology models."""
    tmin_plant: float = 10.0  # Minimum temperature for plant development (°C)
    topt_plant: float = 22.0  # Optimal temperature for plant development (°C)
    tmax_plant: float = 35.0  # Maximum temperature for plant development (°C)
    chill_threshold: float = 10.0  # Temperature threshold for chilling (°C)
    chilling_requirement: float = 100.0  # Required chilling hours
    cycle_length: float = 2700.0  # Length of development cycle (°C day)


@dataclass
class BBCHParameter:
    """Single BBCH stage parameter."""
    bbch_code: int = 0
    cycle_completion: float = 0.0


@dataclass
class BBCHSusceptibilityParameter:
    """BBCH susceptibility mapping."""
    bbch_code: int = 0
    susceptibility: float = 0.0


# ============================================================================
# INFECTION MODEL PARAMETERS
# ============================================================================

@dataclass
class Rule310Parameters:
    """Parameters specific to Rule310 model."""
    base_temperature: float = 10.0  # °C
    precipitation_threshold: float = 10.0  # mm
    bbch_threshold: float = 0.0  # BBCH code
    number_of_hours_to_consider: int = 25  # Number of hours for sliding window (from octoPusParameters.csv)


@dataclass
class LaoreParameters:
    """Parameters specific to Laore model."""
    infection_threshold_risk: float = 13.0  # Risk threshold for infection


@dataclass
class MisfitsParameters:
    """Parameters specific to Misfits model."""
    lw_opt_macrosporangia_formation: float = 24.0  # hours
    lw_min_macrosporangia_formation: float = 15.0  # hours
    tmin_macrosporangia_infection: float = 10.0  # °C
    topt_macrosporangia_infection: float = 18.0  # °C
    tmax_macrosporangia_infection: float = 24.0  # °C
    lw_min_macrosporangia_infection: float = 2.0  # hours
    rain_start_macrosporangia_spread: float = 5.0  # mm
    rh_min_macrosporangia_formation: float = 75.0  # %
    tmin_macrosporangia_formation: float = 10.0  # °C
    topt_macrosporangia_formation: float = 18.0  # °C
    tmax_macrosporangia_formation: float = 24.0  # °C


@dataclass
class DMCastParameters:
    """Parameters specific to DMCast model."""
    mu_k1: float = 118.0
    sigma_k1: float = 13.5
    threshold_pom: float = 0.03
    prec_threshold_oospore_germ: float = 2.5  # mm
    temp_threshold_oospore_germ: float = 11.0  # °C
    temp_threshold_sporangia_germ: float = 12.0  # °C
    days_for_sporangia_germ: float = 8.0  # days
    prec_threshold_inf: float = 0.2  # mm
    temp_threshold_inf: float = 11.0  # °C
    bbch_threshold: float = 0.0  # BBCH code
    days_for_infection: float = 11.0  # days


@dataclass
class EPIParameters:
    """Parameters specific to EPI model."""
    ke_constant: float = 0.012
    ur_upper_threshold: float = 90.0  # %
    ur_lower_threshold: float = 65.0  # %
    pe_constant: float = 0.2
    alert_threshold: float = 13.0
    temp_threshold_inf: float = 11.0  # °C
    prec_threshold_inf: float = 2.5  # mm
    bbch_threshold: float = 0.0  # BBCH code


@dataclass
class IPIParameters:
    """Parameters specific to IPI model."""
    ri_upper_threshold: float = 3.0
    tmeani_tmin_threshold: float = 13.0  # °C
    tmeani_upper_threshold: float = 1.0  # °C
    lwi_lower_threshold: float = 1.0  # hours
    lwi_upper_threshold: float = 5.0  # hours
    rhi_upper_threshold: float = 2.0
    ipi_tmin_threshold: float = 9.0  # °C
    alert_threshold: float = 13.0
    temp_threshold_inf: float = 11.0  # °C
    prec_threshold_inf: float = 2.5  # mm
    bbch_threshold: float = 0.0  # BBCH code


@dataclass
class MagareyParameters:
    """Parameters specific to Magarey model."""
    base_temperature_rule210: float = 10.0  # °C
    precipitation_threshold_rule210: float = 10.0  # mm
    base_temperature_infection: float = 8.0  # °C
    precipitation_threshold_infection: float = 2.0  # mm
    number_of_hours_to_consider_rule210: float = 25.0  # hours
    number_of_hours_to_consider_germination: float = 16.0  # hours
    number_of_hours_to_consider_infection: float = 8.0  # hours
    degree_hours_threshold_infection: float = 45.0  # °C day
    rain_triggering_splash: float = 0.5  # mm


@dataclass
class UCSCParameters:
    """Parameters specific to UCSC model."""
    vpd_threshold: float = 450.0  # Kpa
    dormancy_braking_lower_threshold: float = 0.03
    dormancy_braking_upper_threshold: float = 0.97
    germination_threshold: float = 1.0
    sporangia_survival_threshold: float = 1.0
    zoospore_survival_threshold: float = 1.0
    infection_threshold: float = 60.0
    incubation_lower_threshold: float = 1.0
    incubation_upper_threshold: float = 1.0


# ============================================================================
# MAIN PARAMETERS CONTAINER
# ============================================================================

@dataclass
class Parameters:
    """Container for all model parameters."""
    phenology_parameters: PhenologyParameters = field(default_factory=PhenologyParameters)
    bbch_parameters: Dict[int, BBCHParameter] = field(default_factory=dict)
    bbch_susceptibility_parameters: Dict[int, BBCHSusceptibilityParameter] = field(default_factory=dict)
    # Infection model parameters
    rule310_parameters: Rule310Parameters = field(default_factory=Rule310Parameters)
    laore_parameters: LaoreParameters = field(default_factory=LaoreParameters)
    misfits_parameters: MisfitsParameters = field(default_factory=MisfitsParameters)
    dmcast_parameters: DMCastParameters = field(default_factory=DMCastParameters)
    epi_parameters: EPIParameters = field(default_factory=EPIParameters)
    ipi_parameters: IPIParameters = field(default_factory=IPIParameters)
    magarey_parameters: MagareyParameters = field(default_factory=MagareyParameters)
    ucsc_parameters: UCSCParameters = field(default_factory=UCSCParameters)


# ============================================================================
# INFECTION EVENT DATA STRUCTURES
# ============================================================================

@dataclass
class GenericInfection:
    """Generic infection event data structure."""
    infection_date: datetime = field(default_factory=datetime.now)
    model_name: str = ""
    precipitation_sum: float = 0.0
    temperature_avg: float = 0.0
    bbch_code: float = 0.0
    severity: float = 0.0
    notes: str = ""


@dataclass
class MagareyInfectionEvent(GenericInfection):
    """Magarey infection event."""
    temperature_average_germ: float = 0.0
    rain_sum_germ: float = 0.0
    temperature_average_splash: float = 0.0
    rain_sum_splash: float = 0.0
    temperature_average_inf: float = 0.0
    germination_hours: int = 0
    germination: int = 0
    splashing_hours: int = 0
    splashing: int = 0
    infection_hours: int = 0
    degree_hours: float = 0.0
    infection: float = 0.0
    splashing_date: datetime = field(default_factory=datetime.now)
    germination_date: datetime = field(default_factory=datetime.now)


@dataclass
class UCSCInfectionEvent(GenericInfection):
    """UCSC infection event."""
    cohort_density: float = 0.0
    hydro_thermal_time: float = 0.0
    start_germination: datetime = field(default_factory=datetime.now)
    end_germination: datetime = field(default_factory=datetime.now)
    incubation_date: datetime = field(default_factory=datetime.now)
    germination: int = 0
    sporangia_survival: float = 0.0
    germinated_oospores: float = 0.0
    wet_hours_release: int = 0
    temperature_sum_rel: float = 0.0
    average_temp_wet_hours_rel: float = 0.0
    zoospore_release: int = 0
    zoospore_release_date: datetime = field(default_factory=datetime.now)
    released_zoospores: float = 0.0
    hours_after_release: int = 0
    wet_hours_survival: int = 0
    dispersed_zoospores: float = 0.0
    zoospore_dispersal: int = 0
    wet_hours_infection: int = 0
    temperature_sum_inf: float = 0.0
    average_temp_wet_hours_inf: float = 0.0
    infection: int = 0
    zoospores_causing_infection: float = 0.0
    infection_ci_low: float = 0.0
    infection_ci_up: float = 0.0
    incubation_period: int = 0


# ============================================================================
# PHENOLOGY OUTPUT
# ============================================================================

@dataclass
class OutputsPhenology:
    """Phenology state variables that are updated by the models."""
    # Chilling/dormancy states
    chill_rate: float = 0.0
    anti_chill_rate: float = 0.0
    chill_state: float = 0.0
    anti_chill_state: float = 0.0
    is_chill_started: bool = False

    # Forcing states
    forcing_rate: float = 0.0
    forcing_state: float = 0.0
    cycle_completion_percentage: float = 0.0
    bbch_phenophase_code: float = 0.0
    bbch_phenophase: int = 0
    plant_susceptibility: float = 0.0


# ============================================================================
# INFECTION MODEL OUTPUTS
# ============================================================================

@dataclass
class Rule310Output:
    """Output container for Rule310 model results."""
    infection_events: List[GenericInfection] = field(default_factory=list)


@dataclass
class LaoreOutput:
    """Output container for Laore model results."""
    infection_events: List[GenericInfection] = field(default_factory=list)
    daily_infection_risk: float = 0.0


@dataclass
class MisfitsOutput:
    """Output container for Misfits model results."""
    infection_events: List[GenericInfection] = field(default_factory=list)
    macrosporangia_suitability_hourly: float = 0.0
    macrosporangia_suitability_daily: float = 0.0
    macrosporangia_temperature_function: float = 0.0
    macrosporangia_temp_moisture_function: float = 0.0
    macrosporangia_formed_hourly: float = 0.0
    are_macrosporangia_formed: float = 0.0
    macrosporangia_spread_hourly: float = 0.0
    downy_mildew_infection_hourly: float = 0.0
    macrosporangia_infection_temp_moisture_function: float = 0.0
    are_macrosporangia_spread: float = 0.0
    is_rained: float = 0.0
    macrosporangia_precipitation_sum: float = 0.0
    counter_leafwetness_macrosporangia: float = 0.0
    macrosporangia_formed_daily: float = 0.0
    macrosporangia_spread_daily: float = 0.0
    downy_mildew_infection_daily: float = 0.0


@dataclass
class DMCastOutput:
    """Output container for DMCast model results."""
    infection_events: List[GenericInfection] = field(default_factory=list)
    pomsum: float = 0.0


@dataclass
class EPIOutput:
    """Output container for EPI model results."""
    infection_events: List[GenericInfection] = field(default_factory=list)
    epi: float = 0.0
    ke: float = 0.0
    pe: float = 0.0


@dataclass
class IPIOutput:
    """Output container for IPI model results."""
    infection_events: List[GenericInfection] = field(default_factory=list)
    ipisum: float = 0.0


@dataclass
class MagareyOutput:
    """Output container for Magarey model results."""
    infection_events: List[GenericInfection] = field(default_factory=list)


@dataclass
class UCSCOutput:
    """Output container for UCSC model results."""
    infection_events: List[GenericInfection] = field(default_factory=list)
    hti: float = 0.0
    hts: float = 0.0
    dor: float = 0.0
    ger: int = 0


# ============================================================================
# MAIN OUTPUT CONTAINER
# ============================================================================

@dataclass
class Output:
    """Container for all output states."""
    outputs_phenology: OutputsPhenology = field(default_factory=OutputsPhenology)
    # Infection model outputs
    outputs_rule310: Rule310Output = field(default_factory=Rule310Output)
    outputs_laore: LaoreOutput = field(default_factory=LaoreOutput)
    outputs_misfits: MisfitsOutput = field(default_factory=MisfitsOutput)
    outputs_dmcast: DMCastOutput = field(default_factory=DMCastOutput)
    outputs_epi: EPIOutput = field(default_factory=EPIOutput)
    outputs_ipi: IPIOutput = field(default_factory=IPIOutput)
    outputs_magarey: MagareyOutput = field(default_factory=MagareyOutput)
    outputs_ucsc: UCSCOutput = field(default_factory=UCSCOutput)

    # Cumulative pressure counters for each infection model
    pressure_rule310: int = 0
    pressure_epi: int = 0
    pressure_ipi: int = 0
    pressure_dmcast: int = 0
    pressure_magarey: int = 0
    pressure_ucsc: int = 0
    pressure_misfits: int = 0
    pressure_laore: int = 0


# ============================================================================
# UTILITY FUNCTIONS - HOURLY ESTIMATION FROM DAILY DATA
# ============================================================================

def calculate_dew_point(tmax: float, tmin: float) -> float:
    """
    Calculate dew point temperature from daily max/min.

    Replicates C# octoPus weatherReader.dewPoint() method.
    """
    return 0.38 * tmax - 0.018 * (tmax ** 2) + 1.4 * tmin - 5.0


def estimate_hourly_from_daily(input_daily: InputDaily) -> List[Input]:
    """
    Estimate hourly weather data from daily aggregates.

    Replicates EXACTLY the C# octoPus weatherReader.estimateHourly() method.

    Args:
        input_daily: Daily weather data (tmax, tmin, prec)

    Returns:
        List of 24 hourly Input objects for the day

    Estimation methods:
    - Temperature: Cosine function with peak at hour 15 (3 PM)
    - RH: Saturation vapor pressure equations using dew point
    - Rain: Uniform distribution (daily/24) if daily >= 0.2mm
    - Leaf wetness: 1 if prec > 0 OR RH > 90%, else 0
    """
    import math

    hourly_data = []

    # Daily aggregates
    avg_t = (input_daily.temp_max + input_daily.temp_min) / 2.0
    daily_range = input_daily.temp_max - input_daily.temp_min
    dew_point = calculate_dew_point(input_daily.temp_max, input_daily.temp_min)
    rain = input_daily.prec

    # Base date (midnight)
    base_date = datetime(
        input_daily.date.year,
        input_daily.date.month,
        input_daily.date.day
    )

    for hour in range(24):
        hourly = Input()

        # Set datetime
        hourly.date = base_date.replace(hour=hour)

        # Temperature - cosine pattern with peak at hour 15
        # C#: avgT + dailyRange / 2 * Math.Cos(0.2618f * (i - 15))
        hourly_t = avg_t + daily_range / 2.0 * math.cos(0.2618 * (hour - 15))
        hourly.temp = hourly_t

        # Relative Humidity - saturation vapor pressure equations
        # C#: es = 0.61121 * exp((17.502 * hourlyT) / (240.97 + hourlyT))
        # C#: ea = 0.61121 * exp((17.502 * dewPoint) / (240.97 + dewPoint))
        # C#: rh = ea / es * 100
        es = 0.61121 * math.exp((17.502 * hourly_t) / (240.97 + hourly_t))
        ea = 0.61121 * math.exp((17.502 * dew_point) / (240.97 + dew_point))
        rh_hour = ea / es * 100.0
        if rh_hour > 100:
            rh_hour = 100.0
        hourly.rh = rh_hour

        # Rain - uniform distribution if daily >= 0.2mm
        if rain >= 0.2:
            hourly.prec = rain / 24.0
        else:
            hourly.prec = 0.0

        # Leaf wetness - rough estimate (same as C#)
        if hourly.prec > 0 or hourly.rh > 90:
            hourly.lw = 1.0
        else:
            hourly.lw = 0.0

        hourly_data.append(hourly)

    return hourly_data
