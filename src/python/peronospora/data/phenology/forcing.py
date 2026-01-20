import math
from data_structures import InputDaily, Parameters, Output


class Forcing:
    """
    Forcing model for calculating plant development after chilling requirements are met.
    
    Based on: Misfits group (2022). A public decision support system for the assessment 
    of plant disease infection risk shared by Italian regions. 
    J Environ Manage 1:317:115365
    """
    
    @staticmethod
    def run_forcing(input_daily: InputDaily, parameters: Parameters, output: Output) -> None:
        """Run the forcing model for a single day."""
        # Compute average temperature
        average_temperature = (input_daily.temp_max + input_daily.temp_min) / 2.0
        
        # The forcing rate is computed only if the chill state is >= 0 and chill is started
        if (output.outputs_phenology.chill_state >= 0 and 
            output.outputs_phenology.is_chill_started):
            
            # Compute forcing rate
            temp_function = Forcing.temperature_function(
                average_temperature,
                parameters.phenology_parameters.tmax_plant,
                parameters.phenology_parameters.tmin_plant,
                parameters.phenology_parameters.topt_plant
            )
            
            output.outputs_phenology.forcing_rate = (
                (parameters.phenology_parameters.topt_plant - parameters.phenology_parameters.tmin_plant) *
                temp_function
            )
            
            output.outputs_phenology.forcing_state += output.outputs_phenology.forcing_rate
        else:
            output.outputs_phenology.forcing_rate = 0.0
            output.outputs_phenology.forcing_state = 0.0
        
        # Compute cycle completion percentage
        output.outputs_phenology.cycle_completion_percentage = (
            (output.outputs_phenology.forcing_state / parameters.phenology_parameters.cycle_length) * 100
        )
        
        # Check if the cycle is completed
        if output.outputs_phenology.cycle_completion_percentage >= 100:
            output.outputs_phenology.cycle_completion_percentage = 100.0
            output.outputs_phenology.forcing_state = parameters.phenology_parameters.cycle_length
        
        # Compute BBCH code
        Forcing.compute_bbch(parameters, output)
        
        # Update BBCH phenophase (integer part of BBCH code)
        output.outputs_phenology.bbch_phenophase = int(float(output.outputs_phenology.bbch_phenophase_code))
        
        # Compute host susceptibility
        Forcing.phenological_susceptibility(parameters, output)
    
    @staticmethod
    def compute_bbch(parameters: Parameters, output: Output) -> None:
        """Compute BBCH code based on forcing state."""
        forcing_state = output.outputs_phenology.forcing_state
        cycle_length = parameters.phenology_parameters.cycle_length
        
        # Get all BBCH keys sorted
        bbch_keys = sorted(parameters.bbch_parameters.keys())
        
        if forcing_state <= 0 or len(bbch_keys) == 0:
            output.outputs_phenology.bbch_phenophase_code = 0.0
            return
        
        # Debug info (disabled for production)
        # if forcing_state > 100:  # Only log when forcing starts being significant
        #     print(f"DEBUG: forcing_state={forcing_state:.1f}, cycle_length={cycle_length}, bbch_keys={bbch_keys}")
        
        # Loop through consecutive BBCH pairs
        for i in range(len(bbch_keys) - 1):
            current_bbch = bbch_keys[i]
            next_bbch = bbch_keys[i + 1]
            
            # Current threshold
            current_threshold = (
                parameters.bbch_parameters[current_bbch].cycle_completion / 100.0 *
                cycle_length
            )
            
            # Next threshold
            next_threshold = (
                parameters.bbch_parameters[next_bbch].cycle_completion / 100.0 *
                cycle_length
            )
            
            # Debug thresholds (disabled for production)
            # if forcing_state > 100:
            #     print(f"  Checking BBCH {current_bbch}->{next_bbch}: thresholds {current_threshold:.1f} to {next_threshold:.1f}")
            
            # Check if forcing state is between thresholds
            if current_threshold <= forcing_state < next_threshold:
                # Interpolate BBCH code between current and next BBCH
                if next_threshold > current_threshold:
                    progress = (forcing_state - current_threshold) / (next_threshold - current_threshold)
                    output.outputs_phenology.bbch_phenophase_code = current_bbch + (next_bbch - current_bbch) * progress
                else:
                    output.outputs_phenology.bbch_phenophase_code = current_bbch
                
                # print(f"BBCH Update: forcing={forcing_state:.1f}, between {current_bbch} and {next_bbch}, final={output.outputs_phenology.bbch_phenophase_code:.1f}")
                return
        
        # If forcing is beyond the last threshold, use the last BBCH
        last_bbch = bbch_keys[-1]
        last_threshold = (
            parameters.bbch_parameters[last_bbch].cycle_completion / 100.0 * cycle_length
        )
        
        if forcing_state >= last_threshold:
            output.outputs_phenology.bbch_phenophase_code = last_bbch
            # print(f"BBCH Final: forcing={forcing_state:.1f} >= last_threshold={last_threshold:.1f}, BBCH={last_bbch}")
        else:
            # If forcing is less than the first threshold, use the first BBCH
            first_bbch = bbch_keys[0]
            first_threshold = (
                parameters.bbch_parameters[first_bbch].cycle_completion / 100.0 * cycle_length
            )
            
            if forcing_state < first_threshold:
                # Proportional to the first BBCH
                if first_threshold > 0:
                    progress = forcing_state / first_threshold
                    output.outputs_phenology.bbch_phenophase_code = first_bbch * progress
                else:
                    output.outputs_phenology.bbch_phenophase_code = 0.0
                
                # if forcing_state > 10:  # Only log when there's some meaningful forcing
                #     print(f"BBCH Early: forcing={forcing_state:.1f} < first_threshold={first_threshold:.1f}, BBCH={output.outputs_phenology.bbch_phenophase_code:.1f}")
    
    @staticmethod
    def phenological_susceptibility(parameters: Parameters, output: Output) -> None:
        """Compute host susceptibility based on BBCH stage."""
        pheno_susceptibility = 0.0
        bbch = output.outputs_phenology.bbch_phenophase_code
        
        # Get BBCH susceptibility keys
        bbch_keys = list(parameters.bbch_susceptibility_parameters.keys())
        
        if not bbch_keys:
            print(f"WARNING: No susceptibility parameters loaded!")
            output.outputs_phenology.plant_susceptibility = 0.0
            return
        
        min_bbch = min(bbch_keys)
        max_bbch = max(bbch_keys)
        
        if min_bbch < bbch < max_bbch:
            # BBCH is between min and max - interpolate
            x1 = max([key for key in bbch_keys if key < bbch])
            x2 = min([key for key in bbch_keys if key >= bbch])
            
            y1 = parameters.bbch_susceptibility_parameters[x1].susceptibility
            y2 = parameters.bbch_susceptibility_parameters[x2].susceptibility
            
            if (x2 - x1) == 0:
                pheno_susceptibility = (y2 + y1) / 2.0
            else:
                # Linear interpolation
                pheno_susceptibility = y1 + (bbch - x1) * (y2 - y1) / (x2 - x1)
                
        elif bbch <= min_bbch:
            # BBCH is below or equal minimum - use minimum susceptibility
            pheno_susceptibility = parameters.bbch_susceptibility_parameters[min_bbch].susceptibility
            
        elif bbch >= max_bbch:
            # BBCH is above or equal maximum - use maximum susceptibility  
            pheno_susceptibility = parameters.bbch_susceptibility_parameters[max_bbch].susceptibility
        
        output.outputs_phenology.plant_susceptibility = pheno_susceptibility
        
        # Debug per primi cambiamenti significativi (disabled for production)
        # if bbch > 1 and pheno_susceptibility > 0:
        #     print(f"Susceptibility Update: bbch={bbch:.1f}, susceptibility={pheno_susceptibility:.1f}")
    
    @staticmethod
    def temperature_function(temperature: float, tmax: float, tmin: float, topt: float) -> float:
        """Temperature response function for forcing rate calculation."""
        if temperature < tmin or temperature > tmax:
            return 0.0
        
        first_term = (tmax - temperature) / (tmax - topt)
        second_term = (temperature - tmin) / (topt - tmin)
        exponential = (topt - tmin) / (tmax - topt)
        
        t_function = first_term * (second_term ** exponential)
        
        return t_function