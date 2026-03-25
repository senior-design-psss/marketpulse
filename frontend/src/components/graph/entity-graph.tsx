"use client";

import { useRouter } from "next/navigation";
import dynamic from "next/dynamic";
import type { GraphNode, GraphEdge } from "@/hooks/use-graph";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

function sentimentToColor(score: number | null): string {
  if (score === null) return "#475569";
  if (score > 0.3) return "#2E7D32";
  if (score > 0.1) return "#66BB6A";
  if (score > -0.1) return "#475569";
  if (score > -0.3) return "#E57373";
  return "#D32F2F";
}

export function EntityGraphViz({
  nodes,
  edges,
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
}) {
  const router = useRouter();

  if (!nodes.length) {
    return (
      <div className="flex h-[600px] items-center justify-center text-muted-foreground">
        No data yet — run the pipeline from the Control Panel
      </div>
    );
  }

  const industryNodes = nodes.filter((n) => n.node_type === "industry");
  const companyNodes = nodes.filter((n) => n.node_type === "company");

  // Categories for legend (one per industry)
  const categories = industryNodes.map((ind) => ({
    name: ind.name,
    itemStyle: { color: ind.color || "#6b7280" },
  }));

  const categoryMap: Record<string, number> = {};
  industryNodes.forEach((ind, i) => {
    categoryMap[ind.id.replace("ind_", "")] = i;
  });

  // Industry hub nodes — large circles
  const hubNodes = industryNodes.map((ind) => ({
    id: ind.id,
    name: ind.name,
    symbolSize: 55,
    category: categoryMap[ind.id.replace("ind_", "")] ?? 0,
    itemStyle: {
      color: ind.color || "#6b7280",
      borderColor: sentimentToColor(ind.sentiment),
      borderWidth: 4,
      shadowBlur: 15,
      shadowColor: (ind.color || "#6b7280") + "60",
    },
    label: {
      show: true,
      color: "#FFA028",
      fontSize: 12,
      fontWeight: "bold" as const,
      fontFamily: "JetBrains Mono, monospace",
    },
    tooltip: {
      formatter: () => {
        const s = ind.sentiment;
        const score = s != null ? (s >= 0 ? "+" : "") + s.toFixed(3) : "N/A";
        return (
          `<strong style="color:${ind.color || "#FFA028"}">${ind.name}</strong><br/>`
          + `Sentiment: ${score}<br/>Volume: ${ind.volume} items`
        );
      },
    },
    _type: "industry",
    _slug: ind.id.replace("ind_", ""),
  }));

  // Company nodes — sized by volume, colored by sentiment
  const compNodes = companyNodes.map((c) => ({
    id: c.symbol || c.id,
    name: c.symbol || c.name,
    symbolSize: Math.max(25, Math.min(40, 25 + (c.volume / 3))),
    category: c.industry ? (categoryMap[c.industry] ?? 0) : 0,
    itemStyle: {
      color: sentimentToColor(c.sentiment),
      borderColor: "#1E1E1E",
      borderWidth: 2,
    },
    label: {
      show: true,
      color: "#D7D7D7",
      fontSize: 10,
      fontFamily: "JetBrains Mono, monospace",
      fontWeight: "bold" as const,
    },
    tooltip: {
      formatter: () => {
        const s = c.sentiment;
        const score = s != null ? (s >= 0 ? "+" : "") + s.toFixed(3) : "N/A";
        return (
          `<strong style="color:#FFA028">${c.symbol}</strong> (${c.name})<br/>`
          + `Sentiment: ${score}<br/>Volume: ${c.volume}<br/>Industry: ${c.industry || "N/A"}`
        );
      },
    },
    _type: "company",
    _symbol: c.symbol,
  }));

  // Build edges
  const echartEdges = edges.map((e) => {
    const isHub = e.edge_type === "industry_company";
    return {
      source: e.source,
      target: e.target,
      lineStyle: {
        width: isHub ? 1.5 : Math.max(2, Math.min(6, e.weight)),
        color: isHub
          ? "#333333"
          : e.correlation != null
            ? e.correlation > 0.2 ? "#4AF6C3" : e.correlation < -0.2 ? "#FF433D" : "#475569"
            : "#FFA028",
        opacity: isHub ? 0.3 : 0.7,
        type: isHub ? ("dashed" as const) : ("solid" as const),
        curveness: isHub ? 0 : 0.2,
      },
      tooltip: {
        formatter: () =>
          isHub
            ? `${e.source.replace("ind_", "")} → ${e.target}`
            : `${e.source} ↔ ${e.target}<br/>Co-mentions: ${e.weight}${
                e.correlation != null ? `<br/>Correlation: ${e.correlation.toFixed(3)}` : ""
              }`,
      },
    };
  });

  const option = {
    tooltip: {
      trigger: "item",
      backgroundColor: "#141414",
      borderColor: "#333",
      textStyle: { color: "#D7D7D7", fontSize: 11, fontFamily: "JetBrains Mono" },
    },
    legend: {
      data: categories.map((c) => c.name),
      textStyle: { color: "#ACACAE", fontSize: 10, fontFamily: "JetBrains Mono" },
      top: 10,
      itemWidth: 12,
      itemHeight: 12,
    },
    animationDuration: 2000,
    animationEasingUpdate: "quinticInOut",
    series: [
      {
        type: "graph",
        layout: "force",
        data: [...hubNodes, ...compNodes],
        links: echartEdges,
        categories,
        roam: true,
        draggable: true,
        force: {
          repulsion: 400,
          edgeLength: [60, 180],
          gravity: 0.08,
          friction: 0.6,
          layoutAnimation: true,
        },
        emphasis: {
          focus: "adjacency",
          lineStyle: { width: 4, opacity: 1 },
          itemStyle: { borderWidth: 6 },
        },
      },
    ],
  };

  const onEvents = {
    click: (params: { data?: { _type?: string; _symbol?: string; _slug?: string } }) => {
      const d = params.data;
      if (!d) return;
      if (d._type === "company" && d._symbol) {
        router.push(`/companies/${d._symbol.toLowerCase()}`);
      } else if (d._type === "industry" && d._slug) {
        router.push(`/industries/${d._slug}`);
      }
    },
  };

  return (
    <ReactECharts
      option={option}
      style={{ height: "100%", width: "100%" }}
      onEvents={onEvents}
    />
  );
}
