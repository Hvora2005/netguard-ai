# NetGuard AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AI-based network traffic classification & threat-detection platform. Upload traffic datasets, preprocess them without data leakage, train and compare multiple ML models, run live predictions with explainability, analyze PCAP files, investigate flows, review security alerts, and generate reports.

**Status: all 6 phases implemented** (project scaffolding · dataset ingestion & preprocessing · model training/evaluation/experiment tracking · live prediction & explainability · PCAP analysis/traffic explorer/alerts · reports & tests). See `ARCHITECTURE.md`, `API.md`, and `ML_PIPELINE.md` for deeper detail on each layer.

No Docker is used or required anywhere in this project.

## Tech stack

- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Lucide icons
- **Backend:** Python, FastAPI, Pydantic, SQLAlchemy, Uvicorn
- **ML:** scikit-learn, XGBoost, joblib, (optional) SHAP
- **Network processing:** Scapy (PCAP parsing)
- **Reports:** reportlab (PDF), built-in HTML/CSV export
- **Database:** SQLite by default (a local file, created automatically)

## Prerequisites

- Python 3.11–3.13
- Node.js 20+ and npm
- No database server, no Docker, no paid APIs, no Npcap/WinPcap required (those are only needed for *live* packet capture, not for reading uploaded `.pcap` files)

## Quick start

### Windows (PowerShell)

```powershell
.\setup.ps1     # one-time: creates venv, installs backend + frontend deps
.\run.ps1       # starts backend (http://localhost:8000) and frontend (http://localhost:5173)
```

### macOS / Linux

```bash
chmod +x setup.sh run.sh
./setup.sh
./run.sh
```

Then open **http://localhost:5173**. Click **"Load demo (synthetic)"** in Dataset Explorer to try the full pipeline immediately without downloading a real dataset.

## Manual setup (if you prefer not to use the scripts)

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Windows
# source .venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
copy .env.example .env            # Windows: Copy-Item .env.example .env
uvicorn app.main:app --reload
```

The API is at `http://localhost:8000`, with interactive OpenAPI docs at `http://localhost:8000/docs`. The SQLite database, `models_storage/`, `uploads/`, and `reports/` directories are created automatically on first startup.

### Frontend

```powershell
cd frontend
npm install
copy .env.example .env
npm run dev
```

## Walking through the whole pipeline

1. **Dataset Explorer** → "Load demo (synthetic)" (or upload your own CIC-IDS-style CSV) → confirm the target column.
2. **Preprocessing** → pick a dataset, configure imputation/scaling/encoding/imbalance handling, preview before/after stats.
3. **Model Training** → pick a model type, train it (preprocessing is fit only on the training split).
4. **Model Comparison** → compare completed experiments; activate the model you want to use elsewhere.
5. **Live Prediction** → enter flow features by hand against the active/any model; see the prediction, confidence, and contributing features.
6. **Explainability** → view a model's global feature importance (SHAP for tree models when installed, otherwise feature importance/coefficients).
7. **PCAP Analyzer** → upload a `.pcap`/`.pcapng` capture; flows are extracted, classified with a chosen model, and written to Traffic Explorer + Security Alerts.
8. **Traffic Explorer** → filter/paginate classified flows; click one to open **Flow Investigation** (network info, stats, classification, explanation).
9. **Security Alerts** → review alerts generated from non-benign predictions, acknowledge/resolve them.
10. **Reports** → generate an HTML/CSV/PDF report for a completed experiment (metrics, feature importance, traffic stats, alerts, conclusions) and download it.

## Optional: real SHAP explainability

`requirements.txt` deliberately excludes `shap`, because on Windows it often needs **Microsoft C++ Build Tools** to compile from source, which would break the "clone and run, no issues" goal for anyone without them already installed. If you want real SHAP explanations (currently used for tree-based models: Random Forest, Decision Tree, XGBoost) instead of the feature-importance fallback:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-explainability.txt
```

If that install fails on your machine, the app will simply keep using the feature-importance/coefficient fallback — nothing else breaks.

## Using a real network-traffic dataset

Any CIC-IDS-style CSV works: a table of flow features plus a label column (commonly named `Label`, `Class`, or `Attack_cat`). Upload it in Dataset Explorer — the app auto-detects a likely target column, computes column/class statistics, and lets you confirm or change the target column before training.

Public datasets you can download separately and import this way include CIC-IDS2017, CIC-IDS2018, and NSL-KDD. This project does not bundle or download them for you.

PCAP-derived flow features are mapped onto whichever feature names your trained model expects, using CIC-IDS-style column names (`Destination Port`, `Flow Duration`, `Flow Bytes/s`, etc. — see `backend/app/network/feature_mapping.py`). If your model was trained on a dataset with very different column names, PCAP classification for that model will fall back to mostly-imputed values; see `ML_PIPELINE.md` for the exact mapping and its limitations.

## Demo / synthetic dataset

Dataset Explorer's "Load demo" button (and `scripts/generate_demo_dataset.py`) generates a small dataset with plausible flow statistics for five clearly-labeled synthetic classes (`BENIGN`, `DoS`, `PortScan`, `DDoS`, `BruteForce`). It exists purely so you can exercise the whole pipeline immediately. Every dataset created this way is flagged `is_demo: true` in the database and shown with a **DEMO** badge in the UI — it does not represent measurements of real attacks, and the app never claims otherwise.

## Project structure

```
netguard-ai/
├── backend/
│   ├── app/
│   │   ├── api/routes/        # FastAPI endpoints
│   │   ├── core/               # settings/config, severity rules
│   │   ├── database/           # SQLAlchemy engine/session/base
│   │   ├── ml/                 # model factory, trainer, evaluation, explainability, predictor, registry
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── network/             # PCAP parsing (Scapy), raw-flow -> model-feature mapping
│   │   ├── preprocessing/       # inspection + preprocessing pipeline builders
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/            # business logic used by routes
│   │   └── main.py
│   ├── models_storage/          # trained model bundles (joblib)
│   ├── uploads/                 # uploaded CSVs and PCAPs
│   ├── reports/                 # generated reports (HTML/CSV/PDF)
│   └── tests/                   # pytest suite
├── frontend/
│   └── src/{components,pages,layouts,hooks,services,types}
├── data/                        # generated demo CSV lands here if you use the CLI script
├── scripts/generate_demo_dataset.py
├── ARCHITECTURE.md / API.md / ML_PIPELINE.md
└── setup.ps1 / setup.sh / run.ps1 / run.sh
```

## API overview

- `GET /api/health`
- `POST /api/datasets/upload`, `POST /api/datasets/demo`, `GET /api/datasets`, `GET /api/datasets/{id}`, `GET /api/datasets/{id}/preview`, `PUT /api/datasets/{id}/target-column`, `DELETE /api/datasets/{id}`
- `POST /api/preprocessing/preview`
- `POST /api/models/train`, `GET /api/models`, `GET /api/models/{id}`, `PUT /api/models/{id}/rename`, `PUT /api/models/{id}/activate`, `DELETE /api/models/{id}`
- `GET /api/experiments`, `GET /api/experiments/{id}`
- `GET /api/models/{id}/feature-schema`, `GET /api/models/{id}/explain/global`, `POST /api/predict`
- `POST /api/pcap/analyze`
- `GET /api/traffic`, `GET /api/traffic/{id}`
- `GET /api/alerts`, `PUT /api/alerts/{id}/status`
- `POST /api/reports/generate`, `GET /api/reports`, `GET /api/reports/{id}/download`

Full interactive documentation for every endpoint (including request/response schemas) is generated automatically at `/docs`. See `API.md` for a narrative walkthrough.

## Avoiding data leakage

Preprocessing (imputation, scaling, encoding) is fit **only on the training split** during `POST /api/models/train`, then applied to both splits and saved as part of the model bundle so prediction/PCAP classification reuse the exact same fitted transform. The `/api/preprocessing/preview` endpoint fits on the whole dataset instead, but purely to show illustrative before/after statistics — that fitted instance is discarded and never reused for actual training. See `ML_PIPELINE.md`, `backend/app/preprocessing/pipeline.py`, and `backend/app/ml/trainer.py` for the exact flow.

## Running the tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -v
```

Tests run against an isolated temporary SQLite database and storage directories (see `backend/tests/conftest.py`) — they never touch your real `netguard.db`, `uploads/`, `models_storage/`, or `reports/`.

## Troubleshooting

- **`git` not recognized:** this repo doesn't require git to run locally; install Git for Windows separately if you want version control.
- **SHAP fails to install:** expected without C++ Build Tools — see "Optional: real SHAP explainability" above; the rest of the app is unaffected.
- **"No libpcap provider available" warning on startup:** harmless — it only means *live* packet capture isn't available; reading uploaded `.pcap`/`.pcapng` files works regardless.
- **PCAP upload fails to parse:** confirm the file is a valid `.pcap`/`.pcapng` capture; corrupt files return a clear error instead of a fake result.
- **Port already in use:** change `--port` on the `uvicorn` command, or the `server.port` in `frontend/vite.config.ts`, and update `VITE_API_BASE_URL`/`CORS_ORIGINS` to match.
- **Frontend can't reach backend:** confirm the backend is running on port 8000 and `frontend/.env`'s `VITE_API_BASE_URL` matches.

## Future extensions (not implemented — architecture leaves room for them)

Real-time interface monitoring/streaming classification, Kafka/Redis/Celery-based async pipelines, advanced anomaly detection, model drift detection, federated learning, cloud deployment, deeper deep-learning models (1D CNN/LSTM) if the data genuinely supports sequential learning.
