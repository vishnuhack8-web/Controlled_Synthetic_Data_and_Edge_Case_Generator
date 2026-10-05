export type ParameterType = "number" | "category" | "text" | "boolean" | "datetime";

export interface NumberConfig {
  min: number;
  max: number;
  unit: string;
  distribution: "uniform" | "normal" | "exponential";
}

export interface CategoryConfig {
  values: string[];
  weights?: number[];
}

export interface TextConfig {
  note: string;
  format: string;
}

export interface BooleanConfig {
  true_share: number;
}

export interface DatetimeConfig {
  interval: string;
  start_time: string;
}

export interface Parameter {
  name: string;
  type: ParameterType;
  number?: NumberConfig;
  category?: CategoryConfig;
  text?: TextConfig;
  boolean?: BooleanConfig;
  datetime?: DatetimeConfig;
}

export interface MachineProfile {
  id?: string;
  name: string;
  description: string;
  suggested_domain: string;
  domain: string;
  parameters: Parameter[];
}

export interface GenerationConfig {
  machine_id: string;
  num_records: number;
  edge_case_frequency: number;
  scenario: string;
  seed?: number;
  output_format: "csv" | "json" | "parquet";
}

export interface LLMStatus {
  reachable: boolean;
  models_installed: string[];
  model_in_use: string | null;
  using_fallback: boolean;
}

export interface QualityReport {
  quality_score: number;
  schema_compliance_pct: number;
  completeness_pct: number;
  range_satisfaction_pct: number;
  statistical_fidelity_pct: number;
  passed: boolean;
  details: string[];
}

export interface PrivacyReport {
  privacy_score: number;
  exact_matches_found: number;
  nearest_neighbor_min_dist: number;
  k_anonymity_min: number;
  pii_leaks_count: number;
  passed: boolean;
  details: string[];
}

export interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  cv_f1_mean: number;
  cv_f1_std: number;
}

export interface PredictiveReport {
  model_name: string;
  with_edge_cases: ModelMetrics;
  without_edge_cases: ModelMetrics;
  edge_case_value_gain_f1: number;
  edge_case_value_gain_recall: number;
  summary_message: string;
}

export interface RunResult {
  run_id: string;
  machine_id: string;
  machine_name: string;
  domain: string;
  num_records: number;
  edge_case_frequency: number;
  total_edge_cases: number;
  scenario: string;
  seed: number;
  output_format: string;
  file_name: string;
  quality_report: QualityReport;
  privacy_report: PrivacyReport;
  predictive_report: PredictiveReport;
  trend_analytics: Record<string, any>;
  edge_case_breakdown: Record<string, number>;
  preview_rows: Record<string, any>[];
  columns: string[];
}
