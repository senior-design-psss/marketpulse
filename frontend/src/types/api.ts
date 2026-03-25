// TypeScript types matching backend Pydantic schemas

// === Industries ===
export interface Industry {
  id: string;
  name: string;
  slug: string;
  display_color: string | null;
}

export interface IndustryWithSentiment extends Industry {
  avg_score: number | null;
  volume: number;
  momentum: number | null;
  confidence: number | null;
}

export interface IndustryListResponse {
  industries: IndustryWithSentiment[];
}

export interface HeatmapCompany {
  symbol: string;
  name: string;
  score: number;
  volume: number;
  momentum: number | null;
  change: number | null;
}

export interface HeatmapResponse {
  industry: Industry;
  companies: HeatmapCompany[];
}

export interface RadarSource {
  reddit: number | null;
  news: number | null;
  stocktwits: number | null;
}

export interface RadarCompany {
  symbol: string;
  name: string;
  sources: RadarSource;
}

export interface RadarResponse {
  industry: Industry;
  companies: RadarCompany[];
}

// === Companies ===
export interface CompanyBase {
  id: string;
  symbol: string;
  name: string;
}

export interface CompanyWithSentiment extends CompanyBase {
  avg_score: number | null;
  volume: number;
  momentum: number | null;
  acceleration: number | null;
  confidence: number | null;
  industries: string[];
  price: number | null;
  price_change: number | null;
  price_date: string | null;
}

export interface CompanyListResponse {
  companies: CompanyWithSentiment[];
}

export interface CompanyDetail extends CompanyWithSentiment {
  reddit_avg: number | null;
  reddit_volume: number;
  news_avg: number | null;
  news_volume: number;
  stocktwits_avg: number | null;
  stocktwits_volume: number;
}

export interface TimeseriesPoint {
  timestamp: string;
  score: number;
  volume: number;
  source: string | null;
}

export interface CompanyTimeseriesResponse {
  company: CompanyBase;
  data: TimeseriesPoint[];
  timeframe: string;
}

// === Sentiment ===
export interface SentimentFeedItem {
  id: string;
  source: string;
  company_symbol: string | null;
  company_name: string | null;
  title: string | null;
  body_excerpt: string;
  ensemble_score: number;
  ensemble_label: string;
  ensemble_confidence: number;
  finbert_label: string | null;
  llm_reasoning: string | null;
  scored_at: string;
}

export interface SentimentFeedResponse {
  items: SentimentFeedItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface MarketOverview {
  overall_score: number;
  overall_label: string;
  total_items_today: number;
  active_alerts: number;
  sources_active: number;
  industries: {
    slug: string;
    name: string;
    color: string | null;
    score: number | null;
    volume: number;
  }[];
}

// === Common ===
export type SentimentLabel =
  | "very_positive"
  | "positive"
  | "neutral"
  | "negative"
  | "very_negative";

export type Source = "reddit" | "news" | "stocktwits";
export type Timeframe = "1h" | "6h" | "24h" | "7d" | "30d";
