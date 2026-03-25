"use client";

import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { TimeseriesPoint } from "@/types/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

export function SentimentTimeseries({
  data,
  title = "Sentiment Timeline",
}: {
  data: TimeseriesPoint[];
  title?: string;
}) {
  if (!data.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="flex h-[400px] items-center justify-center text-muted-foreground">
          No sentiment data yet
        </CardContent>
      </Card>
    );
  }

  const timestamps = data.map((d) =>
    new Date(d.timestamp).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  );
  const scores = data.map((d) => d.score);

  const option = {
    tooltip: {
      trigger: "axis",
      formatter: (params: { dataIndex: number }[]) => {
        const idx = params[0].dataIndex;
        const point = data[idx];
        return `${timestamps[idx]}<br/>Score: ${point.score >= 0 ? "+" : ""}${point.score.toFixed(3)}<br/>Source: ${point.source || "all"}`;
      },
    },
    xAxis: {
      type: "category",
      data: timestamps,
      axisLabel: { color: "#94a3b8", fontSize: 10, rotate: 30 },
      axisLine: { lineStyle: { color: "#334155" } },
    },
    yAxis: {
      type: "value",
      min: -1,
      max: 1,
      axisLabel: {
        color: "#94a3b8",
        fontSize: 10,
        formatter: (v: number) => (v >= 0 ? "+" : "") + v.toFixed(1),
      },
      splitLine: { lineStyle: { color: "#1e293b" } },
    },
    series: [
      {
        type: "line",
        data: scores,
        smooth: true,
        symbol: "circle",
        symbolSize: 4,
        lineStyle: { width: 2, color: "#3b82f6" },
        itemStyle: { color: "#3b82f6" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(59, 130, 246, 0.3)" },
              { offset: 0.5, color: "rgba(59, 130, 246, 0.05)" },
              { offset: 1, color: "rgba(239, 68, 68, 0.3)" },
            ],
          },
        },
        markLine: {
          silent: true,
          data: [{ yAxis: 0, lineStyle: { color: "#475569", type: "dashed" } }],
          label: { show: false },
        },
      },
    ],
    grid: { left: 50, right: 20, top: 20, bottom: 60 },
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
