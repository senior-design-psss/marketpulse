"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

interface BriefingItem {
  id: string;
  briefing_type: string;
  title: string;
  content: string;
  key_insights: Record<string, unknown> | null;
  items_analyzed: number | null;
  generated_at: string;
}

interface BriefingResponse {
  briefing: BriefingItem | null;
}

interface BriefingListResponse {
  briefings: BriefingItem[];
}

interface CompanySummaryResponse {
  symbol: string;
  summary: string;
  generated_at: string | null;
}

export function useLatestBriefing() {
  return useQuery({
    queryKey: ["analyst-briefing"],
    queryFn: () => apiFetch<BriefingResponse>("/analyst/briefing"),
    refetchInterval: 30 * 60_000,
  });
}

export function useBriefingsList(limit = 10) {
  return useQuery({
    queryKey: ["analyst-briefings", limit],
    queryFn: () => apiFetch<BriefingListResponse>(`/analyst/briefings?limit=${limit}`),
    refetchInterval: 30 * 60_000,
  });
}

export function useCompanySummary(symbol: string) {
  return useQuery({
    queryKey: ["analyst-summary", symbol],
    queryFn: () => apiFetch<CompanySummaryResponse>(`/analyst/summary/${symbol}`),
    enabled: !!symbol,
    staleTime: 15 * 60_000,
  });
}

export type { BriefingItem, CompanySummaryResponse };
