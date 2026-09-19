export interface ColumnMeta {
  name: string;
  dtype: string;
  is_numeric: boolean;
  missing_count: number;
  unique_count: number;
}

export interface DatasetSummary {
  id: number;
  filename: string;
  original_filename: string;
  n_rows: number;
  n_columns: number;
  size_bytes: number;
  target_column: string | null;
  is_demo: boolean;
  status: string;
  created_at: string;
}

export interface DatasetDetail extends DatasetSummary {
  columns_meta: ColumnMeta[] | null;
  class_distribution: Record<string, number> | null;
  missing_values: Record<string, number> | null;
  duplicate_rows: number;
}

export interface DatasetPreview {
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface PreprocessingConfig {
  feature_columns: string[] | null;
  missing_strategy: "mean" | "median" | "most_frequent" | "drop_rows";
  scaling: "standard" | "minmax" | "none";
  categorical_encoding: "onehot" | "label";
  handle_imbalance: "none" | "smote" | "class_weight";
  test_size: number;
  task_type: "binary" | "multiclass";
  benign_labels: string[];
  random_state: number;
}

export interface ColumnStat {
  name: string;
  mean: number | null;
  std: number | null;
  missing_count: number;
}

export interface PreprocessingPreviewResponse {
  before_row_count: number;
  after_row_count: number;
  before_class_distribution: Record<string, number>;
  after_class_distribution: Record<string, number>;
  before_numeric_stats: ColumnStat[];
  after_numeric_stats: ColumnStat[];
  numeric_feature_count: number;
  categorical_feature_count: number;
  notes: string[];
}

export interface PerClassMetric {
  precision: number;
  recall: number;
  f1: number;
  support: number;
}

export interface ExperimentMetrics {
  accuracy: number;
  macro_f1: number;
  weighted_f1: number;
  per_class: Record<string, PerClassMetric>;
  confusion_matrix: number[][];
  class_labels: string[];
  roc_auc: number | null;
  pr_auc: number | null;
}

export interface ExperimentSummary {
  id: number;
  dataset_id: number;
  model_type: string;
  task_type: string;
  status: string;
  error_message: string | null;
  duration_seconds: number | null;
  created_at: string;
}

export interface ExperimentDetail extends ExperimentSummary {
  preprocessing_config: PreprocessingConfig;
  hyperparameters: Record<string, unknown>;
  metrics: ExperimentMetrics | null;
  feature_names: string[] | null;
  class_labels: string[] | null;
}

export interface MLModelSummary {
  id: number;
  experiment_id: number;
  name: string;
  model_type: string;
  task_type: string;
  is_active: boolean;
  created_at: string;
}

export interface FeatureSchemaField {
  name: string;
  is_numeric: boolean;
}

export interface ModelFeatureSchema {
  model_id: number;
  model_name: string;
  task_type: string;
  class_labels: string[];
  fields: FeatureSchemaField[];
}

export interface ExplanationItem {
  feature: string;
  contribution: number;
}

export interface PredictionResponse {
  id: number;
  model_id: number;
  predicted_class: string;
  confidence: number | null;
  probabilities: Record<string, number> | null;
  explanation: ExplanationItem[] | null;
  explanation_method: string;
  created_at: string;
}

export interface GlobalExplanationItem {
  feature: string;
  importance: number;
}

export interface GlobalExplanationResponse {
  model_id: number;
  method: string;
  importances: GlobalExplanationItem[] | null;
}

export interface TrafficFlowSummary {
  id: number;
  source_name: string;
  src_ip: string;
  dst_ip: string;
  src_port: number | null;
  dst_port: number | null;
  protocol: string;
  packet_count: number;
  byte_count: number;
  predicted_class: string | null;
  confidence: number | null;
  severity: string;
  first_seen: string | null;
  created_at: string;
}

export interface TrafficFlowDetail extends TrafficFlowSummary {
  duration_seconds: number;
  packet_rate: number;
  byte_rate: number;
  model_id: number | null;
  explanation: ExplanationItem[] | null;
  explanation_method: string | null;
}

export interface TrafficFlowPage {
  items: TrafficFlowSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface PcapAnalyzeResponse {
  flow_count: number;
  alerts_created: number;
  classification_breakdown: Record<string, number>;
  model_used: string;
}

export interface SecurityAlertSummary {
  id: number;
  flow_id: number;
  severity: string;
  classification: string;
  confidence: number | null;
  message: string;
  source: string;
  destination: string;
  status: string;
  created_at: string;
}

export interface SecurityAlertPage {
  items: SecurityAlertSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface ReportSummary {
  id: number;
  experiment_id: number;
  html_path: string | null;
  csv_path: string | null;
  pdf_path: string | null;
  created_at: string;
}

export const MODEL_TYPES = [
  { value: "logistic_regression", label: "Logistic Regression" },
  { value: "decision_tree", label: "Decision Tree" },
  { value: "random_forest", label: "Random Forest" },
  { value: "svm", label: "Support Vector Machine" },
  { value: "knn", label: "K-Nearest Neighbors" },
  { value: "xgboost", label: "XGBoost" },
  { value: "mlp", label: "MLP Neural Network" },
] as const;
