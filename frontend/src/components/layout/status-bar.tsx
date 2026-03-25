"use client";

import { Activity, Clock, Database, Wifi } from "lucide-react";
import { useMarketOverview } from "@/hooks/use-market-data";

export function StatusBar() {
  const { data } = useMarketOverview();

  return (
    <footer className="flex h-6 shrink-0 items-center gap-4 border-t border-border bg-[#0D1117] px-4 font-mono text-[10px] text-muted-foreground dark:text-[#ACACAE]">
      <span className="flex items-center gap-1">
        <Wifi className="h-2.5 w-2.5 text-[#4AF6C3]" />
        {data?.sources_active ?? 0}/3 sources
      </span>
      <span className="flex items-center gap-1">
        <Database className="h-2.5 w-2.5" />
        {data?.total_items_today ?? 0} items today
      </span>
      <span className="flex items-center gap-1">
        <Activity className="h-2.5 w-2.5" />
        {data?.active_alerts ?? 0} alerts
      </span>
      <span className="ml-auto flex items-center gap-1">
        <Clock className="h-2.5 w-2.5" />
        MarketPulse AI v0.1
      </span>
    </footer>
  );
}
