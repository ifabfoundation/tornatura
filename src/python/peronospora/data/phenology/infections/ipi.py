import sys
import os
import math
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from typing import List
from data_structures import Input, Parameters, Output, GenericInfection


class IPI:
    """
    IPI model - Gherardi I (2001). Modello a prognosi negativa per le infezioni primarie 
    di Plasmopara viticola. Inf Agrar 57:83-86.
    """
    
    def __init__(self):
        # Input lists per accumulo dati (come nel C#)
        self.ri_counts: List[Input] = []
        self.tmini_counts: List[Input] = []
        self.tmeani_counts: List[Input] = []
        self.lwi_counts: List[Input] = []
        self.rhi_counts: List[Input] = []
        self.ipi_counts: List[Input] = []
        self.infection_count: List[Input] = []
        
        # Lista per accumulo IPI (come nel C#)
        self.ipi_sum: List[float] = []
    
    def run(self, input_data: Input, parameters: Parameters, output: Output) -> None:
        """Esegue il modello IPI per dati orari."""
        
        # 1. Calcola indice IPI giornaliero
        ipi_index = self._ipi_index(input_data, parameters.ipi_parameters)
        
        # 2. Accumula dati per controllo infezioni
        self.infection_count.append(input_data)
        
        # 3. Controllo a mezzanotte (come nel C#)
        if input_data.date.hour == 0:
            # Accumula IPI giornaliero
            self.ipi_sum.append(ipi_index)
            sum_ipi = sum(self.ipi_sum)
            
            # Aggiorna output con somma cumulativa
            output.outputs_ipi.ipisum = sum_ipi
            
            # Reset somma IPI alla fine dell'anno (come nel C#)
            last_day_of_year = datetime(input_data.date.year, 12, 31)
            if input_data.date.date() == last_day_of_year.date():
                self.ipi_sum = []
            
            # Verifica condizioni di infezione
            if sum_ipi >= parameters.ipi_parameters.alert_threshold:
                # Calcola precipitazione e temperatura giornaliera
                daily_prec = sum(x.prec for x in self.infection_count if x.prec > 0.2)
                daily_temp = sum(x.temp for x in self.infection_count) / len(self.infection_count) if self.infection_count else 0
                
                # TODO: BBCH non usato nel modello attuale
                bbch_phase = 0
                
                # Verifica condizioni per infezione
                if (daily_temp > parameters.ipi_parameters.temp_threshold_inf and
                    daily_prec > parameters.ipi_parameters.prec_threshold_inf and
                    bbch_phase >= parameters.ipi_parameters.bbch_threshold):
                    
                    # Crea evento di infezione
                    infection_event = GenericInfection(
                        infection_date=input_data.date,
                        model_name="IPI",
                        precipitation_sum=daily_prec,
                        temperature_avg=daily_temp,
                        bbch_code=bbch_phase,
                        severity=1.0,
                        notes=f"IPI infection: sum={sum_ipi:.3f}, temp={daily_temp:.1f}°C, prec={daily_prec:.1f}mm"
                    )
                    output.outputs_ipi.infection_events.append(infection_event)
                    print(f"IPI: Infection detected on {input_data.date.strftime('%Y-%m-%d')} (IPI sum: {sum_ipi:.3f})")
                
                # Reset contatore giornaliero (come nel C#)
                self.infection_count = []
    
    def _ri(self, input_data: Input, ipi_parameters) -> float:
        """Calcola indice di precipitazione (Ri)."""
        ri = 0.0
        
        # Aggiungi dati orari alla lista
        self.ri_counts.append(input_data)
        
        # Mantieni finestra mobile di 48 ore
        if len(self.ri_counts) == 48:
            self.ri_counts.pop(0)
        
        # Calcola una volta al giorno a mezzanotte
        if input_data.date.hour == 0:
            # Somma precipitazioni delle ultime 48 ore
            precipitation = sum(x.prec for x in self.ri_counts)
            
            # Formula dal C#: Ri = 0.00667 + 0.194405 * Precipitation + 0.0002239 * Precipitation^2
            ri = 0.00667 + 0.194405 * precipitation + 0.0002239 * (precipitation ** 2)
            
            # Applica limiti
            if ri < 0:
                ri = 0
            if ri > ipi_parameters.ri_upper_threshold:
                ri = ipi_parameters.ri_upper_threshold
        
        return ri
    
    def _tmini(self, input_data: Input) -> float:
        """Calcola indice di temperatura minima (Tmini) - non usato nel calcolo finale ma incluso nel C#."""
        tmini = 0.0
        
        # Aggiungi dati orari alla lista
        self.tmini_counts.append(input_data)
        
        # Calcola una volta al giorno a mezzanotte
        if input_data.date.hour == 0:
            # Temperatura minima giornaliera
            tmin = min(x.temp for x in self.tmini_counts)
            
            # Formula dal C#: Tmini = 0.047272 - 0.082915 * Tmin + 0.010239 * Tmin^2
            tmini = 0.047272 - 0.082915 * tmin + 0.010239 * (tmin ** 2)
            
            # Applica limiti
            if tmini < 0:
                tmini = 0
            if tmini > 1:
                tmini = 1
            
            # Reset lista giornaliera
            self.tmini_counts = []
        
        return tmini
    
    def _tmeani(self, input_data: Input, ipi_parameters) -> float:
        """Calcola indice di temperatura media (Tmeani)."""
        tmeani = 0.0
        
        # Aggiungi dati orari alla lista
        self.tmeani_counts.append(input_data)
        
        # Calcola una volta al giorno a mezzanotte
        if input_data.date.hour == 0:
            # Temperatura minima e media giornaliera
            tmin = min(x.temp for x in self.tmeani_counts)
            tmean = sum(x.temp for x in self.tmeani_counts) / len(self.tmeani_counts)
            
            # Calcola correzione temperatura minima
            if tmin > ipi_parameters.tmeani_tmin_threshold:
                tmin_corr = 1.0
            else:
                tmin_corr = 0.35 + 0.05 * tmin
            
            # Formula dal C#: Tmeani = (-2.19247 + 0.259906 * Tmean - 0.000139 * Tmean^3 - 6.095832 * 10^-6 * Tmean^4) * Tmin_corr
            tmeani = (-2.19247 + 0.259906 * tmean - 0.000139 * (tmean ** 3) - 6.095832e-6 * (tmean ** 4)) * tmin_corr
            
            # Applica limiti
            if tmeani < 0:
                tmeani = 0
            if tmeani > ipi_parameters.tmeani_upper_threshold:
                tmeani = 1.0
            
            # Reset lista giornaliera
            self.tmeani_counts = []
        
        return tmeani
    
    def _lwi(self, input_data: Input, ipi_parameters) -> float:
        """Calcola indice di bagnatura fogliare (Lwi)."""
        lwi = 0.0
        
        # Aggiungi dati orari alla lista
        self.lwi_counts.append(input_data)
        
        # Calcola una volta al giorno a mezzanotte
        if input_data.date.hour == 0:
            # Bagnatura fogliare e precipitazione giornaliera
            lw = sum(x.lw for x in self.lwi_counts)
            daily_rain = sum(x.prec for x in self.lwi_counts)
            
            # Formula dal C#: Lwi = 0.004 * Lw^2 + 0.008 * Lw - 0.01
            lwi = 0.004 * (lw ** 2) + 0.008 * lw - 0.01
            
            # Applica condizioni
            if lwi > ipi_parameters.lwi_lower_threshold:
                lwi = 1.0
            
            if daily_rain <= 0.2 and lw <= ipi_parameters.lwi_upper_threshold:
                lwi = 0.0
            
            # Reset lista giornaliera
            self.lwi_counts = []
        
        return lwi
    
    def _rhi(self, input_data: Input, ipi_parameters) -> float:
        """Calcola indice di umidità relativa (Rhi)."""
        rhi = 0.0
        
        # Aggiungi dati orari alla lista
        self.rhi_counts.append(input_data)
        
        # Calcola una volta al giorno a mezzanotte
        if input_data.date.hour == 0:
            # Umidità relativa media giornaliera
            ur_mean = sum(x.rh for x in self.rhi_counts) / len(self.rhi_counts)
            
            # Formula dal C#: Rhi = (-69.994545 + 1.502 * URmean - 0.007818 * URmean^2) / 2
            rhi = (-69.994545 + 1.502 * ur_mean - 0.007818 * (ur_mean ** 2)) / 2
            
            # Applica limiti
            if rhi < 0:
                rhi = 0
            if rhi > ipi_parameters.rhi_upper_threshold:
                rhi = 1.0
            
            # Reset lista giornaliera
            self.rhi_counts = []
        
        return rhi
    
    def _ipi_index(self, input_data: Input, ipi_parameters) -> float:
        """Calcola indice IPI giornaliero."""
        ipi_index = 0.0
        
        # Aggiungi dati orari alla lista
        self.ipi_counts.append(input_data)
        
        # Calcola una volta al giorno a mezzanotte
        if input_data.date.hour == 0:
            # Precipitazione giornaliera
            daily_rain = sum(x.prec for x in self.ipi_counts)
            
            # Calcola componenti intermedie
            ri = self._ri(input_data, ipi_parameters)
            lwi = self._lwi(input_data, ipi_parameters)
            tmeani = self._tmeani(input_data, ipi_parameters)
            rhi = self._rhi(input_data, ipi_parameters)
            
            # Passi intermedi dal C#
            ipi_lw_ri = ri + lwi
            
            if daily_rain == 0:
                ipi_lwri_tmean = 0.0
            else:
                ipi_lwri_tmean = ipi_lw_ri * tmeani
            
            if daily_rain == 0:
                ipi_tmean_ri = 0.0
            else:
                ipi_tmean_ri = tmeani * ri
            
            # Temperatura minima giornaliera
            tmin = min(x.temp for x in self.ipi_counts)
            
            # Calcolo IPI finale
            ipi_tmean_rhi = tmeani * rhi
            
            if tmin > ipi_parameters.ipi_tmin_threshold:
                if ipi_lwri_tmean > ipi_tmean_rhi:
                    ipi_index = ipi_lwri_tmean
                else:
                    ipi_index = ipi_tmean_rhi
            
            # Reset lista giornaliera
            self.ipi_counts = []
        
        return ipi_index
    
    def reset(self) -> None:
        """Reset del modello."""
        self.ri_counts.clear()
        self.tmini_counts.clear()
        self.tmeani_counts.clear()
        self.lwi_counts.clear()
        self.rhi_counts.clear()
        self.ipi_counts.clear()
        self.infection_count.clear()
        self.ipi_sum.clear()
    
    def get_current_stats(self) -> dict:
        """Ottieni statistiche correnti per debugging."""
        return {
            "ipi_sum": sum(self.ipi_sum),
            "ipi_events": len(self.ipi_sum),
            "total_infections": len(self.infection_count)
        }
