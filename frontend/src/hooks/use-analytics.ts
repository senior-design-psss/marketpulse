"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type {
  AnomalyResponse,
  CrossSourceResponse,
  MomentumResponse,
  PredictiveResponse,
} from "@/types/analytics";

export function useMomentum() {
  return useQuery({
    queryKey: ["analytics-momentum"],
    queryFn: () => apiFetch<MomentumResponse>("/analytics/momentum"),
    refetchInterval: 5 * 60_000,
  });
}

export function useAnomalies() {
  return useQuery({
    queryKey: ["analytics-anomalies"],
    queryFn: () => apiFetch<AnomalyResponse>("/analytics/anomalies"),
    refetchInterval: 2 * 60_000,
  });
}

export function useCrossSource() {
  return useQuery({
    queryKey: ["analytics-cross-source"],
    queryFn: () => apiFetch<CrossSourceResponse>("/analytics/cross-source"),
    refetchInterval: 5 * 60_000,
  });
}

export function usePredictiveSignals() {
  return useQuery({
    queryKey: ["analytics-predictive"],
    queryFn: () => apiFetch<PredictiveResponse>("/analytics/predictive"),
    refetchInterval: 15 * 60_000,
  });
}
