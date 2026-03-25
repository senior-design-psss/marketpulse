"use client";

import dynamic from "next/dynamic";
import { useIndustries } from "@/hooks/use-market-data";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

// Bloomberg-style red-gray-green gradient
function scoreToColor(score: number | null): string {
  if (score === null) return "#424242";
  if (score > 0.3) return "#2E7D32";
  if (score > 0.1) return "#66BB6A";
  if (score > 0.02) return "#A5D6A7";
  if (score > -0.02) return "#424242";
  if (score > -0.1) return "#EF9A9A";
  if (score > -0.3) return "#E57373";
  return "#D32F2F";
}

export function IndustryHeatmap() {
  const { data, isLoading } = useIndustries();

  if (isLoading || !data) {
    return (
      <div className="flex h-[280px] items-center justify-center font-mono text-[11px] text-muted-foreground sm:h-[340px] lg:h-[380px]">
        Loading MMAP...
      </div>
    );
  }

  const treemapData = data.industries.map((ind) => ({
    name: ind.name,
    value: Math.max(ind.volume, 1),
    score: ind.avg_score,
    itemStyle: {
      color: scoreToColor(ind.avg_score),
      borderColor: "#000000",
      borderWidth: 2,
    },
  }));

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      backgroundColor: "#141414",
      borderColor: "#333333",
      textStyle: { color: "#D7D7D7", fontSize: 11, fontFamily: "JetBrains Mono" },
      formatter: (params: { data?: { name?: string; score?: number | null; value?: number } }) => {
        const d = params.data;
        if (!d || !d.name) return "";
        const s = d.score;
        const score = s != null ? (s >= 0 ? "+" : "") + s.toFixed(3) : "N/A";
        return `<strong style="color:#FFA028">${d.name}</strong><br/>Sentiment: ${score}<br/>Volume: ${d.value ?? 0}`;
      },
    },
    series: [
      {
        type: "treemap",
        data: treemapData,
        roam: false,
        nodeClick: false,
        breadcrumb: { show: false },
        label: {
          show: true,
          formatter: (params: { data?: { name?: string; score?: number | null } }) => {
            if (!params.data?.name) return "";
            const s = params.data.score;
            const scoreStr = s != null ? (s >= 0 ? "+" : "") + s.toFixed(2) : "";
            return `${params.data.name}\n${scoreStr}`;
          },
          color: "#FFFFFF",
          fontSize: 11,
          fontWeight: "bold",
          fontFamily: "JetBrains Mono, monospace",
        },
        levels: [
          {
            itemStyle: {
              borderColor: "#000000",
              borderWidth: 3,
              gapWidth: 2,
            },
          },
        ],
      },
    ],
  };

  return (
    <div className="h-[280px] min-w-0 sm:h-[340px] lg:h-[380px]">
      <ReactECharts
        option={option}
        style={{ height: "100%", width: "100%" }}
        opts={{ renderer: "canvas" }}
      />
    </div>
  );
}
