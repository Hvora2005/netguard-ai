# Architecture

## Layers

```
Frontend (React/Vite)
        │  HTTP/JSON
        ▼
FastAPI routes (app/api/routes/*)
        │
        ▼
Services (app/services/*)   ── business logic, orchestrates the layers below
        │
        ├──▶ Preprocessing (app/preprocessing/*)   — inspection, sklearn pipeline builders
        ├──▶ ML (app/ml/*)                          — model factory, trainer, evaluation,
        │                                              explainability, predictor, registry
        ├──▶ Network (app/network/*)                — Scapy PCAP parsing, raw-flow → model-feature mapping
        └──▶ Database (app/database/*, app/models/*) — SQLAlchemy engine/session, ORM models
        │
        ▼
SQLite file (netguard.db) + models_storage/ (joblib bundles) + uploads/ + reports/
```

Routes stay thin: they parse the request, call a service function, and return its result. All actual logic (validation beyond basic type-checking, file handling, ML training, PCAP parsing) lives in `app/services/*` or the lower layers, so it's testable without spinning up HTTP.

## Request flow example: training a model

1. `POST /api/models/train` (`app/api/routes/models.py`) receives a `TrainRequest`.
2. It loads the `Dataset` row and calls `app/ml/trainer.run_training`.
3. `run_training`:
   - reads the CSV via `app/services/dataset_service.load_dataframe`
   - resolves labels (binary collapse or multiclass, per `app/preprocessing/pipeline.resolve_labels`)
   - splits train/test (stratified)
   - builds an **unfitted** `ColumnTransformer` (`app/preprocessing/pipeline.build_preprocessor`) and fits it **only on the training split**
   - optionally applies SMOTE (training split only) or computes class weights
   - builds an estimator (`app/ml/model_factory.build_estimator`) and fits it
   - evaluates on the untouched test split (`app/ml/evaluation.evaluate_predictions`)
   - saves `{preprocessor, estimator, feature/class metadata}` as one joblib bundle (`app/ml/registry.save_bundle`)
   - persists an `Experiment` row (config + metrics) and an `MLModel` row (pointing at the bundle file)
4. The same bundle is loaded again, unchanged, for `/api/predict` and `/api/pcap/analyze` — this is what guarantees preprocessing consistency between training and inference (see `ML_PIPELINE.md`).

## Database schema

| Table | Purpose | Key relationships |
|---|---|---|
| `datasets` | Uploaded/generated CSV + computed metadata (column stats, class distribution) | — |
| `experiments` | One row per training run: config, hyperparameters, metrics, status | `dataset_id → datasets.id` |
| `ml_models` | Saved model registry: name, bundle path, active flag | `experiment_id → experiments.id` (1:1) |
| `predictions` | Every live prediction made via `/api/predict` | `model_id → ml_models.id` |
| `traffic_flows` | Flows extracted from an uploaded PCAP, with classification + severity | `model_id → ml_models.id` |
| `security_alerts` | Created automatically for non-benign flows | `flow_id → traffic_flows.id` |
| `reports` | Generated report file paths (HTML/CSV/PDF) | `experiment_id → experiments.id` |

Tables are created automatically on startup via `Base.metadata.create_all()` (see the `lifespan` handler in `app/main.py`) — no manual migration step for this project's scope.

## Frontend structure

- `layouts/DashboardLayout.tsx` — sidebar + topbar shell, all pages render inside it via `<Outlet />`
- `pages/*` — one file per nav item, each independently fetching its own data from `services/api.ts`
- `components/*` — shared building blocks: `Sidebar`, `Topbar`, `StatCard`, loading/empty/error states, `MetricsView`, toast provider
- `types/index.ts` — TypeScript interfaces mirroring the backend's Pydantic schemas, kept in sync by hand (no codegen, given the project's scale)

## Why these architectural choices

- **SQLite over Postgres by default**: zero setup for a university project; `DATABASE_URL` in `.env` can point at Postgres instead without code changes, since SQLAlchemy abstracts the dialect.
- **One joblib bundle per model** (preprocessor + estimator + metadata) rather than saving the raw estimator alone: this is what makes "preprocessing fit during training is reused consistently at inference" actually true, rather than just documented.
- **Services layer instead of logic-in-routes**: keeps route handlers testable and keeps `app/ml`/`app/network` reusable from a script or test without importing FastAPI at all.
- **No background job queue (Celery/Kafka)**: training/PCAP analysis run synchronously in the request. This is intentional for the project's scale — correctness and understandable architecture were prioritized over premature optimization; README's "Future extensions" section documents where a queue would slot in for larger datasets.
