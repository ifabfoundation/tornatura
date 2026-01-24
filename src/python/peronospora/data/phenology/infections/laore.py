import sys
import os
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List
from data_structures import Input, Parameters, Output, GenericInfection


class Laore:
    """
    Laore model - Reis EM, Sônego OR, Mendes CS (2013). 
    Application and validation of a warning system for grapevine downy mildew control using fungicides. 
    Summa Phytopathologica 39:10-15. https://doi.org/10.1590/S0100-54052013000100002
    """
    
    def __init__(self):
        self.past_hours: List[Input] = []  # Not used in logic but kept for consistency
        self.temperature_list_for_infection: List[float] = []
        self.counter_lw_sporangia: int = 0
    
    def run(self, input_data: Input, parameters: Parameters, output: Output) -> None:
        """Run the Laore model for hourly input data."""
        # Add one hour (kept for consistency with C# code)
        self.past_hours.append(input_data)
        
        # Reset daily variables at midnight (hour 0)
        if input_data.date.hour == 0:
            self.temperature_list_for_infection = []
            self.counter_lw_sporangia = 0
            print(f"Laore: Daily reset at {input_data.date}")
        
        # Collect temperature and count hours with precipitation OR leaf wetness
        if input_data.prec > 0 or input_data.lw == 1:
            self.temperature_list_for_infection.append(input_data.temp)
            self.counter_lw_sporangia += 1
            print(f"Laore: Wet hour collected - temp={input_data.temp:.1f}°C, total_wet_hours={self.counter_lw_sporangia}")
        
        # Calculate daily risk at 23:00
        if input_data.date.hour == 23:
            self._calculate_daily_risk(input_data, parameters, output)
    
    def _calculate_daily_risk(self, input_data: Input, parameters: Parameters, output: Output) -> None:
        """Calculate daily infection risk using the Laore formula."""
        if len(self.temperature_list_for_infection) > 0:
            # Calculate average temperature during wet hours
            avg_temp = sum(self.temperature_list_for_infection) / len(self.temperature_list_for_infection)
            count_lw = float(self.counter_lw_sporangia)
            
            print(f"Laore daily calculation:")
            print(f"  - Average temp during wet hours: {avg_temp:.1f}°C")
            print(f"  - Total wet hours: {count_lw:.0f}")
            
            # Laore formula with three factors
            first_factor = -0.071 + 0.018 * avg_temp - 0.0005 * avg_temp * avg_temp + 0.01
            second_factor = 1 + (math.exp(-(0.24 * count_lw)) + 0.07 * avg_temp * count_lw)
            third_factor = 0.0021 * (avg_temp * avg_temp * count_lw) * -13.44
            
            risk = first_factor * (second_factor - third_factor)
            
            # Risk cannot be negative
            if risk < 0:
                risk = 0.0
            
            print(f"  - First factor: {first_factor:.4f}")
            print(f"  - Second factor: {second_factor:.4f}")
            print(f"  - Third factor: {third_factor:.4f}")
            print(f"  - Final risk: {risk:.3f} (threshold: {parameters.laore_parameters.infection_threshold_risk})")
            
            # Store daily infection risk
            output.outputs_laore.daily_infection_risk = risk
            
            # Check if risk exceeds threshold for infection event
            if risk > parameters.laore_parameters.infection_threshold_risk:
                print(f"Laore INFECTION DETECTED! Risk {risk:.3f} > threshold {parameters.laore_parameters.infection_threshold_risk}")
                self._create_infection_event(input_data, risk, avg_temp, count_lw, output)
            else:
                print(f"Laore: Risk below threshold ({risk:.3f} <= {parameters.laore_parameters.infection_threshold_risk})")
        else:
            print(f"Laore: No wet hours recorded today - no risk calculation")
            output.outputs_laore.daily_infection_risk = 0.0
    
    def _create_infection_event(self, input_data: Input, risk: float, avg_temp: float, 
                              wet_hours: float, output: Output) -> None:
        """Create an infection event."""
        infection_event = GenericInfection(
            infection_date=input_data.date,
            model_name="Laore",
            precipitation_sum=0.0,  # Not directly used in Laore
            temperature_avg=avg_temp,
            bbch_code=0.0,  # Laore doesn't use BBCH
            severity=risk,  # Use risk as severity measure
            notes=f"Laore infection: Risk={risk:.3f}, AvgT={avg_temp:.1f}°C, WetHours={wet_hours:.0f}"
        )
        output.outputs_laore.infection_events.append(infection_event)
    
    def reset(self) -> None:
        """Reset the model state."""
        self.past_hours.clear()
        self.temperature_list_for_infection.clear()
        self.counter_lw_sporangia = 0
        
    def get_current_stats(self) -> dict:
        """Get current model statistics for debugging."""
        return {
            "temperature_records": len(self.temperature_list_for_infection),
            "wet_hours_count": self.counter_lw_sporangia,
            "avg_temp_wet_hours": (sum(self.temperature_list_for_infection) / len(self.temperature_list_for_infection)) if self.temperature_list_for_infection else 0.0
        } 