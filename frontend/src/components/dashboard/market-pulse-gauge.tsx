"use client";

import dynamic from "next/dynamic";
import { useMarketOverview } from "@/hooks/use-market-data";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

export function MarketPulseGauge() {
  const { data, isLoading } = useMarketOverview();

  if (isLoading || !data) {
    return (
      <div className="flex h-[220px] items-center justify-center font-mono text-[11px] text-muted-foreground sm:h-[240px] lg:h-[260px]">
        Loading gauge...
      </div>
    );
  }

  const gaugeValue = ((data.overall_score + 1) / 2) * 100;

  const option = {
    backgroundColor: "transparent",
    series: [
      {
        type: "gauge",
        startAngle: 180,
        endAngle: 0,
        min: 0,
        max: 100,
        splitNumber: 4,
        axisLine: {
          lineStyle: {
            width: 20,
            color: [
              [0.25, "#FF433D"],
              [0.45, "#E57373"],
              [0.55, "#424242"],
              [0.75, "#66BB6A"],
              [1, "#2E7D32"],
            ],
          },
        },
        pointer: {
          icon: "path://M12.8,0.7l12,40.1H0.7L12.8,0.7z",
          length: "60%",
          width: 8,
          offsetCenter: [0, "-10%"],
          itemStyle: { color: "#FFA028" },
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: {
          show: true,
          distance: -35,
          color: "#ACACAE",
          fontSize: 10,
          fontFamily: "JetBrains Mono",
          formatter: (value: number) => {
            if (value === 0) return "BEAR";
            if (value === 50) return "NTRL";
            if (value === 100) return "BULL";
            return "";
          },
        },
        detail: {
          valueAnimation: true,
          formatter: () => {
            const s = data.overall_score;
            return `{score|${s >= 0 ? "+" : ""}${s.toFixed(3)}}\n{label|${data.overall_label.toUpperCase()}}`;
          },
          rich: {
            score: { fontSize: 20, fontFamily: "JetBrains Mono", color: "#FFA028", fontWeight: "bold" },
            label: { fontSize: 11, fontFamily: "JetBrains Mono", color: "#ACACAE", padding: [4, 0, 0, 0] },
          },
          offsetCenter: [0, "30%"],
        },
        data: [{ value: gaugeValue }],
      },
    ],
  };

  return (
    <div className="h-[220px] min-w-0 sm:h-[240px] lg:h-[260px]">
      <ReactECharts option={option} style={{ height: "100%", width: "100%" }} />
    </div>
  );
}
