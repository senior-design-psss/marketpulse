"use client";

import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

interface SourceData {
  reddit_avg: number | null;
  reddit_volume: number;
  news_avg: number | null;
  news_volume: number;
  stocktwits_avg: number | null;
  stocktwits_volume: number;
}

export function SourceBreakdown({ data }: { data: SourceData }) {
  const sources = [
    { name: "Reddit", avg: data.reddit_avg, volume: data.reddit_volume, color: "#f97316" },
    { name: "News", avg: data.news_avg, volume: data.news_volume, color: "#3b82f6" },
    { name: "StockTwits", avg: data.stocktwits_avg, volume: data.stocktwits_volume, color: "#22c55e" },
  ];

  const totalVolume = sources.reduce((s, src) => s + src.volume, 0);

  const pieOption = {
    tooltip: {
      formatter: (params: { data: { name: string; value: number; avg: number | null } }) => {
        const d = params.data;
        const scoreStr = d.avg !== null ? `${d.avg >= 0 ? "+" : ""}${d.avg.toFixed(3)}` : "N/A";
        return `${d.name}<br/>Volume: ${d.value}<br/>Avg Score: ${scoreStr}`;
      },
    },
    series: [
      {
        type: "pie",
        radius: ["40%", "70%"],
        center: ["50%", "50%"],
        avoidLabelOverlap: true,
        itemStyle: { borderRadius: 4, borderColor: "#0f172a", borderWidth: 2 },
        label: {
          show: true,
          color: "#e2e8f0",
          fontSize: 11,
          formatter: "{b}\n{d}%",
        },
        data: sources.map((s) => ({
          name: s.name,
          value: s.volume,
          avg: s.avg,
          itemStyle: { color: s.color },
        })),
      },
    ],
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Source Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="h-[400px]">
        {totalVolume === 0 ? (
          <div className="flex h-full items-center justify-center text-muted-foreground">
            No source data yet
          </div>
        ) : (
          <ReactECharts option={pieOption} style={{ height: "100%", width: "100%" }} />
        )}
      </CardContent>
    </Card>
  );
}
