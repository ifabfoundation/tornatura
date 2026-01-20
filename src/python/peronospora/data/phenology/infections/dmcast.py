import sys
import os
import math
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Dict
from data_structures import Input, Parameters, Output, GenericInfection


class DMCastInfectionEvent(GenericInfection):
    """Evento di infezione specifico per DMCast con campi aggiuntivi."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.germination_date = None
        self.infection = 0.0
        self.infection_hours = 0
        self.rain_sum_splash = 0.0
        self.sporangia_germination = 0
        self.sporangia_germ_date = None
        self.temperature_sum = 0.0
        self.sporangia_germ_hours = 0
        self.pheno_phase = 0
        self.rain_sum_inf = 0.0


class DMCast:
    """
    DMCast model - Park EW, Seem RC, Gadoury DM, Pearson RC (1997) 
    DMCast: A prediction model for grape downy mildew development. 
    Vitic Enol Sci 52:182–139
    """
    
    def __init__(self):
        # Input lists per accumulo dati
        self.past_24_counts: List[Input] = []
        self.past_month: List[Input] = []
        self.oo_germ_count: List[Input] = []
        
        # Dictionary per dati climatici (mese -> valore)
        # IMPORTANTE: Questi vengono inizializzati vuoti e popolati dal runner
        # con i dati climatici storici reali come nel C#
        self.climatic_rainfall_sum: Dict[int, float] = {}
        self.climatic_rainy_days: Dict[int, float] = {}
        self.climatic_std_rainfall_sum: Dict[int, float] = {}
        
        # Liste per calcoli interni
        self.ra_list: List[float] = []
        self.rainy_days: List[int] = []
        self.pom_list: List[float] = []
    
    def run(self, input_data: Input, parameters: Parameters, output: Output) -> None:
        """Esegue il modello DMCast per dati orari."""
        
        # Verifica che i dati climatici siano stati inizializzati
        if not self.climatic_rainfall_sum:
            print("WARNING: DMCast climatic data not initialized! Using default values for Bergamo region.")
            self._initialize_default_climatic_data()
        
        # 1. Calcola probabilità di maturazione (Pom) - FONDAMENTALE!
        self._pom(input_data, parameters)
        
        # 2. Verifica se c'è germinazione oospore
        if self._oospore_germ(input_data, parameters, output.outputs_dmcast) == 1:
            # Crea nuovo evento di infezione
            infection_event = DMCastInfectionEvent(
                infection_date=input_data.date,
                model_name="DMCast",
                precipitation_sum=0.0,
                temperature_avg=input_data.temp,
                bbch_code=0.0,
                severity=0.0,  # Sarà aggiornato quando c'è infezione
                notes=f"DMCast oospore germination at {input_data.date}"
            )
            infection_event.germination_date = input_data.date
            infection_event.id_infection = len(output.outputs_dmcast.infection_events) + 1
            # L'infezione è inizialmente 0, diventerà 1 solo quando il ciclo è completo
            infection_event.infection = 0
            output.outputs_dmcast.infection_events.append(infection_event)
        
        # 3. Loop su tutti gli eventi di infezione esistenti
        events_to_remove = []
        for event in output.outputs_dmcast.infection_events:
            if isinstance(event, DMCastInfectionEvent):
                self._process_infection_event(event, input_data, parameters)
                
                # Rimuovi eventi incompleti alla fine dell'anno
                if (input_data.date.month == 12 and input_data.date.day == 31 and 
                    event.infection == 0):
                    events_to_remove.append(event)
        
        # Rimuovi eventi incompleti
        for event in events_to_remove:
            output.outputs_dmcast.infection_events.remove(event)
    
    def _process_infection_event(self, event: DMCastInfectionEvent, input_data: Input, 
                                parameters: Parameters) -> None:
        """Processa un singolo evento di infezione attraverso le sue fasi."""
        
        # Fase 1: Germinazione sporangi
        event.sporangia_germ_hours += 1
        
        if (event.sporangia_germ_hours >= parameters.dmcast_parameters.days_for_sporangia_germ * 24 and
            event.sporangia_germ_hours <= (parameters.dmcast_parameters.days_for_sporangia_germ + 6) * 24 and
            event.sporangia_germination == 0):
            
            event.temperature_sum += input_data.temp
            
            if input_data.date.hour == 0:  # Valutazione giornaliera
                temp_threshold = parameters.dmcast_parameters.temp_threshold_sporangia_germ * 24
                if event.temperature_sum >= temp_threshold:
                    event.sporangia_germination = 1
                    event.sporangia_germ_date = input_data.date
                    # Sporangia germination completed silently
                event.temperature_sum = 0
        
        # Fase 2: Infezione (solo dopo germinazione sporangi)
        if event.sporangia_germination == 1:
            event.infection_hours += 1
            
            if event.infection_hours <= parameters.dmcast_parameters.days_for_infection * 24:
                event.temperature_sum += input_data.temp
                event.rain_sum_splash += input_data.prec
                
                if input_data.date.hour == 0:  # Valutazione giornaliera
                    bbch = 0  # TODO: non usato nel modello attuale
                    
                    temp_threshold = parameters.dmcast_parameters.temp_threshold_inf * 24
                    prec_threshold = parameters.dmcast_parameters.prec_threshold_inf
                    
                    if (event.temperature_sum >= temp_threshold and
                        event.rain_sum_splash > prec_threshold and
                        bbch >= 0):
                        
                        event.infection = 1
                        event.infection_date = input_data.date  # Aggiorna la data di infezione alla fase finale
                        event.severity = 1.0
                        print(f"DMCast: Final infection completed on {input_data.date.strftime('%Y-%m-%d')}!")
                    
                    event.temperature_sum = 0
                    event.rain_sum_splash = 0
    
    def _ri(self, input_data: Input) -> float:
        """Calcola precipitazione giornaliera (Ri)."""
        current_date = input_data.date
        hour = input_data.date.hour
        
        # Aggiungi dati orari alla lista
        self.past_24_counts.append(input_data)
        
        ri = 0.0
        
        # Calcola alla mezzanotte
        if hour == 0:
            # Somma precipitazioni > 0.2mm nelle ultime 24 ore
            ri = sum(x.prec for x in self.past_24_counts if x.prec > 0.2)
            # Reset lista per nuovo giorno
            self.past_24_counts = []
        
        return ri
    
    def _rai(self, input_data: Input) -> float:
        """Calcola indice pluviometrico mensile (RAi)."""
        ri = self._ri(input_data)
        current_date = input_data.date
        
        # Periodo di valutazione: 21 settembre - 31 gennaio (come nel C#)
        start_date = datetime(current_date.year, 9, 21)
        end_date = datetime(current_date.year, 1, 31)  # Gennaio dell'anno corrente, non dell'anno successivo!
        
        # Aggiungi dati alla lista mensile
        self.past_month.append(input_data)
        
        ra = 0.0
        
        # Condizione corretta: periodo da settembre a gennaio dell'anno successivo
        if current_date <= end_date or current_date >= start_date:
            if current_date.hour == 0:
                # Calcola soglie climatiche
                month = current_date.month
                
                # Verifica che i dati climatici esistano
                if month in self.climatic_rainfall_sum and month in self.climatic_rainy_days:
                    hm = self.climatic_rainfall_sum[month] / self.climatic_rainy_days[month]  # soglia minima
                    hmax = ((self.climatic_rainfall_sum[month] + self.climatic_std_rainfall_sum[month]) / 
                           self.climatic_rainy_days[month])  # soglia massima
                    
                    pos = 0.0  # effetto positivo
                    lac = 0.0  # mancanza pioggia (negativo)
                    exc = 0.0  # eccesso pioggia (negativo)
                    
                    # Considera solo giorni piovosi
                    if ri > 0.2:
                        if hm < ri <= hmax:
                            pos = ri
                        elif ri <= hm:  # Corretto: <= invece di <
                            lac = hm - ri
                        elif ri > hmax:
                            exc = ri - hmax
                            pos = hmax
                    
                    # Effetto negativo netto
                    neg = abs(exc - lac)
                    
                    # Indice finale di maturazione
                    rai = pos - neg
                    self.ra_list.append(rai)
                    
                    # Reset all'inizio del nuovo periodo (21 settembre)
                    if current_date.date() == start_date.date():
                        self.ra_list = []
        
        # Calcola effetto cumulativo
        ra = sum(self.ra_list)
        return ra
    
    def _pom(self, input_data: Input, parameters: Parameters) -> float:
        """Calcola probabilità di maturazione oospore (Pom)."""
        pom = 0.0
        current_date = input_data.date
        
        # Periodo di valutazione: 31 gennaio - 22 settembre
        start_date = datetime(current_date.year, 1, 31)
        end_date = datetime(current_date.year, 9, 22)
        
        if start_date < current_date < end_date:
            if current_date.hour == 0:
                ra = self._rai(input_data)
                
                # Calcola probabilità con distribuzione gaussiana
                mu = parameters.dmcast_parameters.mu_k1 - 0.3 * ra
                sigma = parameters.dmcast_parameters.sigma_k1 + 0.02 * ra
                
                day_of_year = current_date.timetuple().tm_yday
                exponent = -((day_of_year - mu) ** 2) / (2 * (sigma ** 2))
                pom = (1 / (sigma * math.sqrt(2 * math.pi))) * math.exp(exponent)
                
                # Debug rimosso per velocità
                
                self.pom_list.append(pom)
                
                # Reset alla fine del periodo
                if current_date == end_date.replace(day=end_date.day - 1):
                    self.pom_list = []
        
        return pom
    
    def _oospore_germ(self, input_data: Input, parameters: Parameters, 
                     dmcast_output) -> int:
        """Calcola giorni di germinazione oospore."""
        oo_germ = 0
        self.oo_germ_count.append(input_data)
        
        # Calcola somma cumulativa Pom
        pom_sum = sum(self.pom_list)
        dmcast_output.pomsum = pom_sum
        
        # Periodo di valutazione: prima del 22 settembre
        end_date = datetime(input_data.date.year, 9, 22)
        
        if pom_sum >= parameters.dmcast_parameters.threshold_pom and input_data.date < end_date:
            if input_data.date.hour == 0:
                # Calcola precipitazione e temperatura giornaliera
                daily_prec = sum(x.prec for x in self.oo_germ_count if x.prec > 0.2)
                daily_temp = sum(x.temp for x in self.oo_germ_count) / len(self.oo_germ_count) if self.oo_germ_count else 0
                
                if (daily_temp > parameters.dmcast_parameters.temp_threshold_oospore_germ and
                    daily_prec > parameters.dmcast_parameters.prec_threshold_oospore_germ):
                    oo_germ = 1
                    print(f"DMCast: Oospore germination triggered on {input_data.date.strftime('%Y-%m-%d')} (POM sum: {pom_sum:.4f}, temp: {daily_temp:.1f}°C, prec: {daily_prec:.1f}mm)")
                
                # Reset contatore giornaliero
                self.oo_germ_count = []
        
        return oo_germ
    
    def reset(self) -> None:
        """Reset del modello."""
        self.past_24_counts.clear()
        self.past_month.clear()
        self.oo_germ_count.clear()
        self.ra_list.clear()
        self.rainy_days.clear()
        self.pom_list.clear()
    
    def _initialize_default_climatic_data(self):
        """Inizializza dati climatici di default per la regione di Bergamo."""
        self.climatic_rainfall_sum = {
            1: 65.0, 2: 60.0, 3: 75.0, 4: 85.0, 5: 95.0, 6: 80.0,
            7: 65.0, 8: 85.0, 9: 75.0, 10: 105.0, 11: 95.0, 12: 70.0
        }
        self.climatic_rainy_days = {
            1: 8.0, 2: 7.0, 3: 9.0, 4: 10.0, 5: 11.0, 6: 9.0,
            7: 7.0, 8: 8.0, 9: 8.0, 10: 10.0, 11: 9.0, 12: 8.0
        }
        self.climatic_std_rainfall_sum = {
            1: 25.0, 2: 23.0, 3: 28.0, 4: 32.0, 5: 35.0, 6: 30.0,
            7: 25.0, 8: 32.0, 9: 28.0, 10: 38.0, 11: 35.0, 12: 27.0
        }
    
    def set_climatic_data(self, rainfall_sum: Dict[int, float], 
                         rainy_days: Dict[int, float], 
                         std_rainfall_sum: Dict[int, float]):
        """Imposta i dati climatici calcolati dal dataset storico (come nel C#)."""
        self.climatic_rainfall_sum = rainfall_sum.copy()
        self.climatic_rainy_days = rainy_days.copy()
        self.climatic_std_rainfall_sum = std_rainfall_sum.copy()
        print(f"DMCast: Climatic data set for {len(rainfall_sum)} months")
    
    def get_current_stats(self) -> dict:
        """Ottieni statistiche correnti per debugging."""
        return {
            "pom_sum": sum(self.pom_list),
            "ra_sum": sum(self.ra_list),
            "pom_events": len(self.pom_list),
            "ra_events": len(self.ra_list),
            "climatic_data_set": bool(self.climatic_rainfall_sum)
        }
