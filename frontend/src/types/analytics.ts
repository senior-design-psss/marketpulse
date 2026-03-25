// Analytics API types

export interface MomentumItem {
  symbol: string;
  name: string;
  avg_score: number;
  momentum: number;
  acceleration: number | null;
  volume: number;
}

export interface MomentumResponse {
  movers: MomentumItem[];
}

export interface AnomalyAlertItem {
  id: string;
  company_symbol: string | null;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  metric_value: number | null;
  baseline_value: number | null;
  z_score: number | null;
  triggered_at: string;
}

export interface AnomalyResponse {
  alerts: AnomalyAlertItem[];
}

export interface CrossSourceItem {
  symbol: string;
  source_a: string;
  source_b: string;
  score_a: number;
  score_b: number;
  divergence: number;
}

export interface CrossSourceResponse {
  signals: CrossSourceItem[];
}

export interface PredictiveSignalItem {
  id: string;
  symbol: string;
  signal_type: string;
  direction: string;
  strength: number;
  correlation: number | null;
  lag_hours: number | null;
  description: string;
  generated_at: string;
}

export interface PredictiveResponse {
  signals: PredictiveSignalItem[];
}
