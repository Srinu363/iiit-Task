/** API types matching backend Pydantic schemas. */

export interface Issue {
  type: string;
  severity: "low" | "medium" | "high";
  confidence: number;
  uncertain: boolean;
}

export interface FeatureImportance {
  feature: string;
  value: number;
  reference: number;
  deviation: number;
}

export interface AnalysisResult {
  id: string;
  filename: string;
  file_hash: string;
  created_at: string;
  quality_score: number;
  quality_label: "ACCEPTABLE" | "DEGRADED" | "DEFECTIVE";
  issues: Issue[];
  image_stats: Record<string, number>;
  explanations: string[];
  feature_importance: FeatureImportance[];
  heatmaps: Record<string, number[][]> | null;
  anomaly_score: number | null;
  model_version: string | null;
  latency_ms: number | null;
  cached: boolean;
}

export interface AnalysisListItem {
  id: string;
  filename: string;
  file_hash: string;
  created_at: string;
  quality_score: number;
  quality_label: "ACCEPTABLE" | "DEGRADED" | "DEFECTIVE";
  issues: Issue[];
  latency_ms: number | null;
  cached: boolean;
}

export interface AnalysisListResponse {
  items: AnalysisListItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface HealthResponse {
  status: string;
  model_loaded: boolean;
  database_connected: boolean;
  version: string;
}

export interface ModelInfoResponse {
  model_version: string | null;
  training_date: string | null;
  num_features: number | null;
  feature_names: string[];
  issue_types: string[];
  training_samples: number | null;
  regressor_metrics: Record<string, number> | null;
}
