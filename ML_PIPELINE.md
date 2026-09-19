# ML Pipeline

## End-to-end flow

```
Raw CSV
  │  app/services/dataset_service.load_dataframe
  │  (strip column names, replace inf with NaN)
  ▼
Column/class inspection (app/preprocessing/inspection.py)
  │  auto-guess target column, compute column metadata,
  │  class distribution, missing-value summary
  ▼
Label resolution (app/preprocessing/pipeline.resolve_labels)
  │  binary: collapse to BENIGN / MALICIOUS via configured benign_labels
  │  multiclass: use raw label strings as-is (no hardcoded categories)
  ▼
Train/test split (stratified, app/ml/trainer.run_training)
  ▼
Preprocessing — FIT ONLY ON THE TRAINING SPLIT
  │  numeric: impute (mean/median/most_frequent) -> scale (standard/minmax/none)
  │  categorical: impute (most_frequent) -> encode (one-hot/ordinal)
  │  (app/preprocessing/pipeline.build_preprocessor — returns an UNFITTED
  │   sklearn ColumnTransformer; the caller decides what to fit it on)
  ▼
Class imbalance handling (training split only)
  │  none | SMOTE (imblearn, training rows only) | class_weight (passed to
  │  the estimator's constructor, only for models that support it)
  ▼
Model training (app/ml/model_factory.build_estimator)
  │  logistic_regression | decision_tree | random_forest | svm | knn |
  │  xgboost | mlp
  ▼
Evaluation on the UNTOUCHED test split (app/ml/evaluation.py)
  │  accuracy, macro/weighted F1, per-class precision/recall/F1/support,
  │  confusion matrix, ROC-AUC + PR-AUC (binary: direct; multiclass: OVR
  │  macro-averaged) — AUC is left null rather than guessed if a class has
  │  zero test-set samples
  ▼
Persist ONE bundle: {preprocessor (fitted), estimator (fitted),
                       feature/numeric/categorical column names,
                       class_labels, task_type, model_type}
  (app/ml/registry.save_bundle — joblib file per experiment)
  ▼
Reused, unchanged, for:
  - POST /api/predict            (app/ml/predictor.predict_single)
  - POST /api/pcap/analyze       (app/ml/predictor.predict_batch)
  - GET  /api/traffic/{id}       (recomputes explanation via the same bundle)
```

**Why this avoids data leakage:** the `ColumnTransformer` returned by `build_preprocessor` is unfitted. `run_training` calls `.fit_transform(X_train)` and `.transform(X_test)` — the test split never influences an imputer's median, a scaler's mean/std, or a one-hot encoder's known categories. `POST /api/preprocessing/preview` is the one deliberate exception: it fits on the whole dataset, but only to show illustrative before/after numbers in the UI, and that fitted instance is thrown away — it never touches `run_training`.

## Model comparison — no single "best" model

`GET /experiments` and the Model Comparison page report accuracy, macro F1, weighted F1, ROC-AUC, and PR-AUC side by side, plus training time. The app deliberately does not declare a "winner": which metric matters (e.g., recall over precision when missing an attack is costlier than a false alarm) depends on deployment context and class distribution, and report conclusions (`app/services/report_service.py`) state this explicitly rather than picking a favorite.

## Explainability

Preference order, all in `app/ml/explainability.py`:

1. **SHAP `TreeExplainer`** — only for tree-based models (`random_forest`, `decision_tree`, `xgboost`) and only if the optional `shap` package is installed (see `requirements-explainability.txt`). Computed directly on the instance being explained, no stored background dataset needed.
2. **Coefficient × transformed feature value** — for models exposing `coef_` (e.g. `logistic_regression`), a real per-instance contribution.
3. **Model `feature_importances_`** — global importance reused as the local explanation when neither of the above applies, labeled `model_feature_importance_global_fallback` so the UI is honest that it isn't instance-specific.
4. **Unavailable** — reported as such (e.g. KNN, non-linear SVM, or MLP without SHAP) rather than fabricating a number.

Every explanation response includes `explanation_method` so the frontend (and report) can show which of the above actually produced it. None of these values are presented as causal — the UI and reports explicitly label them as describing model behavior, not real-world cause and effect.

## PCAP → ML feature mapping

`app/network/pcap_parser.py` groups packets into **unidirectional** 5-tuple flows (src/dst IP+port, protocol) using Scapy — a deliberate simplification versus full bidirectional flow reconstruction (like CICFlowMeter), chosen because it needs no extra system dependencies and still produces real, non-fabricated per-flow statistics (packet/byte counts, duration, rates, SYN/ACK counts).

`app/network/feature_mapping.py` then maps those raw stats onto whatever feature columns the *selected trained model* expects, using CIC-IDS-style names (`Destination Port`, `Flow Duration`, `Flow Bytes/s`, `SYN Flag Count`, etc.). Any expected column this parser cannot derive — notably `Total Backward Packets`, since flows here are unidirectional — is left as `NaN`, which the model's own imputer (fit during training) fills in exactly the way it fills any other missing value. This is documented as a limitation, not hidden: PCAP classification works best against a model trained with CIC-IDS-style column names (the bundled demo dataset uses this convention deliberately).

## Severity rules for alerts

`app/core/severity.py` defines an explicit lookup table (e.g. `ddos → critical`, `dos → high`, `port scan → medium`), not a learned or "AI-decided" severity. A prediction's severity is downgraded one level when the model's own confidence is below `LOW_CONFIDENCE_THRESHOLD` (0.6), since a low-confidence "critical" call is less actionable than a high-confidence one. Alert messages read "Model detected traffic matching the learned pattern for X" — never "X attack confirmed" — since a classifier prediction is not a confirmed real-world incident.
