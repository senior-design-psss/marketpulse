"use client";

import dynamic from "next/dynamic";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { PricePoint } from "@/hooks/use-market-data";
import type { TimeseriesPoint } from "@/types/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

export function PriceSentimentOverlay({
  prices,
  sentiment,
  symbol,
}: {
  prices: PricePoint[];
  sentiment: TimeseriesPoint[];
  symbol: string;
}) {
  if (!prices.length && !sentiment.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Price vs Sentiment</CardTitle>
        </CardHeader>
        <CardContent className="flex h-[400px] items-center justify-center text-muted-foreground">
          No price or sentiment data yet. Fetch prices from the Control Panel.
        </CardContent>
      </Card>
    );
  }

  // Build date-keyed sentiment averages
  const sentByDate: Record<string, { sum: number; count: number }> = {};
  for (const s of sentiment) {
    const date = s.timestamp.split("T")[0];
    if (!sentByDate[date]) sentByDate[date] = { sum: 0, count: 0 };
    sentByDate[date].sum += s.score;
    sentByDate[date].count += 1;
  }

  const dates = prices.map((p) => p.date);
  const sentimentLine = dates.map((d) => {
    const entry = sentByDate[d];
    return entry ? +(entry.sum / entry.count).toFixed(4) : null;
  });

  const option = {
    backgroundColor: "transparent",
    tooltip: {
      trigger: "axis",
      backgroundColor: "#141414",
      borderColor: "#333333",
      textStyle: { color: "#D7D7D7", fontSize: 11, fontFamily: "JetBrains Mono" },
      axisPointer: { type: "cross" },
    },
    legend: {
      data: ["Price", "Sentiment"],
      textStyle: { color: "#ACACAE", fontSize: 11 },
      top: 0,
    },
    xAxis: {
      type: "category",
      data: dates,
      axisLabel: { color: "#ACACAE", fontSize: 10, rotate: 30 },
      axisLine: { lineStyle: { color: "#333333" } },
    },
    yAxis: [
      {
        type: "value",
        name: "Price ($)",
        nameTextStyle: { color: "#FFA028", fontSize: 10 },
        position: "left",
        axisLabel: {
          color: "#ACACAE",
          fontSize: 10,
          formatter: (v: number) => `$${v.toFixed(0)}`,
        },
        splitLine: { lineStyle: { color: "#1A1A1A" } },
      },
      {
        type: "value",
        name: "Sentiment",
        nameTextStyle: { color: "#4AF6C3", fontSize: 10 },
        position: "right",
        min: -1,
        max: 1,
        axisLabel: {
          color: "#ACACAE",
          fontSize: 10,
          formatter: (v: number) => (v >= 0 ? "+" : "") + v.toFixed(1),
        },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: "Price",
        type: "candlestick",
        data: prices.map((p) => [p.open ?? p.close, p.close, p.low ?? p.close, p.high ?? p.close]),
        itemStyle: {
          color: "#0068FF",
          color0: "#FF433D",
          borderColor: "#0068FF",
          borderColor0: "#FF433D",
        },
        yAxisIndex: 0,
      },
      {
        name: "Sentiment",
        type: "line",
        data: sentimentLine,
        yAxisIndex: 1,
        smooth: true,
        symbol: "circle",
        symbolSize: 4,
        lineStyle: { width: 2, color: "#4AF6C3" },
        itemStyle: { color: "#4AF6C3" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(74, 246, 195, 0.2)" },
              { offset: 0.5, color: "rgba(74, 246, 195, 0)" },
              { offset: 1, color: "rgba(255, 67, 61, 0.2)" },
            ],
          },
        },
        connectNulls: true,
      },
    ],
    grid: { left: 60, right: 60, top: 40, bottom: 60 },
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Price vs Sentiment — {symbol}</span>
          <span className="text-xs font-normal text-muted-foreground">
            Blue candles = price up, Red = down | Green line = sentiment
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="h-[400px]">
        <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
      </CardContent>
    </Card>
  );
}
