"use client";

import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { RadarCompany } from "@/types/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

export function SentimentRadarChart({
  companies,
  title = "Multi-Source Sentiment",
}: {
  companies: RadarCompany[];
  title?: string;
}) {
  if (!companies.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="flex h-[400px] items-center justify-center text-muted-foreground">
          No data yet
        </CardContent>
      </Card>
    );
  }

  // Take top 5 companies for readability
  const top = companies.slice(0, 5);
  const colors = ["#3b82f6", "#22c55e", "#f97316", "#a855f7", "#ec4899"];

  const option = {
    tooltip: {},
    legend: {
      data: top.map((c) => c.symbol),
      textStyle: { color: "#94a3b8", fontSize: 11 },
      bottom: 0,
    },
    radar: {
      indicator: [
        { name: "Reddit", max: 1 },
        { name: "News", max: 1 },
        { name: "StockTwits", max: 1 },
      ],
      shape: "polygon",
      axisName: { color: "#e2e8f0", fontSize: 12 },
      splitArea: { areaStyle: { color: ["#0f172a", "#1e293b"] } },
      splitLine: { lineStyle: { color: "#334155" } },
      axisLine: { lineStyle: { color: "#334155" } },
    },
    series: [
      {
        type: "radar",
        data: top.map((c, i) => ({
          name: c.symbol,
          value: [
            Math.max(0, (c.sources.reddit ?? 0) + 1) / 2, // Map -1..1 to 0..1
            Math.max(0, (c.sources.news ?? 0) + 1) / 2,
            Math.max(0, (c.sources.stocktwits ?? 0) + 1) / 2,
          ],
          lineStyle: { color: colors[i] },
          itemStyle: { color: colors[i] },
          areaStyle: { color: colors[i], opacity: 0.1 },
        })),
      },
    ],
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="h-[400px]">
        <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      </CardContent>
    </Card>
  );
}
