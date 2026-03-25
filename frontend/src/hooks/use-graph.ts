"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

export interface GraphNode {
  id: string;
  name: string;
  node_type: "industry" | "company";
  symbol: string | null;
  sentiment: number | null;
  volume: number;
  industry: string | null;
  color: string | null;
}

export interface GraphEdge {
  source: string;
  target: string;
  edge_type: "industry_company" | "co_mention";
  weight: number;
  correlation: number | null;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export function useEntityGraph() {
  return useQuery({
    queryKey: ["entity-graph"],
    queryFn: () => apiFetch<GraphResponse>("/graph/entities"),
    refetchInterval: 15 * 60_000,
  });
}
