import sys
import os
import math
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List, Dict
from data_structures import Input, Parameters, Output, GenericInfection


class EPI:
    """
    EPI model - Strizyk S (1983). Modèle d'état potentiel d'infection: 
    application a Plasmopara viticola. Assoc. Coord. Tech. Agric. 1:46.
    """
    
    def __init__(self):
        # Input lists per accumulo dati (come nel C#)
        self.decade_counts: List[Input] = []
        self.monthly_counts: List[Input] = []
        self.ke_counts: List[Input] = []
        self.infection_count: List[Input] = []
        
        # Dictionary per dati climatici (mese -> valore)
        # Questi vengono inizializzati vuoti e popolati dal runner
        # con i dati climatici storici reali come nel C#
        self.climatic_average_temperature: Dict[int, float] = {}
        self.climatic_rainfall_sum: Dict[int, float] = {}
        self.climatic_rainy_days: Dict[int, float] = {}
        self.climatic_relative_humidity_night: Dict[int, float] = {}
        
        # Liste per cumulate Pe e Ke (come nel C#)
        self.pe_sum: List[float] = []
        self.ke_sum: List[float] = []
    
    def run(self, input_data: Input, parameters: Parameters, output: Output) -> None:
        """Esegue il modello EPI per dati orari."""
        
        # Verifica che i dati climatici siano stati inizializzati
        if not self.climatic_rainfall_sum:
            print("WARNING: EPI climatic data not initialized! Using default values.")
            self._initialize_default_climatic_data()
        
        # 1. Calcola energia potenziale (Pe) 
        pe = self._pe(input_data, parameters.epi_parameters, output.outputs_epi)
        
        # 2. Calcola energia cinetica (Ke)
        ke = self._ke(input_data, parameters.epi_parameters, output.outputs_epi)
        
        # 3. Accumula Pe e Ke
        self.pe_sum.append(pe)
        self.ke_sum.append(ke)
        
        # Calcola somme cumulative
        pes = sum(self.pe_sum)
        kes = sum(self.ke_sum)
        
        # Reset liste a ottobre (come nel C#)
        if input_data.date.month == 10:
            self.pe_sum = []
            self.ke_sum = []
        
        # Accumula dati per controllo infezioni
        self.infection_count.append(input_data)
        
        # Controllo infezioni (una volta al giorno a mezzanotte)
        if input_data.date.hour == 0:
            # Calcola indice EPI totale
            epi_index = kes + pes
            output.outputs_epi.epi = epi_index
            
            # Verifica soglia di allarme
            if (epi_index > parameters.epi_parameters.alert_threshold and 
                input_data.date.month < 10):  # Solo prima di ottobre
                
                # Calcola precipitazione e temperatura giornaliera
                daily_prec = sum(x.prec for x in self.infection_count if x.prec > 0.2)
                daily_temp = sum(x.temp for x in self.infection_count) / len(self.infection_count) if self.infection_count else 0
                
                # TODO: BBCH non usato nel modello attuale
                bbch_phase = 0
                
                # Verifica condizioni per infezione
                if (daily_temp > parameters.epi_parameters.temp_threshold_inf and
                    daily_prec > parameters.epi_parameters.prec_threshold_inf and
                    bbch_phase >= 0):
                    
                    # Crea evento di infezione
                    infection_event = GenericInfection(
                        infection_date=input_data.date,
                        model_name="EPI",
                        precipitation_sum=daily_prec,
                        temperature_avg=daily_temp,
                        bbch_code=bbch_phase,
                        severity=1.0,
                        notes=f"EPI infection: index={epi_index:.3f}, temp={daily_temp:.1f}°C, prec={daily_prec:.1f}mm"
                    )
                    output.outputs_epi.infection_events.append(infection_event)
                    print(f"EPI: Infection detected on {input_data.date.strftime('%Y-%m-%d')} (EPI index: {epi_index:.3f})")
                
                # Reset contatore giornaliero (come nel C# - SEMPRE quando soglia superata)
                self.infection_count = []
    
    def _ke(self, input_data: Input, epi_parameters, outputs_epi) -> float:
        """Calcola energia cinetica (Ke)."""
        ke = 0.0
        
        # Ke si calcola solo da aprile a settembre
        if 4 <= input_data.date.month <= 9:
            hour = input_data.date.hour
            
            # Aggiungi dati orari alla lista
            self.ke_counts.append(input_data)
            
            # Calcola una volta al giorno a mezzanotte (se abbiamo almeno 23 ore)
            if hour == 0 and len(self.ke_counts) >= 23:
                # Calcola umidità relativa diurna (ore 9-18)
                rh_day_values = [x.rh for x in self.ke_counts if 9 <= x.date.hour <= 18]
                rh_day = sum(rh_day_values) / len(rh_day_values) if rh_day_values else 0
                
                # Calcola temperatura media giornaliera
                temp_avg = sum(x.temp for x in self.ke_counts) / len(self.ke_counts)
                
                # Le radici quadrate non gestiscono valori negativi
                if temp_avg < 0:
                    temp_avg = 0
                
                # Calcola Um (umidità combinata)
                month = input_data.date.month
                if month in self.climatic_relative_humidity_night:
                    climatic_rh_night = self.climatic_relative_humidity_night[month]
                    um = (5 * climatic_rh_night + 3 * rh_day) / 8
                    
                    # Verifica range Um (come nel C#)
                    if um <= epi_parameters.ur_lower_threshold or um >= epi_parameters.ur_upper_threshold:
                        um = 0
                    
                    # Calcola energia cinetica
                    if month in self.climatic_average_temperature:
                        climatic_temp = self.climatic_average_temperature[month]
                        ke = epi_parameters.ke_constant * (
                            (um**2 * math.sqrt(temp_avg) - rh_day**2 * math.sqrt(climatic_temp)) / 100
                        )
                
                # Reset lista per nuovo giorno
                self.ke_counts = []
        
        # Aggiorna output
        outputs_epi.ke = ke
        return ke
    
    def _ct(self, month: int) -> float:
        """Calcola costante mensile per Pe."""
        # Costanti mensili come nel C#
        ct_values = {
            10: 1.2,
            11: 1.2,
            12: 1.0,
            1: 0.8,
            2: 0.8,
            3: 0.8
        }
        return ct_values.get(month, 0.0)
    
    def _pe(self, input_data: Input, epi_parameters, outputs_epi) -> float:
        """Calcola energia potenziale (Pe)."""
        pe = 0.0
        current_date = input_data.date
        
        # Pe si calcola tra 1 ottobre e 31 marzo (come nel C#)
        if current_date.month >= 9 or current_date.month <= 3:
            # Aggiungi dati alle liste di accumulo
            self.decade_counts.append(input_data)
            self.monthly_counts.append(input_data)
            
            # Calcola costante mensile
            ct = self._ct(current_date.month)
            
            # Calcola precipitazioni e temperature mensili su finestra mobile di 30 giorni
            tm = 0.0
            rm = 0.0
            if len(self.monthly_counts) == 30 * 24:  # 30 giorni * 24 ore
                # Rimuovi il primo elemento per mantenere finestra di 30 giorni
                self.monthly_counts.pop(0)
                
                # Calcola precipitazione mensile totale
                rm = sum(x.prec for x in self.monthly_counts)
                
                # Calcola temperatura media mensile
                tm = sum(x.temp for x in self.monthly_counts) / len(self.monthly_counts)
                
                # Le radici quadrate non gestiscono valori negativi
                if tm < 0:
                    tm = 0
            
            # Calcola Pe solo nel periodo ottobre-marzo
            if current_date.month >= 10 or current_date.month <= 3:
                # Ogni 10 giorni (240 ore = 10 giorni * 24 ore)
                if len(self.decade_counts) == 240:
                    # Calcola precipitazione nella decade
                    rd = sum(x.prec for x in self.decade_counts if x.prec > 0.2)
                    
                    # Conta giorni piovosi (come nel C#)
                    rainy_days = 0
                    i = 0
                    while i < 240:
                        if self.decade_counts[i].prec > 0.2:
                            rainy_days += 1
                            hour = 24 - self.decade_counts[i].date.hour
                            i += hour
                        else:
                            i += 1
                    
                    rdd = float(rainy_days)
                    
                    # Calcola energia negativa (EN)
                    en = 0.0
                    if rdd > 0:
                        k = rd / rdd
                        month = input_data.date.month
                        
                        if (month in self.climatic_rainy_days and 
                            k >= 135 / self.climatic_rainy_days[month]):
                            a = self.climatic_rainy_days[month] * 1.5 / 18
                            en = a * math.log(k)
                    
                    # Calcola energia potenziale base (pe)
                    month = input_data.date.month
                    if month in self.climatic_rainfall_sum:
                        pe_base = 2 * ct * (math.sqrt(rm) - math.sqrt(self.climatic_rainfall_sum[month] * 0.95))
                    else:
                        pe_base = 0
                    
                    # Calcola energia positiva (EP)
                    ep = 0.0
                    if (month in self.climatic_average_temperature and 
                        month in self.climatic_rainfall_sum):
                        
                        climatic_temp = self.climatic_average_temperature[month]
                        climatic_rain = self.climatic_rainfall_sum[month]
                        
                        if climatic_temp >= 0:
                            ep = epi_parameters.pe_constant * ct * (
                                math.sqrt(rm) * math.sqrt(tm) - 
                                math.sqrt(climatic_rain * 0.95) * math.sqrt(climatic_temp * 0.95)
                            )
                        else:
                            ep = epi_parameters.pe_constant * ct * (
                                math.sqrt(rm) * math.sqrt(tm) - 
                                math.sqrt(climatic_rain * 0.95) * 0
                            )
                    
                    # Calcola Pe finale
                    pe = pe_base + ep - en
                    
                    # Reset lista decade
                    self.decade_counts = []
        
        # Aggiorna output
        outputs_epi.pe = pe
        return pe
    
    def _initialize_default_climatic_data(self):
        """Inizializza dati climatici di default per la regione di Bergamo."""
        # Valori di default ragionevoli per l'Italia del Nord
        self.climatic_average_temperature = {
            1: 2.0, 2: 4.0, 3: 9.0, 4: 13.0, 5: 18.0, 6: 22.0,
            7: 25.0, 8: 24.0, 9: 20.0, 10: 14.0, 11: 8.0, 12: 3.0
        }
        self.climatic_rainfall_sum = {
            1: 65.0, 2: 60.0, 3: 75.0, 4: 85.0, 5: 95.0, 6: 80.0,
            7: 65.0, 8: 85.0, 9: 75.0, 10: 105.0, 11: 95.0, 12: 70.0
        }
        self.climatic_rainy_days = {
            1: 8.0, 2: 7.0, 3: 9.0, 4: 10.0, 5: 11.0, 6: 9.0,
            7: 7.0, 8: 8.0, 9: 8.0, 10: 10.0, 11: 9.0, 12: 8.0
        }
        self.climatic_relative_humidity_night = {
            1: 85.0, 2: 82.0, 3: 80.0, 4: 78.0, 5: 75.0, 6: 72.0,
            7: 70.0, 8: 72.0, 9: 75.0, 10: 80.0, 11: 83.0, 12: 86.0
        }
    
    def set_climatic_data(self, avg_temperature: Dict[int, float], 
                         rainfall_sum: Dict[int, float],
                         rainy_days: Dict[int, float],
                         rh_night: Dict[int, float]):
        """Imposta i dati climatici calcolati dal dataset storico (come nel C#)."""
        self.climatic_average_temperature = avg_temperature.copy()
        self.climatic_rainfall_sum = rainfall_sum.copy()
        self.climatic_rainy_days = rainy_days.copy()
        self.climatic_relative_humidity_night = rh_night.copy()
        print(f"EPI: Climatic data set for {len(rainfall_sum)} months")
    
    def reset(self) -> None:
        """Reset del modello."""
        self.decade_counts.clear()
        self.monthly_counts.clear()
        self.ke_counts.clear()
        self.infection_count.clear()
        self.pe_sum.clear()
        self.ke_sum.clear()
    
    def get_current_stats(self) -> dict:
        """Ottieni statistiche correnti per debugging."""
        return {
            "pe_sum": sum(self.pe_sum),
            "ke_sum": sum(self.ke_sum),
            "epi_index": sum(self.pe_sum) + sum(self.ke_sum),
            "pe_events": len(self.pe_sum),
            "ke_events": len(self.ke_sum),
            "climatic_data_set": bool(self.climatic_rainfall_sum)
        }
