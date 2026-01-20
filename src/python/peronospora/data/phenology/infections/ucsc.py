import sys
import os
import math
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Tuple
from data_structures import Input, Parameters, Output, UCSCInfectionEvent


class UCSC:
    """
    UCSC model - Rossi V, Caffi T, Giosuè S, Bugiani R (2008). 
    A mechanistic model simulating primary infections of downy mildew in grapevine. 
    Ecol Modell 212, 480-491. https://doi.org/10.1016/j.ecolmodel.2007.10.046
    """
    
    def __init__(self):
        # Lista per accumulo hydrothermal time
        self.ht_list: List[float] = []
        # Lista per accumulo pioggia (per funzione GER)
        self.cum_rain: List[float] = []
    
    def run(self, input_data: Input, parameters: Parameters, output: Output) -> None:
        """Esegue il modello UCSC per dati orari."""
        
        # 1. Calcola GER (germinazione) e DOR (dormancy breaking)
        ger_dor = self._ger(input_data, output.outputs_ucsc, parameters.ucsc_parameters)
        ger = int(ger_dor[1])  # Cast da float a int
        dor = ger_dor[0]
        
        # Invia GER all'output
        output.outputs_ucsc.ger = ger
        
        # 2. Se c'è germinazione, crea nuovo evento di infezione
        if ger == 1:
            infection_event = UCSCInfectionEvent()
            infection_event.start_germination = input_data.date
            infection_event.id_infection = len(output.outputs_ucsc.infection_events)
            infection_event.model_name = "UCSC"
            
            # Calcola densità di ogni coorte di oospore
            # NOTA: Nel C# c'è un bug alla riga 31 - usa infectionEvent.cohortDensity che è sempre 0
            # perché l'oggetto è appena stato creato. Replichiamo questo comportamento.
            if len(output.outputs_ucsc.infection_events) > 0:
                dor_1 = 0  # Bug C#: infectionEvent.cohortDensity è sempre 0 per nuovo evento
            else:
                dor_1 = 0.03
            
            output.outputs_ucsc.infection_events.append(infection_event)
            infection_event.cohort_density = dor - dor_1
            
            print(f"UCSC: New germination event started on {input_data.date.strftime('%Y-%m-%d %H:%M:%S')} (cohort density: {infection_event.cohort_density:.4f})")
        
        # 3. Calcola HTi (hydrothermal time)
        hti = self._hti(input_data, output.outputs_ucsc, parameters.ucsc_parameters)
        
        # 4. Processa tutti gli eventi di infezione esistenti
        for event in output.outputs_ucsc.infection_events[:]:  # Copia la lista per evitare modifiche durante iterazione
            if isinstance(event, UCSCInfectionEvent):
                self._process_infection_event(event, input_data, parameters.ucsc_parameters, hti)
        
        # 5. Rimuovi eventi non completati alla fine dell'anno
        last_day_of_year = datetime(input_data.date.year, 12, 31)
        if input_data.date.date() == last_day_of_year.date():
            events_to_remove = [e for e in output.outputs_ucsc.infection_events 
                              if hasattr(e, 'infection') and e.infection == 0]
            for event in events_to_remove:
                output.outputs_ucsc.infection_events.remove(event)
            if events_to_remove:
                print(f"UCSC: Removed {len(events_to_remove)} uncompleted events at year end")
    
    def _hti(self, input_data: Input, ucsc_outputs, ucsc_parameters) -> float:
        """Calcola hydro-thermal time (HT)."""
        hti = 0.0
        last_day_of_year = datetime(input_data.date.year, 12, 31)
        
        if input_data.date.date() < last_day_of_year.date():
            # Calcolo VPD usando il metodo di Monteith e Unsworth (1990)
            svp = 610.7 * (10 ** (7.5 * input_data.temp / (237.3 + input_data.temp)))
            vpd = svp * (1 - input_data.rh / 100)
            
            # Definisci parametro M
            if input_data.prec > 0 or vpd <= ucsc_parameters.vpd_threshold:
                m = 1
            else:
                m = 0
            
            # Calcola HTi
            if input_data.temp > 0:
                hti = m / (1330.1 - 116.19 * input_data.temp + 2.6256 * (input_data.temp ** 2))
            
            self.ht_list.append(hti)
        else:
            # Reset alla fine dell'anno
            self.ht_list = []
        
        # Invia hydrothermal time agli output
        ucsc_outputs.hti = hti
        
        return hti
    
    def _dor(self, input_data: Input, ucsc_outputs) -> float:
        """Calcola rate of dormancy breaking (DOR)."""
        ht = sum(self.ht_list)
        
        # Invia hydrothermal time cumulato agli output
        ucsc_outputs.hts = ht
        
        dor = math.exp(-15.891 * math.exp(-0.653 * (ht + 1)))
        
        # Invia DOR agli output
        ucsc_outputs.dor = dor
        
        return dor
    
    def _ger(self, input_data: Input, ucsc_outputs, ucsc_parameters) -> List[float]:
        """Calcola germinazione di oospore (GER)."""
        dor_ger = []
        dor = self._dor(input_data, ucsc_outputs)
        dor_ger.append(dor)
        
        if (dor >= ucsc_parameters.dormancy_braking_lower_threshold and 
            dor <= ucsc_parameters.dormancy_braking_upper_threshold):
            
            if input_data.prec > 0.2:
                self.cum_rain.append(input_data.prec)
                rain_event = sum(self.cum_rain)
                
                if rain_event > input_data.prec:
                    dor_ger.append(0.0)
                else:
                    dor_ger.append(1.0)
            else:
                self.cum_rain = []
        
        # Se c'è solo DOR nella lista, aggiungi 0 per GER
        if len(dor_ger) == 1:
            dor_ger.append(0.0)
        
        return dor_ger
    
    def _process_infection_event(self, event: UCSCInfectionEvent, input_data: Input, ucsc_parameters, hti: float) -> None:
        """Processa un singolo evento di infezione attraverso tutte le fasi del modello UCSC."""
        
        # ===============================
        # FASE 1: PROCESSO DI GERMINAZIONE
        # ===============================
        if event.germination == 0 and hti > 0:
            event.hydro_thermal_time += hti
        
        # Quando il tempo idrotermale cumulato raggiunge la soglia, la germinazione è completa
        if event.hydro_thermal_time > ucsc_parameters.germination_threshold:
            event.germination = 1
            event.end_germination = input_data.date
            event.hydro_thermal_time = ucsc_parameters.germination_threshold  # Cap al valore soglia
            print(f"UCSC: Germination completed for event {event.id_infection} on {input_data.date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # ===============================
        # FASE 2: SOPRAVVIVENZA SPORANGI
        # ===============================
        if event.germination == 1:
            # Calcola sopravvivenza degli sporangi
            temp_rh_factor = input_data.temp * (1 - input_data.rh / 100)
            sus = 1 / (24 * (5.67 - 0.47 * temp_rh_factor + 0.01 * (temp_rh_factor ** 2)))
            event.sporangia_survival += sus
            
            # Condizione di sopravvivenza
            if event.sporangia_survival <= ucsc_parameters.sporangia_survival_threshold:
                event.germinated_oospores = event.cohort_density
            else:
                event.germinated_oospores = 0
        
        # ===============================
        # FASE 3: RILASCIO ZOOSPORE
        # ===============================
        if event.germinated_oospores > 0:
            if input_data.prec > 0.2:
                event.wet_hours_release += 1
                event.temperature_sum_rel += input_data.temp
                event.average_temp_wet_hours_rel = event.temperature_sum_rel / event.wet_hours_release
            
            # Rilascio zoospore
            if event.average_temp_wet_hours_rel > 0:
                release_threshold = math.exp((-1.022 + 19.634) / event.average_temp_wet_hours_rel)
                
                if event.wet_hours_release >= release_threshold:
                    event.zoospore_release = 1
                    event.zoospore_release_date = input_data.date
                    event.released_zoospores = event.germinated_oospores
                    print(f"UCSC: Zoospore release for event {event.id_infection} on {input_data.date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # ===============================
        # FASE 4: SOPRAVVIVENZA ZOOSPORE
        # ===============================
        if event.zoospore_release == 1:
            event.hours_after_release += 1
            
            if input_data.prec > 0.2:
                event.wet_hours_survival += 1
            
            # Definisci soglia di sopravvivenza
            if event.wet_hours_survival > 0:
                survival_time = event.hours_after_release / event.wet_hours_survival
                if survival_time > ucsc_parameters.zoospore_survival_threshold:
                    event.released_zoospores = 0
        
        # ===============================
        # FASE 5: DISPERSIONE ZOOSPORE
        # ===============================
        if event.released_zoospores > 0:
            if input_data.prec > 0.2:
                event.dispersed_zoospores = event.released_zoospores
                event.zoospore_dispersal = 1
        
        # ===============================
        # FASE 6: INFEZIONE
        # ===============================
        if event.zoospore_dispersal == 1:
            if input_data.prec > 0.2 and event.infection == 0:
                event.wet_hours_infection += 1
                event.temperature_sum_inf += input_data.temp
                event.average_temp_wet_hours_inf = event.temperature_sum_inf / event.wet_hours_infection
            
                # Condizione di infezione - IMPORTANTE: verificare solo quando infection == 0
                wdtwd = event.wet_hours_infection * event.average_temp_wet_hours_inf
                if wdtwd >= ucsc_parameters.infection_threshold:
                    event.infection = 1
                    event.infection_date = input_data.date
                    event.zoospores_causing_infection = event.dispersed_zoospores
                    event.severity = 1.0
                    event.notes = f"UCSC infection: wet_hours={event.wet_hours_infection}, avg_temp={event.average_temp_wet_hours_inf:.1f}°C, WDTWD={wdtwd:.1f}"
                    print(f"UCSC: INFECTION COMPLETED for event {event.id_infection} on {input_data.date.strftime('%Y-%m-%d %H:%M:%S')}!")
                    print(f"  - Wet hours infection: {event.wet_hours_infection}")
                    print(f"  - Average temp wet hours: {event.average_temp_wet_hours_inf:.1f}°C")
                    print(f"  - WDTWD: {wdtwd:.1f}")
                    print(f"  - Zoospores causing infection: {event.zoospores_causing_infection:.4f}")
                else:
                    event.zoospores_causing_infection = 0
        
        # ===============================
        # FASE 7: APPARIZIONE MACCHIE OLEOSE
        # ===============================
        if event.infection == 1:
            # Calcola progresso orario di incubazione (INC) e intervalli di confidenza
            inc_low = 1 / (24 * (45.1 - 3.45 * input_data.temp + 0.073 * (input_data.temp ** 2)))
            inc_up = 1 / (24 * (59.9 - 4.55 * input_data.temp + 0.095 * (input_data.temp ** 2)))
            
            if inc_low > 0 or inc_up > 0:
                event.infection_ci_low += inc_low
                event.infection_ci_up += inc_up
                
                # NOTA: Nel C# c'è una condizione impossibile: infectionCIUp <= incubationUpperThreshold
                # con incubationUpperThreshold = 1.0, ma infectionCIUp aumenta continuamente
                # Questo significa che l'incubation period non viene mai completato dopo un certo punto
                if (event.infection_ci_low >= ucsc_parameters.incubation_lower_threshold and
                    event.infection_ci_up <= ucsc_parameters.incubation_upper_threshold):
                    event.incubation_period = 1
                    event.incubation_date = input_data.date
                    print(f"UCSC: Incubation period completed for event {event.id_infection} on {input_data.date.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def reset(self) -> None:
        """Reset del modello."""
        self.ht_list.clear()
        self.cum_rain.clear()
    
    def get_current_stats(self) -> dict:
        """Ottieni statistiche correnti per debugging."""
        return {
            "ht_list_length": len(self.ht_list),
            "ht_cumulative": sum(self.ht_list),
            "cum_rain_length": len(self.cum_rain),
            "cum_rain_total": sum(self.cum_rain) if self.cum_rain else 0
        }
