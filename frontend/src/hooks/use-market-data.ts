"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  CompanyDetail,
  CompanyListResponse,
  CompanyTimeseriesResponse,
  HeatmapResponse,
  IndustryListResponse,
  MarketOverview,
  RadarResponse,
  SentimentFeedResponse,
  Timeframe,
  Source,
} from "@/types/api";

// === Market Overview ===
export function useMarketOverview() {
  return useQuery({
    queryKey: ["market-overview"],
    queryFn: () => apiFetch<MarketOverview>("/sentiment/overview"),
    refetchInterval: 15_000,
    staleTime: 5_000,
  });
}

// === Industries ===
export function useIndustries() {
  return useQuery({
    queryKey: ["industries"],
    queryFn: () => apiFetch<IndustryListResponse>("/industries"),
    refetchInterval: 5 * 60_000,
  });
}

export function useIndustryHeatmap(slug: string) {
  return useQuery({
    queryKey: ["industry-heatmap", slug],
    queryFn: () => apiFetch<HeatmapResponse>(`/industries/${slug}/heatmap`),
    enabled: !!slug,
    refetchInterval: 5 * 60_000,
  });
}

export function useIndustryRadar(slug: string) {
  return useQuery({
    queryKey: ["industry-radar", slug],
    queryFn: () => apiFetch<RadarResponse>(`/industries/${slug}/radar`),
    enabled: !!slug,
    refetchInterval: 5 * 60_000,
  });
}

// === Companies ===
export function useCompanies() {
  return useQuery({
    queryKey: ["companies"],
    queryFn: () => apiFetch<CompanyListResponse>("/companies"),
    refetchInterval: 5 * 60_000,
  });
}

export function useCompanyDetail(symbol: string) {
  return useQuery({
    queryKey: ["company", symbol],
    queryFn: () => apiFetch<CompanyDetail>(`/companies/${symbol}`),
    enabled: !!symbol,
    refetchInterval: 2 * 60_000,
  });
}

export function useCompanyTimeseries(
  symbol: string,
  timeframe: Timeframe = "24h",
  source: Source | "all" = "all"
) {
  return useQuery({
    queryKey: ["company-timeseries", symbol, timeframe, source],
    queryFn: () =>
      apiFetch<CompanyTimeseriesResponse>(
        `/companies/${symbol}/timeseries?timeframe=${timeframe}&source=${source}`
      ),
    enabled: !!symbol,
    refetchInterval: 5 * 60_000,
  });
}

// === Sentiment Feed ===
export function useSentimentFeed(
  page: number = 1,
  source: Source | "all" = "all",
  label: string = "all"
) {
  return useQuery({
    queryKey: ["sentiment-feed", page, source, label],
    queryFn: () =>
      apiFetch<SentimentFeedResponse>(
        `/sentiment/feed?page=${page}&page_size=20&source=${source}&label=${label}`
      ),
    refetchInterval: 15_000,
    staleTime: 5_000,
  });
}

// === Company Sources (articles) ===
export interface SourceArticle {
  id: string;
  source: string;
  title: string | null;
  body: string;
  url: string | null;
  author: string | null;
  subreddit: string | null;
  published_at: string | null;
  ensemble_score: number;
  ensemble_label: string;
  ensemble_confidence: number;
  finbert_label: string | null;
  finbert_positive: number | null;
  finbert_negative: number | null;
  llm_score: number | null;
  llm_reasoning: string | null;
  scored_at: string | null;
}

export interface CompanySourcesResponse {
  symbol: string;
  total: number;
  page: number;
  items: SourceArticle[];
}

export function useCompanySources(symbol: string, page: number = 1) {
  return useQuery({
    queryKey: ["company-sources", symbol, page],
    queryFn: () =>
      apiFetch<CompanySourcesResponse>(`/companies/${symbol}/sources?page=${page}&page_size=20`),
    enabled: !!symbol,
  });
}

// === Company Prices ===
export interface PricePoint {
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number;
  volume: number | null;
  daily_return: number | null;
}

export interface CompanyPricesResponse {
  symbol: string;
  prices: PricePoint[];
}

export function useCompanyPrices(symbol: string, days: number = 30) {
  return useQuery({
    queryKey: ["company-prices", symbol, days],
    queryFn: () => apiFetch<CompanyPricesResponse>(`/companies/${symbol}/prices?days=${days}`),
    enabled: !!symbol,
  });
}
