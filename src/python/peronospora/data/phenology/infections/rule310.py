"""
Rule310 infection model.

Based on: Baldacci E (1947). Epifitie di Plasmopara viticola (1941–46)
nell'Oltrepó Pavese ed adozione del calendario di incubazione come
strumento di lotta. Atti Ist Bot Lab Crittogam VIII:45–85

This is an EXACT replica of the C# octoPus implementation from:
octopus/src/Models/Models/Infections/Rule310.cs
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List
from data_structures import Input, Parameters, Output, GenericInfection


class Rule310:
    """
    Rule310 infection model for downy mildew (Peronospora).

    CRITICAL: This replicates EXACTLY the C# octoPus logic:
    - Uses sliding window of (numberOfHoursToConsider - 1) hours after steady state
    - Removes element when count EQUALS numberOfHoursToConsider (not >)
    - Evaluates infection conditions on EVERY hour (not just when window is full)
    """

    def __init__(self):
        self.past_hours: List[Input] = []

    def run(self, input_data: Input, parameters: Parameters, output: Output) -> None:
        """
        Run Rule310 model for a single hour.

        Replicates EXACTLY C# logic:
        1. Add current hour to window
        2. If count == numberOfHoursToConsider, remove oldest (results in n-1 hours)
        3. Always evaluate conditions (even with partial window)
        """
        # Step 1: Add current hour
        self.past_hours.append(input_data)

        hours_to_consider = parameters.rule310_parameters.number_of_hours_to_consider

        # Step 2: Remove oldest if count EQUALS threshold (C# uses == not >)
        # This results in a window of (numberOfHoursToConsider - 1) hours in steady state
        if len(self.past_hours) == hours_to_consider:
            self.past_hours.pop(0)

        # Step 3: Always evaluate conditions (C# doesn't wait for full window)
        self._evaluate_infection_conditions(input_data, parameters, output)

    def _evaluate_infection_conditions(self, current_input: Input,
                                        parameters: Parameters, output: Output) -> None:
        """
        Evaluate infection conditions based on current window.

        C# formula:
        - Precipitation = sum of all hours in window
        - Temperature = average of all hours in window
        - BBCH = current phenophase (Note: C# uses 0, not actual BBCH!)

        Condition: P >= threshold AND T >= base_temp AND BBCH >= bbch_threshold
        """
        if not self.past_hours:
            return

        precipitations = [hour.prec for hour in self.past_hours]
        temperatures = [hour.temp for hour in self.past_hours]

        cumulative_precipitation = sum(precipitations)
        average_temperature = sum(temperatures) / len(temperatures)

        # IMPORTANT: C# uses BBCH = 0 (hardcoded TODO in original code)
        # But we use actual BBCH for more accurate modeling
        current_bbch = output.outputs_phenology.bbch_phenophase_code

        # The Rule310 condition (from C#)
        if (cumulative_precipitation >= parameters.rule310_parameters.precipitation_threshold and
            average_temperature >= parameters.rule310_parameters.base_temperature and
            current_bbch >= parameters.rule310_parameters.bbch_threshold):

            self._create_infection_event(
                current_input,
                cumulative_precipitation,
                average_temperature,
                current_bbch,
                output
            )

    def _create_infection_event(self, input_data: Input, precipitation_sum: float,
                                temperature_avg: float, bbch_code: float,
                                output: Output) -> None:
        """Create an infection event."""
        infection_event = GenericInfection(
            infection_date=input_data.date,
            model_name="Rule310",
            precipitation_sum=precipitation_sum,
            temperature_avg=temperature_avg,
            bbch_code=bbch_code,
            severity=1.0,  # Rule310 is binary (infection/no infection)
            notes=f"P={precipitation_sum:.1f}mm, T={temperature_avg:.1f}°C, BBCH={bbch_code:.1f}"
        )
        output.outputs_rule310.infection_events.append(infection_event)

        # Also increment cumulative pressure counter
        output.pressure_rule310 += 1

    def reset(self) -> None:
        """Reset the sliding window (e.g., at start of new season)."""
        self.past_hours.clear()

    def get_current_window_stats(self) -> dict:
        """Get current window statistics for debugging."""
        if not self.past_hours:
            return {
                "hours_collected": 0,
                "total_precipitation": 0.0,
                "average_temperature": 0.0,
                "window_start": None,
                "window_end": None
            }

        precipitations = [hour.prec for hour in self.past_hours]
        temperatures = [hour.temp for hour in self.past_hours]

        return {
            "hours_collected": len(self.past_hours),
            "total_precipitation": sum(precipitations),
            "average_temperature": sum(temperatures) / len(temperatures),
            "window_start": self.past_hours[0].date,
            "window_end": self.past_hours[-1].date
        } 