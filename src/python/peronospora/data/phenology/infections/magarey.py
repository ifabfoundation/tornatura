import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List
from data_structures import Input, Parameters, Output, MagareyInfectionEvent


class Magarey:
    """
    Magarey model - Magarey P, Wachtel M, Weir F, Seem R (1991). 
    A computer-based simulator for rational management of grapevine downy mildew (Plasmopara viticola). 
    Plant Prot Q 6, 29-33.
    """
    
    def __init__(self):
        # Lista per dati delle ultime 24 ore (rule 2-10)
        self.past_24hours: List[Input] = []
    
    def run(self, input_data: Input, parameters: Parameters, output: Output) -> None:
        """Esegue il modello Magarey per dati orari."""
        
        # 1. Verifica regola 2-10 per iniziare nuovo evento di infezione
        if self._rule_210(input_data, parameters.magarey_parameters) == 1:
            # Crea nuovo evento di infezione
            infection_event = MagareyInfectionEvent()
            infection_event.germination_date = input_data.date
            infection_event.model_name = "Magarey"
            output.outputs_magarey.infection_events.append(infection_event)
            infection_event.id_infection = len(output.outputs_magarey.infection_events)
            print(f"Magarey: New germination event started on {input_data.date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 2. Processa tutti gli eventi di infezione attivi
        events_to_remove = []
        for event in output.outputs_magarey.infection_events:
            if isinstance(event, MagareyInfectionEvent):
                self._process_infection_event(event, input_data, parameters.magarey_parameters)
                
                # Segna eventi da rimuovere se non completati entro 24 ore
                elapsed_hours = (input_data.date - event.germination_date).total_seconds() / 3600
                if elapsed_hours > 24 and event.infection == 0:
                    events_to_remove.append(event)
        
        # 3. Rimuovi eventi non completati
        for event in events_to_remove:
            output.outputs_magarey.infection_events.remove(event)
    
    def _rule_210(self, input_data: Input, magarey_parameters) -> int:
        """
        Implementa la regola 2-10 per l'inizio della germinazione.
        Verifica condizioni di temperatura e precipitazione nelle ultime N ore.
        """
        # Aggiungi dati orari correnti
        self.past_24hours.append(input_data)
        
        # Mantieni finestra mobile per numero di ore configurato
        hours_to_consider = int(magarey_parameters.number_of_hours_to_consider_rule210)
        if len(self.past_24hours) == hours_to_consider:
            self.past_24hours.pop(0)
        
        # Calcola precipitazione totale e temperatura media
        total_precipitation = sum(x.prec for x in self.past_24hours)
        average_temperature = sum(x.temp for x in self.past_24hours) / len(self.past_24hours) if self.past_24hours else 0
        
        # Verifica condizioni
        if (total_precipitation >= magarey_parameters.precipitation_threshold_rule210 and
            average_temperature >= magarey_parameters.base_temperature_rule210):
            return 1
        
        return 0
    
    def _process_infection_event(self, event: MagareyInfectionEvent, input_data: Input, magarey_parameters) -> None:
        """Processa un singolo evento di infezione attraverso le fasi: germinazione, splashing, infezione."""
        
        # ===============================
        # FASE 1: GERMINAZIONE
        # ===============================
        event.germination_hours += 1
        
        if event.germination_hours < magarey_parameters.number_of_hours_to_consider_germination:
            # Accumula dati per valutazione germinazione
            event.temperature_average_germ += (input_data.temp / 
                                             magarey_parameters.number_of_hours_to_consider_germination)
            event.rain_sum_germ += input_data.prec
        
        elif event.germination_hours == magarey_parameters.number_of_hours_to_consider_germination:
            # Verifica occorrenza germinazione
            if (event.temperature_average_germ >= magarey_parameters.base_temperature_infection and
                event.rain_sum_germ >= magarey_parameters.precipitation_threshold_infection):
                event.germination = 1
                print(f"Magarey: Germination completed for event {event.id_infection} on {input_data.date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # ===============================
        # FASE 2: SPLASHING
        # ===============================
        if event.germination == 1 and event.splashing == 0:
            event.infection_hours += 1
            event.splashing_hours += 1
            
            if event.infection_hours <= magarey_parameters.number_of_hours_to_consider_infection:
                # Accumula temperatura per splashing
                event.temperature_average_splash += input_data.temp
                event.rain_sum_splash = input_data.prec  # Precipitazione corrente (non cumulativa)
                
                # Verifica se c'è abbastanza pioggia per causare splashing
                if event.rain_sum_splash >= magarey_parameters.rain_triggering_splash:
                    # Calcola temperatura media fino a questo punto
                    event.temperature_average_splash = event.temperature_average_splash / event.infection_hours
                    
                    if event.temperature_average_splash >= magarey_parameters.base_temperature_infection:
                        event.splashing = 1
                        event.splashing_date = input_data.date
                        print(f"Magarey: Splashing completed for event {event.id_infection} on {input_data.date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # ===============================
        # FASE 3: INFEZIONE
        # ===============================
        if event.splashing == 1:
            event.infection_hours += 1
            
            if event.infection_hours <= magarey_parameters.number_of_hours_to_consider_infection:
                # Accumula degree hours
                event.degree_hours += input_data.temp
                
                # Verifica se raggiunte abbastanza degree hours per infezione
                if event.degree_hours >= magarey_parameters.degree_hours_threshold_infection:
                    # Calcola temperatura media infezione
                    event.temperature_average_inf = event.degree_hours / event.infection_hours
                    
                    # Verifica condizioni finali per infezione
                    if (event.infection_hours <= magarey_parameters.number_of_hours_to_consider_infection and
                        event.temperature_average_inf >= magarey_parameters.base_temperature_infection):
                        
                        event.infection = 1
                        event.infection_date = input_data.date
                        event.severity = 1.0
                        event.notes = f"Magarey infection: germ_temp={event.temperature_average_germ:.1f}°C, splash_temp={event.temperature_average_splash:.1f}°C, inf_temp={event.temperature_average_inf:.1f}°C, degree_hours={event.degree_hours:.1f}"
                        
                        print(f"Magarey: INFECTION COMPLETED for event {event.id_infection} on {input_data.date.strftime('%Y-%m-%d %H:%M:%S')}!")
                        print(f"  - Germination temp: {event.temperature_average_germ:.1f}°C")
                        print(f"  - Splashing temp: {event.temperature_average_splash:.1f}°C")  
                        print(f"  - Infection temp: {event.temperature_average_inf:.1f}°C")
                        print(f"  - Degree hours: {event.degree_hours:.1f}")
    
    def reset(self) -> None:
        """Reset del modello."""
        self.past_24hours.clear()
    
    def get_current_stats(self) -> dict:
        """Ottieni statistiche correnti per debugging."""
        return {
            "past_24hours_count": len(self.past_24hours),
            "last_temp": self.past_24hours[-1].temp if self.past_24hours else 0,
            "last_prec": self.past_24hours[-1].prec if self.past_24hours else 0
        }
