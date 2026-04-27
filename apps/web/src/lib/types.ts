export type AnalysisStatus = "pending" | "crawling" | "scraping" | "analyzing" | "completed" | "failed";

export interface Analysis {
  id: string;
  topic: string;
  location: string | null;
  category: string | null;
  status: AnalysisStatus;
  created_at: string;
  updated_at: string;
  sources_count?: number;
  items_count?: number;
}

export interface Source {
  id: string;
  analysis_id: string;
  url: string;
  title: string | null;
  source_type: string;
  status: string;
  created_at: string;
}

export interface ScrapedItem {
  id: string;
  analysis_id: string;
  source_id: string | null;
  name: string | null;
  description: string | null;
  address: string | null;
  price_text: string | null;
  price_min: number | null;
  price_max: number | null;
  rating: number | null;
  review_count: number | null;
  raw_text: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface Insight {
  id: string;
  analysis_id: string;
  summary: string | null;
  opportunities: string[];
  competitors: string[];
  pricing_insight: string | null;
  customer_pain_points: string[];
  strategy_recommendations: string[];
  raw_ai_response: Record<string, unknown>;
  created_at: string;
}

