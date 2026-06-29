import math
from peronospora.data.phenology.data_structures import InputDaily, Parameters, Output, BBCHParameter


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
    def generate_detailed_phenology_parameters(parameters: Parameters) -> None:
        """Espande le soglie BBCH GREZZE (sparse) in soglie DETTAGLIATE per ogni
        intero BBCH 10..98. Replica fedele del C# octoPus
        octoPusRunner.generateDetailedPhenologyParameters (chiamata una volta, prima
        del loop fenologico). Senza questo passaggio il BBCH risultava molto in ritardo.
        Idempotente: se i parametri sono già dettagliati non rifà nulla.
        """
        raw = {code: bp.cycle_completion for code, bp in parameters.bbch_parameters.items()}
        if len(raw) > 30:   # già espansi (chiavi intere consecutive)
            return
        if 99 not in raw:
            raw[99] = 100.0
        keys = sorted(raw.keys())
        flowering_fraction = raw[65] / 100.0

        def _li(x1, y1, x2, y2, x):
            if (x2 - x1) == 0:
                return (y2 + y1) / 2.0
            return y1 + (x - x1) * (y2 - y1) / (x2 - x1)

        detailed = {}
        for i in range(len(keys)):
            cur = keys[i]
            if cur < 99:
                nxt = keys[i + 1]
                for j in range(nxt - cur):
                    this = cur + j
                    if nxt < 65:
                        val = _li(cur, raw[cur], nxt, raw[nxt], this) * flowering_fraction
                    elif nxt == 65:
                        val = _li(cur, raw[cur], nxt, 100, this) * flowering_fraction
                    elif nxt < 99:
                        target = flowering_fraction * 100 + raw[nxt] / 100.0 * (100 - raw[cur])
                        val = _li(cur, raw[cur], nxt, target, this)
                    else:
                        start = flowering_fraction * 100 + raw[cur] * (1 - flowering_fraction)
                        val = _li(cur, start, nxt, 100, this)
                    detailed[this] = val
        parameters.bbch_parameters = {
            b: BBCHParameter(bbch_code=b, cycle_completion=v) for b, v in detailed.items()
        }

    @staticmethod
    def compute_bbch(parameters: Parameters, output: Output) -> None:
        """Calcola il codice BBCH dal forcing_state.

        Replica fedele del C# octoPus Forcing.cs computeBBCH(): itera le soglie BBCH
        DETTAGLIATE (chiavi intere consecutive prodotte da
        generate_detailed_phenology_parameters), con accumulo per-coppia e NESSUN
        break (vince l'ultimo match, come nel C#). Validato esatto vs C# in
        fix_fenologia/octopus_core.py (r=1.0000 su bbch_code).
        """
        forcing_state = output.outputs_phenology.forcing_state
        cycle_length = parameters.phenology_parameters.cycle_length
        bbch_params = parameters.bbch_parameters

        bbch_code = 0.0
        for b in sorted(bbch_params.keys()):
            if b < 98 and (b + 1) in bbch_params:
                cum = bbch_params[b].cycle_completion / 100.0 * cycle_length
                nxt = cum + bbch_params[b + 1].cycle_completion / 100.0 * cycle_length
                if cum < forcing_state < nxt:
                    bbch_code = b + (forcing_state - cum) / (nxt - cum)
                    # nessun break: vince l'ultimo match (come nel C#)
        output.outputs_phenology.bbch_phenophase_code = bbch_code
    
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