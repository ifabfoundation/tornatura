import logging
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from peronospora.data import prepare_inference_data
from peronospora.model import PeronospotaPredictor
from peronospora import plot_risk_map
from peronospora import paths


logger = logging.getLogger("peronospora_inference")

DATA_DIR = paths.INFERENCE_DIR
MODEL_DIR = paths.MODEL_DIR
PREDICTIONS_DIR = paths.PREDICTIONS_DIR
RISK_MAP_PATH = paths.RISK_MAP_PATH


def run_inference_pipeline(
    *,
    skip_data_prep: bool = False,
    no_map: bool = False,
    lead: Optional[int] = None,
    clear_cache: bool = False,
) -> Dict[str, Optional[str]]:
    """Run the inference pipeline end-to-end using in-process calls."""
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)

    if not skip_data_prep:
        logger.info("Preparing inference data")
        exit_code = prepare_inference_data.run_pipeline(clear_cache_flag=clear_cache)
        if exit_code != 0:
            raise RuntimeError(f"Data preparation failed with exit code {exit_code}")

    predictor = PeronospotaPredictor(model_dir=str(MODEL_DIR), verbose=False)

    if lead is None:
        predictor.load_all_models(horizon="near_term")
        if not predictor.models:
            raise RuntimeError("No models loaded. Check model directory contents.")

        predictions = predictor.predict_all_leads(str(DATA_DIR), "near_term")
        if not predictions:
            raise RuntimeError("No predictions generated. Check inference data inputs.")

        for lead_id, preds in predictions.items():
            output_file = PREDICTIONS_DIR / f"lead_{lead_id}.csv"
            predictor.save_predictions(preds, str(output_file), lead_id)
    else:
        predictor.load_model(lead, "near_term")
        data_path = DATA_DIR / f"lead_{lead}.csv"
        if not data_path.exists():
            raise FileNotFoundError(f"Inference data not found: {data_path}")

        predictions = predictor.predict(str(data_path), lead)
        output_file = PREDICTIONS_DIR / f"lead_{lead}.csv"
        predictor.save_predictions(predictions, str(output_file), lead)

    map_path: Optional[str] = None
    if not no_map:
        logger.info("Generating risk map")
        all_predictions = plot_risk_map.load_all_predictions(str(PREDICTIONS_DIR))
        if not all_predictions:
            raise RuntimeError("Risk map generation failed: no predictions found.")

        gdf = plot_risk_map.load_emilia_romagna_shapefile()
        plot_risk_map.create_satellite_map_all_weeks(
            all_predictions,
            gdf,
            output_file=str(RISK_MAP_PATH),
        )
        map_path = str(RISK_MAP_PATH)

    return {
        "predictions_dir": str(PREDICTIONS_DIR),
        "map_path": map_path,
    }


def read_predictions(lead: int, limit: Optional[int] = None) -> pd.DataFrame:
    """Load prediction CSV for a specific lead."""
    if lead not in (0, 1):
        raise ValueError("Lead must be 0 or 1.")

    data_path = PREDICTIONS_DIR / f"lead_{lead}.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Predictions not found: {data_path}")

    df = pd.read_csv(data_path)
    if limit is not None and limit > 0:
        return df.head(limit)
    return df
