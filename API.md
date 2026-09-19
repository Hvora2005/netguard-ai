# API Reference

Base URL: `http://localhost:8000/api`. Full auto-generated schemas for every endpoint (request/response models, enums, examples) are available at `http://localhost:8000/docs` (Swagger UI) or `/redoc`. This document is a narrative companion, not a replacement.

All errors return `{"detail": "human-readable message"}` with an appropriate status code (400 for bad input, 404 for missing resources, 500 for unexpected server errors) — no Python stack traces are ever returned to the client (see `app/main.py`'s exception handlers).

## Health

- `GET /health` → `{"status": "ok", "service": "NetGuard AI backend"}`

## Datasets

- `POST /datasets/upload` (multipart `file`, `.csv` only) → registers the dataset, auto-detects a likely target column, computes column/class statistics. 400 if not CSV, empty, or unparsable.
- `POST /datasets/demo` → generates and registers the synthetic demo dataset (`is_demo: true`).
- `GET /datasets` → list of dataset summaries.
- `GET /datasets/{id}` → full detail (column metadata, class distribution, missing values, duplicate count).
- `GET /datasets/{id}/preview` → first ~50 rows as `{columns, rows}`.
- `PUT /datasets/{id}/target-column` (`{"target_column": "Label"}`) → changes the target column and recomputes class distribution.
- `DELETE /datasets/{id}`

## Preprocessing

- `POST /preprocessing/preview` (`{dataset_id, config}`) → fits preprocessing on the **whole** dataset purely for an illustrative before/after comparison (row counts, class distribution, numeric stats, notes). This fitted instance is discarded; it is never reused for actual training.

`config` (`PreprocessingConfig`): `feature_columns` (null = all non-target columns), `missing_strategy` (`mean|median|most_frequent|drop_rows`), `scaling` (`standard|minmax|none`), `categorical_encoding` (`onehot|label`), `handle_imbalance` (`none|smote|class_weight`), `test_size` (0.1–0.5), `task_type` (`binary|multiclass`), `benign_labels` (list of raw label values collapsed to `BENIGN` when `task_type=binary`), `random_state`.

## Models & training

- `POST /models/train` (`TrainRequest`: `dataset_id, model_type, model_name?, hyperparameters, preprocessing`) → runs the full leakage-safe train/evaluate pipeline synchronously, saves the model bundle, and returns the completed (or failed) `Experiment`.

  `model_type` ∈ `logistic_regression | decision_tree | random_forest | svm | knn | xgboost | mlp`.

- `GET /models`, `GET /models/{id}` → saved model registry entries.
- `PUT /models/{id}/rename` (`{"name": "..."}`)
- `PUT /models/{id}/activate` → marks this model active (unsets any other active model); `/api/predict` and `/api/pcap/analyze` use the active model when no `model_id` is given.
- `DELETE /models/{id}` → removes the DB row and the bundle file on disk.

- `GET /experiments`, `GET /experiments/{id}` → full experiment history including `metrics` (accuracy, macro/weighted F1, per-class precision/recall/F1/support, confusion matrix, ROC-AUC, PR-AUC where computable).

## Prediction & explainability

- `GET /models/{id}/feature-schema` → `{model_id, model_name, task_type, class_labels, fields: [{name, is_numeric}]}` — drives the Live Prediction form dynamically.
- `POST /predict` (`{model_id?, features: {...}}`, `model_id` omitted → uses the active model) → `{predicted_class, confidence, probabilities, explanation, explanation_method}`. `confidence`/`probabilities` are the model's own `predict_proba` output, never invented; `explanation_method` documents which method actually produced `explanation` (see `ML_PIPELINE.md`).
- `GET /models/{id}/explain/global` → `{method, importances: [{feature, importance}]}` — the model's global feature importance/coefficients (or `unavailable` if the model type exposes neither and SHAP isn't installed).

## PCAP analysis

- `POST /pcap/analyze` (multipart `file` [.pcap/.pcapng], form field `model_id?`) → parses the capture into flows (Scapy), classifies each with the given/active model, persists `TrafficFlow` + `SecurityAlert` rows, and returns `{flow_count, alerts_created, classification_breakdown, model_used}`. Corrupt/unparsable captures return a clear 400 error rather than a fake result.

## Traffic Explorer

- `GET /traffic` (query: `predicted_class, protocol, severity, src_ip, dst_ip, start, end, page, page_size`) → paginated `TrafficFlowSummary` list.
- `GET /traffic/{id}` → `TrafficFlowDetail` including a freshly recomputed explanation for that specific flow.

## Security Alerts

- `GET /alerts` (query: `severity, status, page, page_size`)
- `PUT /alerts/{id}/status` (`{"status": "open|acknowledged|resolved"}`)

Severity is assigned by an explicit, documented rule table (`app/core/severity.py`), not learned or invented — see `ML_PIPELINE.md`.

## Reports

- `POST /reports/generate` (`{experiment_id, formats: ["html","csv","pdf"]}`) → builds and saves the requested report file(s), returns a `ReportSummary`. Only works for a completed experiment with metrics.
- `GET /reports` → list of generated reports.
- `GET /reports/{id}/download?format=html|csv|pdf` → streams the file.
