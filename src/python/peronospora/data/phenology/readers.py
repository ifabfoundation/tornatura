"""
Readers for loading data from CSV files.

This module provides functionality to read parameters and weather data
from CSV files into the appropriate data structures.
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import sys
import os

from peronospora.data.phenology.data_structures import (
    Parameters, PhenologyParameters, BBCHParameter, BBCHSusceptibilityParameter,
    Rule310Parameters, LaoreParameters, MisfitsParameters, DMCastParameters,
    EPIParameters, IPIParameters, MagareyParameters, UCSCParameters, InputDaily, Input
)


class ParametersReader:
    """Reader for parameter files."""
    
    @staticmethod
    def read_parameters(file_path: str) -> Parameters:
        """
        Read parameters from CSV file.
        
        Args:
            file_path: Path to the octoPusParameters.csv file
            
        Returns:
            Parameters object with loaded values
        """
        df = pd.read_csv(file_path)
        
        # Create parameters object
        parameters = Parameters()
        
        # Filter phenology parameters
        phenology_df = df[df['class'] == 'Phenology']
        
        # Create PhenologyParameters object with values from CSV
        phenology_params = PhenologyParameters()
        
        for _, row in phenology_df.iterrows():
            param_name = row['parameter']
            param_value = float(row['value'])
            
            # Map parameter names to attributes
            param_mapping = {
                'TminPlant': 'tmin_plant',
                'ToptPlant': 'topt_plant', 
                'TmaxPlant': 'tmax_plant',
                'ChillThreshold': 'chill_threshold',
                'ChillingRequirement': 'chilling_requirement',
                'CycleLength': 'cycle_length'
            }
            
            if param_name in param_mapping:
                setattr(phenology_params, param_mapping[param_name], param_value)
        
        parameters.phenology_parameters = phenology_params
        print(f"Loaded phenology parameters: cycle_length={phenology_params.cycle_length}")
        
        # Load BBCH parameters
        bbch_df = df[df['class'] == 'BBCH']
        bbch_count = 0
        for _, row in bbch_df.iterrows():
            param_name = row['parameter']
            param_value = float(row['value'])
            
            # Extract BBCH code from parameter name (e.g., 'bbch10' -> 10)
            if param_name.startswith('bbch'):
                bbch_code = int(param_name[4:])  # Remove 'bbch' prefix
                parameters.bbch_parameters[bbch_code] = BBCHParameter(
                    bbch_code=bbch_code,
                    cycle_completion=param_value
                )
                bbch_count += 1
        
        print(f"Loaded {bbch_count} BBCH parameters: {sorted(parameters.bbch_parameters.keys())}")
        
        # Load Rule310 parameters
        rule310_df = df[df['class'] == 'Rule310']
        rule310_params = Rule310Parameters()
        
        for _, row in rule310_df.iterrows():
            param_name = row['parameter']
            param_value = row['value']
            
            # Map CSV parameter names to class attributes
            param_mapping = {
                'baseTemperature': 'base_temperature',
                'precipitationThreshold': 'precipitation_threshold',
                'bbchThreshold': 'bbch_threshold',
                'numberOfHoursToConsider': 'number_of_hours_to_consider'
            }
            
            if param_name in param_mapping:
                # Convert to appropriate type
                if param_name == 'numberOfHoursToConsider':
                    setattr(rule310_params, param_mapping[param_name], int(param_value))
                else:
                    setattr(rule310_params, param_mapping[param_name], float(param_value))
        
        parameters.rule310_parameters = rule310_params
        
        # Load Laore parameters
        laore_df = df[df['class'] == 'Laore']
        laore_params = LaoreParameters()
        
        for _, row in laore_df.iterrows():
            param_name = row['parameter']
            param_value = float(row['value'])
            
            # Map CSV parameter names to class attributes
            param_mapping = {
                'infectionThresholdRisk': 'infection_threshold_risk'
            }
            
            if param_name in param_mapping:
                setattr(laore_params, param_mapping[param_name], param_value)
        
        parameters.laore_parameters = laore_params
        print(f"Loaded Laore parameters: infection_threshold_risk={laore_params.infection_threshold_risk}")
        
        # Load Misfits parameters
        misfits_df = df[df['class'] == 'Misfits']
        misfits_params = MisfitsParameters()
        
        for _, row in misfits_df.iterrows():
            param_name = row['parameter']
            param_value = float(row['value'])
            
            # Map CSV parameter names to class attributes
            param_mapping = {
                'LWoptMacrosporangiaFormation': 'lw_opt_macrosporangia_formation',
                'LWminMacrosporangiaFormation': 'lw_min_macrosporangia_formation',
                'TminMacrosporangiaInfection': 'tmin_macrosporangia_infection',
                'ToptMacrosporangiaInfection': 'topt_macrosporangia_infection',
                'TmaxMacrosporangiaInfection': 'tmax_macrosporangia_infection',
                'LWminMacrosporangiaInfection': 'lw_min_macrosporangia_infection',
                'RainStartMacrosporangiaSpread': 'rain_start_macrosporangia_spread',
                'RHminMacrosporangiaFormation': 'rh_min_macrosporangia_formation',
                'TminMacrosporangiaFormation': 'tmin_macrosporangia_formation',
                'ToptMacrosporangiaFormation': 'topt_macrosporangia_formation',
                'TmaxMacrosporangiaFormation': 'tmax_macrosporangia_formation'
            }
            
            if param_name in param_mapping:
                setattr(misfits_params, param_mapping[param_name], param_value)
        
        parameters.misfits_parameters = misfits_params
        print(f"Loaded Misfits parameters: lw_min_formation={misfits_params.lw_min_macrosporangia_formation}, rain_spread={misfits_params.rain_start_macrosporangia_spread}")
        
        # Load DMCast parameters
        dmcast_df = df[df['class'] == 'DMCast']
        dmcast_params = DMCastParameters()
        
        for _, row in dmcast_df.iterrows():
            param_name = row['parameter']
            param_value = float(row['value'])
            
            # Map CSV parameter names to class attributes
            param_mapping = {
                'muK1': 'mu_k1',
                'sigmaK1': 'sigma_k1',
                'thresholdPOM': 'threshold_pom',
                'precThresholdOosporeGerm': 'prec_threshold_oospore_germ',
                'tempThresholdOosporeGerm': 'temp_threshold_oospore_germ',
                'tempThresholdSporangiaGerm': 'temp_threshold_sporangia_germ',
                'daysForSporangiaGerm': 'days_for_sporangia_germ',
                'precThresholdInf': 'prec_threshold_inf',
                'tempThresholdInf': 'temp_threshold_inf',
                'bbchThreshold': 'bbch_threshold',
                'daysForInfection': 'days_for_infection'
            }
            
            if param_name in param_mapping:
                setattr(dmcast_params, param_mapping[param_name], param_value)
        
        parameters.dmcast_parameters = dmcast_params
        print(f"Loaded DMCast parameters: mu_k1={dmcast_params.mu_k1}, threshold_pom={dmcast_params.threshold_pom}")
        
        # Load EPI parameters
        epi_df = df[df['class'] == 'EPI']
        epi_params = EPIParameters()
        
        for _, row in epi_df.iterrows():
            param_name = row['parameter']
            param_value = float(row['value'])
            
            # Map CSV parameter names to class attributes
            param_mapping = {
                'keConstant': 'ke_constant',
                'urUpperThreshold': 'ur_upper_threshold',
                'urLowerThreshold': 'ur_lower_threshold',
                'peConstant': 'pe_constant',
                'alertThreshold': 'alert_threshold',
                'tempThresholdInf': 'temp_threshold_inf',
                'precThresholdInf': 'prec_threshold_inf',
                'bbchThreshold': 'bbch_threshold'
            }
            
            if param_name in param_mapping:
                setattr(epi_params, param_mapping[param_name], param_value)
        
        parameters.epi_parameters = epi_params
        print(f"Loaded EPI parameters: ke_constant={epi_params.ke_constant}, alert_threshold={epi_params.alert_threshold}")
        
        # Load IPI parameters
        ipi_df = df[df['class'] == 'IPI']
        ipi_params = IPIParameters()
        
        for _, row in ipi_df.iterrows():
            param_name = row['parameter']
            param_value = float(row['value'])
            
            # Map CSV parameter names to class attributes
            param_mapping = {
                'riUpperThreshold': 'ri_upper_threshold',
                'tmeaniTminThreshold': 'tmeani_tmin_threshold',
                'tmeaniUpperThreshold': 'tmeani_upper_threshold',
                'lwiLowerThreshold': 'lwi_lower_threshold',
                'lwiUpperThreshold': 'lwi_upper_threshold',
                'rhiUpperThreshold': 'rhi_upper_threshold',
                'ipiTminThreshold': 'ipi_tmin_threshold',
                'alertThreshold': 'alert_threshold',
                'tempThresholdInf': 'temp_threshold_inf',
                'precThresholdInf': 'prec_threshold_inf',
                'bbchThreshold': 'bbch_threshold'
            }
            
            if param_name in param_mapping:
                setattr(ipi_params, param_mapping[param_name], param_value)
        
        parameters.ipi_parameters = ipi_params
        print(f"Loaded IPI parameters: ri_upper_threshold={ipi_params.ri_upper_threshold}, alert_threshold={ipi_params.alert_threshold}")
        
        # Load Magarey parameters
        magarey_df = df[df['class'] == 'Magarey']
        magarey_params = MagareyParameters()
        
        for _, row in magarey_df.iterrows():
            param_name = row['parameter']
            param_value = float(row['value'])
            
            # Map CSV parameter names to class attributes
            param_mapping = {
                'baseTemperatureRule210': 'base_temperature_rule210',
                'precipitationThresholdRule210': 'precipitation_threshold_rule210',
                'baseTemperatureInfection': 'base_temperature_infection',
                'precipitationThresholdInfection': 'precipitation_threshold_infection',
                'numberOfHoursToConsiderRule210': 'number_of_hours_to_consider_rule210',
                'numberOfHoursToConsiderGermination': 'number_of_hours_to_consider_germination',
                'numberOfHoursToConsiderInfection': 'number_of_hours_to_consider_infection',
                'degreeHoursThresholdInfection': 'degree_hours_threshold_infection',
                'rainTriggeringSplash': 'rain_triggering_splash'
            }
            
            if param_name in param_mapping:
                setattr(magarey_params, param_mapping[param_name], param_value)
        
        parameters.magarey_parameters = magarey_params
        print(f"Loaded Magarey parameters: base_temp_rule210={magarey_params.base_temperature_rule210}°C, hours_rule210={magarey_params.number_of_hours_to_consider_rule210}")
        
        # Load UCSC parameters
        ucsc_df = df[df['class'] == 'UCSC']
        ucsc_params = UCSCParameters()
        
        for _, row in ucsc_df.iterrows():
            param_name = row['parameter']
            param_value = float(row['value'])
            
            # Map CSV parameter names to class attributes
            param_mapping = {
                'vpdThreshold': 'vpd_threshold',
                'dormancyBrakingLowerThreshold': 'dormancy_braking_lower_threshold',
                'dormancyBrakingUpperThreshold': 'dormancy_braking_upper_threshold',
                'germinationThreshold': 'germination_threshold',
                'sporangiaSurvivalThreshold': 'sporangia_survival_threshold',
                'zoosporeSurvivalThreshold': 'zoospore_survival_threshold',
                'infectionThreshold': 'infection_threshold',
                'incubationLowerThreshold': 'incubation_lower_threshold',
                'incubationUpperThreshold': 'incubation_upper_threshold'
            }
            
            if param_name in param_mapping:
                setattr(ucsc_params, param_mapping[param_name], param_value)
        
        parameters.ucsc_parameters = ucsc_params
        print(f"Loaded UCSC parameters: vpd_threshold={ucsc_params.vpd_threshold}Kpa, germination_threshold={ucsc_params.germination_threshold}")
        
        return parameters
    
    @staticmethod
    def read_parameters_dict(file_path: str) -> Dict[str, float]:
        """
        Read parameters as a dictionary (like the C# implementation).
        
        Args:
            file_path: Path to the octoPusParameters.csv file
            
        Returns:
            Dictionary with parameter names as keys and values as floats
        """
        df = pd.read_csv(file_path)
        param_dict = {}
        
        for _, row in df.iterrows():
            key = f"{row['class']}_{row['parameter']}"
            param_dict[key] = float(row['value'])
            
        return param_dict
    
    @staticmethod
    def read_susceptibility_parameters(file_path: str) -> Dict[int, BBCHSusceptibilityParameter]:
        """
        Read host susceptibility parameters from CSV file.

        Args:
            file_path: Path to the hostSusceptibilityParameters.csv file

        Returns:
            Dictionary with BBCH codes as keys and BBCHSusceptibilityParameter as values
        """
        df = pd.read_csv(file_path)
        susceptibility_params = {}

        for _, row in df.iterrows():
            bbch_code = int(row['BBCH'])
            susceptibility_score = float(row['susceptibility'])

            susceptibility_params[bbch_code] = BBCHSusceptibilityParameter(
                bbch_code=bbch_code,
                susceptibility=susceptibility_score
            )
        
        print(f"Loaded {len(susceptibility_params)} susceptibility parameters: {sorted(susceptibility_params.keys())}")
        return susceptibility_params
    
    @staticmethod
    def read_all_parameters(octopus_params_path: str, susceptibility_params_path: str) -> Parameters:
        """
        Read all parameters from both CSV files.
        
        Args:
            octopus_params_path: Path to the octoPusParameters.csv file
            susceptibility_params_path: Path to the hostSusceptibilityParameters.csv file
            
        Returns:
            Complete Parameters object with all parameters loaded
        """
        # Read main parameters (including Rule310)
        parameters = ParametersReader.read_parameters(octopus_params_path)
        
        # Read and add susceptibility parameters
        parameters.bbch_susceptibility_parameters = ParametersReader.read_susceptibility_parameters(
            susceptibility_params_path
        )
        
        return parameters


class WeatherReader:
    """Reader for weather data files."""

    @staticmethod
    def read_hourly(file_path: str, start_year: int, end_year: int, forecast_day_range: Tuple[int, int] = None) -> List[Input]:
        """
        Read hourly weather data from CSV file (ECMWF HRES format).

        Args:
            file_path: Path to the weather CSV file
            start_year: Start year for filtering data
            end_year: End year for filtering data
            forecast_day_range: Optional tuple (min_day, max_day) to filter by forecast_day.
                               If None, uses the first occurrence of each datetime.

        Returns:
            List of Input objects sorted by datetime
        """
        df = pd.read_csv(file_path)

        # Check if this is ECMWF HRES format (has forecast_base and forecast_day columns)
        is_hres_format = 'forecast_base' in df.columns and 'forecast_day' in df.columns

        if is_hres_format:
            # Filter by forecast day range if specified
            if forecast_day_range is not None:
                min_day, max_day = forecast_day_range
                df = df[(df['forecast_day'] >= min_day) & (df['forecast_day'] <= max_day)]

            # Handle duplicate datetimes: keep the forecast with minimum lead time (most recent forecast)
            if 'datetime' in df.columns:
                # Use datetime column if available
                df['dt'] = pd.to_datetime(df['datetime'])
            else:
                # Create datetime from components
                df['dt'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])

            # Keep only the first forecast for each datetime (smallest forecast_day)
            df = df.sort_values('forecast_day')
            df = df.drop_duplicates(subset=['dt'], keep='first')

        weather_data = []

        for _, row in df.iterrows():
            # Create datetime object
            if is_hres_format and 'dt' in df.columns:
                date = row['dt'].to_pydatetime()
            else:
                date = datetime(
                    year=int(row['year']),
                    month=int(row['month']),
                    day=int(row['day']),
                    hour=int(row['hour'])
                )

            # Filter by year range
            if start_year <= date.year <= end_year:
                # Create Input object
                weather_input = Input(
                    date=date,
                    temp=float(row['temp']),
                    prec=float(row['prec']),
                    rh=float(row['rh']),
                    lw=float(row['lw'])
                )

                # Add VPD if available
                if 'vpd' in row:
                    weather_input.vpd = float(row['vpd'])

                weather_data.append(weather_input)

        # Sort by datetime to ensure chronological order
        weather_data.sort(key=lambda x: x.date)
        return weather_data

    @staticmethod
    def read_daily(file_path: str, start_year: int, end_year: int, forecast_day_range: Tuple[int, int] = None) -> List[InputDaily]:
        """
        Read daily weather data from CSV file (ECMWF HRES format).

        Args:
            file_path: Path to the weather CSV file
            start_year: Start year for filtering data
            end_year: End year for filtering data
            forecast_day_range: Optional tuple (min_day, max_day) to filter by forecast_day.
                               If None, uses the first occurrence of each date.

        Returns:
            List of InputDaily objects
        """
        df = pd.read_csv(file_path)

        # Check if this is ECMWF HRES format
        is_hres_format = 'forecast_base' in df.columns and 'forecast_day' in df.columns

        if is_hres_format:
            # Filter by forecast day range if specified
            if forecast_day_range is not None:
                min_day, max_day = forecast_day_range
                df = df[(df['forecast_day'] >= min_day) & (df['forecast_day'] <= max_day)]

            # Create date column for deduplication
            df['date_key'] = pd.to_datetime(df[['year', 'month', 'day']])

            # Handle duplicate dates: keep the forecast with minimum lead time
            df = df.sort_values('forecast_day')
            df = df.drop_duplicates(subset=['date_key'], keep='first')

        weather_data = []

        for _, row in df.iterrows():
            # Create datetime object
            date = datetime(
                year=int(row['year']),
                month=int(row['month']),
                day=int(row['day'])
            )

            # Filter by year range
            if start_year <= date.year <= end_year:
                # Handle temperature - use temp_max/temp_min if available, else derive from temp_mean
                if 'temp_max' in row and 'temp_min' in row:
                    temp_max = float(row['temp_max'])
                    temp_min = float(row['temp_min'])
                elif 'temp_mean' in row:
                    # Derive from temp_mean with typical daily range of +/- 5°C
                    temp_mean = float(row['temp_mean'])
                    temp_max = temp_mean + 5.0
                    temp_min = temp_mean - 5.0
                else:
                    # Fallback to default
                    temp_max = 20.0
                    temp_min = 10.0

                # Handle precipitation - check different column names
                if 'prec' in row:
                    prec = float(row['prec'])
                elif 'prec_daily_sum' in row:
                    prec = float(row['prec_daily_sum'])
                else:
                    prec = 0.0

                # Handle relative humidity - check different column names
                if 'rh' in row:
                    rh = float(row['rh'])
                elif 'rh_mean' in row:
                    rh = float(row['rh_mean'])
                else:
                    rh = 70.0

                # Create InputDaily object
                daily_input = InputDaily(
                    date=date,
                    temp_max=temp_max,
                    temp_min=temp_min,
                    prec=prec,
                    site=row.get('site', ''),
                    lw=float(row.get('lw_hours', row.get('lw', 0))),  # lw_hours for HRES, lw for legacy
                    rh=rh
                )

                weather_data.append(daily_input)

        # Sort by date to ensure chronological order
        weather_data.sort(key=lambda x: x.date)
        return weather_data