from data_structures import InputDaily, Parameters, Output

class Dormancy:
    """
    Dormancy model for calculating chilling accumulation.
    
    The model calculates the chilling state based on daily minimum and maximum 
    temperatures relative to a chilling threshold. It implements five different
    conditions based on temperature ranges.
    """
    
    @staticmethod
    def run_dormancy(input_daily: InputDaily, parameters: Parameters, output: Output) -> None:
        """
        Run the dormancy model for a single day.
        """
        # Compute average temperature
        average_temperature = (input_daily.temp_max + input_daily.temp_min) / 2.0
        
        # Get chilling threshold from parameters
        chill_threshold = parameters.phenology_parameters.chill_threshold
        
        # Initialize rates
        chill_rate = 0.0
        anti_chill_rate = 0.0
        
        # First condition: Tmin > ChillThreshold AND Tmin >= 0
        if (input_daily.temp_min > chill_threshold and input_daily.temp_min >= 0):
            chill_rate = 0.0
            anti_chill_rate = average_temperature - chill_threshold
            
        # Second condition: Tmin >= 0 AND Tmin <= ChillThreshold AND Tmax > ChillThreshold
        elif (input_daily.temp_min >= 0 and 
              input_daily.temp_min <= chill_threshold and 
              input_daily.temp_max > chill_threshold):
            
            denominator = 2 * (input_daily.temp_max - input_daily.temp_min)
            
            chill_rate = -((average_temperature - input_daily.temp_min) - 
                          (input_daily.temp_max - chill_threshold) ** 2 / denominator)
            
            anti_chill_rate = (input_daily.temp_max - chill_threshold) ** 2 / denominator
            
            # Check if chilling has started
            if not output.outputs_phenology.is_chill_started and chill_rate < 0:
                output.outputs_phenology.is_chill_started = True
                
        # Third condition: Tmin >= 0 AND Tmax <= ChillThreshold
        elif (input_daily.temp_min >= 0 and input_daily.temp_max <= chill_threshold):
            chill_rate = -(average_temperature - input_daily.temp_min)
            anti_chill_rate = 0.0
            
            if not output.outputs_phenology.is_chill_started:
                output.outputs_phenology.is_chill_started = True
                
        # Fourth condition: Tmin < 0 AND Tmax >= 0 AND Tmax <= ChillThreshold
        elif (input_daily.temp_min < 0 and 
              input_daily.temp_max >= 0 and 
              input_daily.temp_max <= chill_threshold):
            
            chill_rate = -(input_daily.temp_max ** 2) / (2 * (input_daily.temp_max - input_daily.temp_min))
            
            if not output.outputs_phenology.is_chill_started:
                output.outputs_phenology.is_chill_started = True
                
            anti_chill_rate = 0.0
            
        # Fifth condition: Tmin < 0 AND Tmax > ChillThreshold
        elif (input_daily.temp_min < 0 and input_daily.temp_max > chill_threshold):
            denominator = 2 * (input_daily.temp_max - input_daily.temp_min)
            
            chill_rate = (-(input_daily.temp_max ** 2) / denominator - 
                         (input_daily.temp_max - chill_threshold) ** 2 / denominator)
            
            if not output.outputs_phenology.is_chill_started:
                output.outputs_phenology.is_chill_started = True
                
            anti_chill_rate = (input_daily.temp_max - chill_threshold) ** 2 / denominator
            
        # Default case (else)
        else:
            anti_chill_rate = 0.0
            chill_rate = 0.0
        
        # Update output rates
        output.outputs_phenology.chill_rate = chill_rate
        output.outputs_phenology.anti_chill_rate = anti_chill_rate
        
        # Update states based on current conditions
        chilling_requirement = parameters.phenology_parameters.chilling_requirement
        
        if (output.outputs_phenology.chill_state > -chilling_requirement and 
            output.outputs_phenology.anti_chill_state == 0):
            
            # Still accumulating chilling
            output.outputs_phenology.chill_state += chill_rate
            # Set anti_chill_rate to 0 during chilling accumulation phase (per C# logic)
            output.outputs_phenology.anti_chill_rate = 0.0
            output.outputs_phenology.anti_chill_state = 0.0
            
        else:
            # Chilling requirement met, now in anti-chilling phase
            output.outputs_phenology.anti_chill_state += anti_chill_rate
            output.outputs_phenology.chill_state += anti_chill_rate
            
            # Prevent chill_state from going positive
            if output.outputs_phenology.chill_state > 0:
                output.outputs_phenology.chill_state = 0.0