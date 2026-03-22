import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
import xgboost as xgb
from datetime import datetime
from peronospora import paths

# Load risk levels configuration
with open(paths.PACKAGE_DIR / "risk_levels.json", 'r', encoding='utf-8') as f:
    RISK_LEVELS = json.load(f)


def get_risk_level(score: float) -> int:
    """
    Convert continuous score to discrete risk level (0-4) using range thresholds.
    
    Ranges:
        0.0 - 1.0  → Level 0 (Nessun rischio)
        1.0 - 2.0  → Level 1 (Sorveglianza)
        2.0 - 3.0  → Level 2 (Attenzione)
        3.0 - 3.5  → Level 3 (Rischio elevato)
        3.5 - 4.0  → Level 4 (Rischio molto elevato)
    """
    if score < 1.0:
        return 0
    elif score < 2.0:
        return 1
    elif score < 3.0:
        return 2
    elif score < 3.5:
        return 3
    else:
        return 4


def get_risk_label(level: int) -> str:
    """Get risk label from level."""
    return RISK_LEVELS.get(str(level), {}).get("label", "Sconosciuto")


class PeronospotaPredictor:

    def __init__(self, model_dir: str = "model", verbose: bool = True):
        self.model_dir = Path(model_dir)
        self.verbose = verbose
        self.models = {}  # {lead: model}
        self.configs = {}  # {lead: config}
        self.metrics = {}  # {lead: metrics}

    def load_model(self, lead: int, horizon: str = "near_term") -> None:
        model_name = f"{horizon}_lead_{lead}"
        model_path = self.model_dir / model_name

        if not model_path.exists():
            raise FileNotFoundError(f"Model directory not found: {model_path}")

        # Carica modello XGBoost
        model_file = model_path / "model.json"
        if not model_file.exists():
            raise FileNotFoundError(f"Model file not found: {model_file}")

        model = xgb.Booster()
        model.load_model(str(model_file))
        self.models[lead] = model

        # Carica configurazione
        config_file = model_path / "config.json"
        if not config_file.exists():
            config_file = model_path / "model_config.json"
        with open(config_file, 'r') as f:
            self.configs[lead] = json.load(f)

        # Carica metriche
        metrics_file = model_path / "metrics.json"
        with open(metrics_file, 'r') as f:
            self.metrics[lead] = json.load(f)

    def load_all_models(self, horizon: str = "near_term") -> None:
        """Carica tutti i modelli disponibili (lead 0, 1)."""
        for lead in [0, 1]:
            try:
                self.load_model(lead, horizon)
            except FileNotFoundError:
                pass

    def predict(self, data_path: str, lead: int) -> pd.DataFrame:
        if lead not in self.models:
            raise ValueError(f"Model for lead {lead} not loaded. Call load_model({lead}) first.")

        # Carica dati
        df = pd.read_csv(data_path)

        # Estrai features
        feature_cols = self.configs[lead]['features']
        feature_cols_corrected = [c if c != 'province' else 'province_cat' for c in feature_cols]

        # Check if all features are available
        missing_features = [f for f in feature_cols_corrected if f not in df.columns]
        if missing_features:
            raise ValueError(f"Missing features in data: {missing_features}")

        X = df[feature_cols_corrected].copy()

        if 'province_cat' in X.columns:
            X['province_cat'] = X['province_cat'].astype('category')

        # Crea DMatrix per XGBoost
        dmatrix = xgb.DMatrix(X, feature_names=feature_cols_corrected, enable_categorical=True)

        # Predici
        predictions = self.models[lead].predict(dmatrix)

        # Crea DataFrame risultati
        results = df[['NUTS_3', 'forecast_base', 'target_period_start',
                      'target_period_end', 'lead_weeks']].copy()

        # Risk score (continuous, clipped to 0-4)
        # Il modello predice 1-5, sottraiamo 1 per ottenere scala 0-4
        results['risk_score'] = np.clip(predictions - 1, 0, 4).round(2)

        # Risk level (discrete 1-5, rounded)
        results['risk_level'] = results['risk_score'].apply(get_risk_level)

        # Risk label from config
        results['risk_label'] = results['risk_level'].apply(get_risk_label)

        # Fenologia
        results['bbch_code'] = df['bbch_code'].round(0).astype(int)
        results['plant_susceptibility'] = df['plant_susceptibility'].round(2)

        # Meteo features per diagnostica
        results['temp'] = df['temp'].round(1)
        results['prec'] = df['prec'].round(1)
        results['rh'] = df['rh'].round(1)
        results['lw'] = df['lw'].round(0).astype(int)

        return results

    def predict_all_leads(self, data_dir: str, horizon: str = "near_term") -> Dict[int, pd.DataFrame]:
        all_predictions = {}

        for lead in self.models.keys():
            data_file = Path(data_dir) / f"lead_{lead}.csv"
            if data_file.exists():
                all_predictions[lead] = self.predict(str(data_file), lead)

        return all_predictions

    def print_summary(self, predictions: pd.DataFrame, lead: int) -> None:
        print(f"\n{'='*70}")
        print(f"PERONOSPORA RISK PREDICTION - LEAD {lead} WEEK(S)")
        print(f"{'='*70}")
        print(f"Forecast base: {predictions['forecast_base'].iloc[0]}")
        print(f"Target period: {predictions['target_period_start'].iloc[0]} to {predictions['target_period_end'].iloc[0]}")

        test_years = self.configs[lead].get('test_years', [2017])
        test_year_str = ', '.join(map(str, test_years)) if isinstance(test_years, list) else str(test_years)

        print(f"\nModel performance (test {test_year_str}):")
        print(f"  MAE: {self.metrics[lead]['test']['mae']:.3f}")
        print(f"  R²:  {self.metrics[lead]['test']['r2']:.3f}")

        # Aggregate by province
        agg = predictions.groupby('NUTS_3').agg({
            'risk_score': 'mean',
            'risk_level': 'first',
            'risk_label': 'first'
        }).reset_index()

        print(f"\nPredictions ({len(agg)} provinces):")
        print(f"  Mean risk score: {agg['risk_score'].mean():.2f}")
        print(f"  Range: [{agg['risk_score'].min():.2f}, {agg['risk_score'].max():.2f}]")

        # Risk distribution
        print(f"\nRisk distribution:")
        for level in [0, 1, 2, 3, 4]:
            count = (agg['risk_level'] == level).sum()
            if count > 0:
                label = get_risk_label(level)
                print(f"  {level} - {label}: {count}")

        print(f"{'='*70}\n")

    def save_predictions(self, predictions: pd.DataFrame, output_path: str, lead: int, 
                         save_history: bool = True) -> None:
        """Salva predizioni su file CSV e storico."""
        # Salva file corrente (sovrascrive)
        predictions.to_csv(output_path, index=False)
        
        # Salva anche nello storico con timestamp
        if save_history:
            history_dir = Path(output_path).parent / "history"
            history_dir.mkdir(parents=True, exist_ok=True)
            
            # Usa forecast_base come identificatore
            forecast_date = predictions['forecast_base'].iloc[0]
            if isinstance(forecast_date, str):
                forecast_date = pd.to_datetime(forecast_date).strftime('%Y-%m-%d')
            else:
                forecast_date = forecast_date.strftime('%Y-%m-%d')
            
            history_file = history_dir / f"{forecast_date}_lead_{lead}.csv"
            predictions.to_csv(history_file, index=False)
            
            if self.verbose:
                print(f"  📁 Saved to history: {history_file.name}")


def main():
    """Main function per inference da command line."""
    parser = argparse.ArgumentParser(
        description="Peronospora Risk Prediction Inference",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--lead', type=int, choices=[0, 1], default=1,
                        help='Lead time in weeks (0=current, 1=next week). Default: 1')
    parser.add_argument('--all', action='store_true',
                        help='Run predictions for all lead times (0, 1)')
    parser.add_argument('--data_path', type=str, default=None,
                        help='Path to inference data CSV')
    parser.add_argument('--data_dir', type=str, default=paths.INFERENCE_DIR,
                        help='Directory containing inference data files')
    parser.add_argument('--model_dir', type=str, default=paths.MODEL_DIR,
                        help='Directory containing trained models')
    parser.add_argument('--output_dir', type=str, default=paths.PREDICTIONS_DIR,
                        help='Directory for output predictions')
    parser.add_argument('--horizon', type=str, choices=['near_term', 'medium_term'],
                        default='near_term', help='Forecast horizon')
    parser.add_argument('--no_summary', action='store_true',
                        help='Suppress summary output')

    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    predictor = PeronospotaPredictor(model_dir=args.model_dir, verbose=True)

    if args.all:
        print("Loading all models...")
        predictor.load_all_models(horizon=args.horizon)

        all_predictions = predictor.predict_all_leads(args.data_dir, args.horizon)

        for lead, preds in all_predictions.items():
            output_file = os.path.join(args.output_dir, f"lead_{lead}.csv")
            predictor.save_predictions(preds, output_file, lead)

            if not args.no_summary:
                predictor.print_summary(preds, lead)
    else:
        print(f"Loading model for lead {args.lead}...")
        predictor.load_model(args.lead, args.horizon)

        if args.data_path is None:
            data_path = os.path.join(args.data_dir, f"lead_{args.lead}.csv")
        else:
            data_path = args.data_path

        predictions = predictor.predict(data_path, args.lead)

        output_file = os.path.join(args.output_dir, f"lead_{args.lead}.csv")
        predictor.save_predictions(predictions, output_file, args.lead)

        if not args.no_summary:
            predictor.print_summary(predictions, args.lead)


if __name__ == "__main__":
    main()
