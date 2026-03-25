"use client";

import { useMarketOverview } from "@/hooks/use-market-data";
import { cn } from "@/lib/utils";

export function StatsOverview() {
  const { data } = useMarketOverview();

  const stats = [
    {
      label: "ITEMS",
      value: String(data?.total_items_today ?? 0),
      color: "text-[#D7D7D7]",
    },
    {
      label: "SCORE",
      value: data ? `${data.overall_score >= 0 ? "+" : ""}${data.overall_score.toFixed(3)}` : "---",
      color: data
        ? data.overall_score > 0.05
          ? "text-[#4AF6C3]"
          : data.overall_score < -0.05
            ? "text-[#FF433D]"
            : "text-[#ACACAE]"
        : "text-[#ACACAE]",
    },
    {
      label: "ALERTS",
      value: String(data?.active_alerts ?? 0),
      color: data?.active_alerts ? "text-[#FF433D]" : "text-[#ACACAE]",
    },
    {
      label: "SOURCES",
      value: `${data?.sources_active ?? 0}/3`,
      color: "text-[#4AF6C3]",
    },
    {
      label: "STATUS",
      value: data?.overall_label?.toUpperCase() ?? "---",
      color: data
        ? data.overall_label === "bullish"
          ? "text-[#4AF6C3]"
          : data.overall_label === "bearish"
            ? "text-[#FF433D]"
            : "text-[#FFA028]"
        : "text-[#ACACAE]",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-2 font-mono text-[11px] sm:grid-cols-3 xl:grid-cols-5">
      {stats.map((stat) => (
        <div
          key={stat.label}
          className="rounded-lg border border-[#1E1E1E] bg-[#0A0A0A] px-3 py-2"
        >
          <div className="text-[10px] tracking-wide text-[#FFA028]">{stat.label}</div>
          <div className={cn("mt-1 truncate font-bold", stat.color)}>{stat.value}</div>
        </div>
      ))}
    </div>
  );
}
