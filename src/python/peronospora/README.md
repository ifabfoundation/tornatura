# Peronospora Risk Prediction - Inference Pipeline

**Version**: 2.0  
**Date**: $(date +%Y-%m-%d)

## Quick Start

```bash
# 1. Setup environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# 4. Run pipeline
python run_inference_pipeline.py
```

## Full Documentation

See **DEVELOPER_GUIDE.md** for complete technical documentation.

## Structure

```
.
├── run_inference_pipeline.py  # Main orchestrator
├── model.py                   # XGBoost inference
├── plot_risk_map.py          # Map visualization
├── scheduler.py              # Automatic scheduling
├── backfill_predictions.py   # Historical predictions
├── requirements.txt          # Python dependencies
├── DEVELOPER_GUIDE.md        # Full technical guide
├── CHANGELOG.md              # Version history
├── data/
│   ├── phenology/            # Phenology models
│   ├── weather/              # Weather data + cache
│   ├── provinces_italy.json   # Province configuration
│   └── prepare_inference_data.py
├── model/                    # Trained XGBoost models
└── predictions/              # Output predictions
```

## Support

Contact: [Your contact info]
