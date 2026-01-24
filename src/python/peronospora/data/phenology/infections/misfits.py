import sys
import os
import math
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List
from data_structures import Input, Parameters, Output, GenericInfection


class MisfitsInfectionEvent(GenericInfection):
    """Evento di infezione specifico per Misfits con campi aggiuntivi."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.germination_date = None
        self.id_infection = 0


class Misfits:
    """
    Misfits model - Misfits group (2022). 
    A public decision support system for the assessment of plant disease infection risk 
    shared by Italian regions. J Environ Manage 1:317:115365
    """
    
    def __init__(self):
        # Variabili locali per accumulo giornaliero
        self._macrosporangia_formed_daily = 0.0
        self._macrosporangia_spread_daily = 0.0
        self._downy_mildew_infection_daily = 0.0
        self._counter_macrosporangia_suitability = 0.0
    
    def run(self, input_data: Input, parameters: Parameters, output: Output) -> None:
        """Esegue il modello Misfits per dati orari."""
        
        # 1. Reinizializza variabili all'ora 0
        self._reinitialize_variables_at_hour_0(input_data.date.hour, output)
        
        # 2. Verifica condizioni per formazione macrosporangi
        macrosporangia_suitability = self._macrosporangia_formation_suitability(
            input_data, parameters, output
        )
        
        # 3. Gestisce l'incremento della suitability dei macrosporangi
        if macrosporangia_suitability == 1:
            output.outputs_misfits.macrosporangia_suitability_hourly += 1
        else:
            output.outputs_misfits.macrosporangia_suitability_hourly = 0
            
        output.outputs_misfits.macrosporangia_suitability_daily += output.outputs_misfits.macrosporangia_suitability_hourly
        self._counter_macrosporangia_suitability += macrosporangia_suitability
        
        # 4. Calcola funzione temperatura per macrosporangi
        output.outputs_misfits.macrosporangia_temperature_function = self._temperature_function(
            input_data.temp,
            parameters.misfits_parameters.tmax_macrosporangia_formation,
            parameters.misfits_parameters.tmin_macrosporangia_formation,
            parameters.misfits_parameters.topt_macrosporangia_formation
        )
        
        # 5. Scala funzione temperatura su durata umidità
        output.outputs_misfits.macrosporangia_temp_moisture_function = self._macrosporangia_moisture_function(
            output.outputs_misfits, parameters
        )
        
        # 6. Verifica formazione macrosporangi
        if output.outputs_misfits.macrosporangia_temp_moisture_function == 1:
            output.outputs_misfits.macrosporangia_formed_hourly = 1
            output.outputs_misfits.are_macrosporangia_formed = 1
        else:
            output.outputs_misfits.macrosporangia_formed_hourly = 0
            
        # Incrementa ore con macrosporangi formati
        self._macrosporangia_formed_daily += output.outputs_misfits.macrosporangia_formed_hourly
        
        # 7. Verifica diffusione macrosporangi
        if output.outputs_misfits.are_macrosporangia_formed == 1:
            output.outputs_misfits.macrosporangia_spread_hourly = self._macrosporangia_spread_suitability(
                input_data, parameters, output.outputs_misfits
            )
        else:
            output.outputs_misfits.macrosporangia_spread_hourly = 0
            
        self._macrosporangia_spread_daily += output.outputs_misfits.macrosporangia_spread_hourly
        
        # 8. Verifica infezione macrosporangi
        if output.outputs_misfits.are_macrosporangia_spread == 1:
            output.outputs_misfits.downy_mildew_infection_hourly = self._macrosporangia_infection_suitability(
                input_data, parameters, output.outputs_misfits
            )
        else:
            output.outputs_misfits.downy_mildew_infection_hourly = 0
            output.outputs_misfits.macrosporangia_infection_temp_moisture_function = 0
            
        self._downy_mildew_infection_daily += output.outputs_misfits.downy_mildew_infection_hourly
        
        # 9. Integra valori giornalieri alle ore 23
        if input_data.date.hour == 23:
            output.outputs_misfits.macrosporangia_suitability_daily += self._counter_macrosporangia_suitability
            output.outputs_misfits.macrosporangia_formed_daily += self._macrosporangia_formed_daily
            output.outputs_misfits.macrosporangia_spread_daily += self._macrosporangia_spread_daily
            output.outputs_misfits.downy_mildew_infection_daily += self._downy_mildew_infection_daily
        
        # 10. Crea evento di infezione se necessario
        if output.outputs_misfits.downy_mildew_infection_hourly == 1:
            infection_event = MisfitsInfectionEvent(
                infection_date=input_data.date,
                model_name="Misfits",
                precipitation_sum=0.0,  # Non usato direttamente in Misfits
                temperature_avg=input_data.temp,
                bbch_code=0.0,  # Non usato in Misfits
                severity=1.0,  # Binario per Misfits
                notes=f"Misfits infection at {input_data.date}"
            )
            infection_event.germination_date = input_data.date
            infection_event.id_infection = len(output.outputs_misfits.infection_events) + 1
            output.outputs_misfits.infection_events.append(infection_event)
    
    def _reinitialize_variables_at_hour_0(self, hour: int, output: Output) -> None:
        """Reinizializza variabili all'ora 0."""
        if hour == 0:
            output.outputs_misfits.macrosporangia_spread_daily = 0.0
            output.outputs_misfits.macrosporangia_formed_daily = 0.0
            output.outputs_misfits.downy_mildew_infection_hourly = 0
            output.outputs_misfits.macrosporangia_suitability_daily = 0.0
            self._macrosporangia_formed_daily = 0.0
            self._macrosporangia_spread_daily = 0.0
            self._downy_mildew_infection_daily = 0.0
            self._counter_macrosporangia_suitability = 0.0
    
    def _macrosporangia_formation_suitability(self, input_data: Input, parameters: Parameters, output: Output) -> int:
        """Verifica condizioni meteorologiche per formazione macrosporangi."""
        macrosporangia_suitability = 0
        
        # Verifica se ha piovuto
        if input_data.prec > 0:
            output.outputs_misfits.is_rained = 1
        
        # Se c'è bagnatura fogliare, la suitability è vera
        if input_data.lw == 1:
            macrosporangia_suitability = 1
            # Quando c'è bagnatura fogliare, il booleano is_rained è falso
            if input_data.prec == 0:
                output.outputs_misfits.is_rained = 0
        else:
            # Se le foglie sono asciutte, verifica se ha piovuto e RH è sopra soglia (75%)
            if (input_data.prec > 0 or 
                (output.outputs_misfits.is_rained == 1 and 
                 input_data.rh > parameters.misfits_parameters.rh_min_macrosporangia_formation)):
                macrosporangia_suitability = 1
            else:
                macrosporangia_suitability = 0
                output.outputs_misfits.is_rained = 0
        
        return macrosporangia_suitability
    
    def _macrosporangia_spread_suitability(self, input_data: Input, parameters: Parameters, 
                                         outputs_misfits) -> int:
        """Verifica condizioni per diffusione macrosporangi."""
        macrosporangia_spread = 0
        
        # Verifica se ha piovuto
        if input_data.prec > 0:
            outputs_misfits.macrosporangia_precipitation_sum += input_data.prec
        else:
            outputs_misfits.macrosporangia_precipitation_sum = 0
        
        # Se precipitazione cumulative supera soglia
        if outputs_misfits.macrosporangia_precipitation_sum >= parameters.misfits_parameters.rain_start_macrosporangia_spread:
            outputs_misfits.macrosporangia_formed_hourly = 0
            macrosporangia_spread = 1
            outputs_misfits.macrosporangia_precipitation_sum = 0
            outputs_misfits.are_macrosporangia_spread = 1
        
        return macrosporangia_spread
    
    def _macrosporangia_infection_suitability(self, input_data: Input, parameters: Parameters,
                                            outputs_misfits) -> int:
        """Verifica condizioni per infezione da macrosporangi."""
        macrosporangia_suitability = 0
        
        # Verifica range temperatura per infezione
        if (input_data.temp < parameters.misfits_parameters.tmin_macrosporangia_infection or
            input_data.temp > parameters.misfits_parameters.tmax_macrosporangia_infection):
            outputs_misfits.macrosporangia_infection_temp_moisture_function = 0
        else:
            t_function = self._temperature_function(
                input_data.temp,
                parameters.misfits_parameters.tmax_macrosporangia_infection,
                parameters.misfits_parameters.tmin_macrosporangia_infection,
                parameters.misfits_parameters.topt_macrosporangia_infection
            )
            
            outputs_misfits.macrosporangia_infection_temp_moisture_function = (
                parameters.misfits_parameters.lw_min_macrosporangia_infection / t_function
                if t_function > 0 else 0
            )
        
        # Verifica se c'è bagnatura fogliare
        if input_data.lw > 0:
            outputs_misfits.counter_leafwetness_macrosporangia += 1
        else:
            outputs_misfits.counter_leafwetness_macrosporangia = 0
            outputs_misfits.are_macrosporangia_spread = 0
        
        # Verifica condizioni per infezione primaria
        if ((outputs_misfits.counter_leafwetness_macrosporangia >= outputs_misfits.macrosporangia_infection_temp_moisture_function or
             outputs_misfits.counter_leafwetness_macrosporangia >= parameters.misfits_parameters.lw_opt_macrosporangia_formation) and
            outputs_misfits.macrosporangia_infection_temp_moisture_function != 0):
            
            macrosporangia_suitability = 1
            outputs_misfits.counter_leafwetness_macrosporangia = 0
            outputs_misfits.are_macrosporangia_spread = 0
            outputs_misfits.are_macrosporangia_formed = 0
            outputs_misfits.downy_mildew_infection_hourly = 1
        
        return macrosporangia_suitability
    
    def _macrosporangia_moisture_function(self, outputs_misfits, parameters: Parameters) -> int:
        """Calcola funzione umidità per macrosporangi."""
        macrosporangia_moisture_suitability = 0
        
        # Verifica se counter suitability è maggiore di LW non limitante
        if (outputs_misfits.macrosporangia_temperature_function > 0 and
            outputs_misfits.macrosporangia_suitability_hourly >= parameters.misfits_parameters.lw_opt_macrosporangia_formation):
            macrosporangia_moisture_suitability = 1
        # Verifica se counter suitability è sotto LW minimo
        elif (outputs_misfits.macrosporangia_temperature_function == 0 or
              outputs_misfits.macrosporangia_suitability_hourly < parameters.misfits_parameters.lw_min_macrosporangia_formation):
            macrosporangia_moisture_suitability = 0
        # Verifica condizione di suitability basata su LW e T requirement
        else:
            moisture_function = (parameters.misfits_parameters.lw_min_macrosporangia_formation / 
                               outputs_misfits.macrosporangia_temperature_function)
            if moisture_function < 0:
                moisture_function = 0
            
            if outputs_misfits.macrosporangia_suitability_hourly > moisture_function:
                macrosporangia_moisture_suitability = 1
            else:
                macrosporangia_moisture_suitability = 0
        
        return macrosporangia_moisture_suitability
    
    def _temperature_function(self, temperature: float, tmax: float, tmin: float, topt: float) -> float:
        """Calcola funzione temperatura."""
        if temperature < tmin or temperature > tmax:
            return 0.0
        
        first_term = (tmax - temperature) / (tmax - topt)
        second_term = (temperature - tmin) / (topt - tmin)
        exponential = (topt - tmin) / (tmax - topt)
        
        t_function = first_term * (second_term ** exponential)
        return t_function
    
    def reset(self) -> None:
        """Reset del modello."""
        self._macrosporangia_formed_daily = 0.0
        self._macrosporangia_spread_daily = 0.0
        self._downy_mildew_infection_daily = 0.0
        self._counter_macrosporangia_suitability = 0.0