"use client";

import { AlertTriangle } from "lucide-react";
import { useAnomalies } from "@/hooks/use-analytics";
import { cn } from "@/lib/utils";

const SEVERITY_STYLES: Record<string, string> = {
  critical: "border-red-600 bg-red-950/50 text-red-400",
  high: "border-red-500 bg-red-950/30 text-red-400",
  medium: "border-amber-500 bg-amber-950/30 text-amber-400",
  low: "border-yellow-500 bg-yellow-950/20 text-yellow-400",
};

export function AnomalyBanner() {
  const { data } = useAnomalies();

  if (!data?.alerts.length) return null;

  return (
    <div className="space-y-2">
      {data.alerts.slice(0, 3).map((alert) => (
        <div
          key={alert.id}
          className={cn(
            "flex items-start gap-3 rounded-lg border px-4 py-3",
            SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.low
          )}
        >
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-mono text-sm font-bold">{alert.title}</span>
              <span className="rounded bg-current/10 px-1.5 py-0.5 text-[10px] uppercase">
                {alert.severity}
              </span>
            </div>
            <p className="mt-0.5 text-xs opacity-80">{alert.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
