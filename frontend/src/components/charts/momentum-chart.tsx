"use client";

import Link from "next/link";
import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useMomentum } from "@/hooks/use-analytics";
import { cn } from "@/lib/utils";

export function MomentumChart() {
  const { data, isLoading } = useMomentum();

  if (isLoading || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Sentiment Momentum</CardTitle>
        </CardHeader>
        <CardContent className="flex h-[300px] items-center justify-center text-muted-foreground">
          Loading...
        </CardContent>
      </Card>
    );
  }

  if (!data.movers.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Sentiment Momentum</CardTitle>
        </CardHeader>
        <CardContent className="flex h-[300px] items-center justify-center text-muted-foreground">
          No momentum data yet — analytics pipeline needs to run
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Sentiment Momentum</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {data.movers.slice(0, 10).map((item) => {
            const isPositive = item.momentum > 0.001;
            const isNegative = item.momentum < -0.001;

            return (
              <Link
                key={item.symbol}
                href={`/companies/${item.symbol.toLowerCase()}`}
                className="flex items-center gap-3 rounded px-2 py-1.5 text-sm hover:bg-muted/50"
              >
                <span className="w-14 font-mono font-bold">{item.symbol}</span>

                {/* Momentum bar */}
                <div className="flex flex-1 items-center gap-2">
                  <div className="relative h-2 flex-1 overflow-hidden rounded bg-muted">
                    <div
                      className={cn(
                        "absolute top-0 h-full rounded",
                        isPositive ? "bg-emerald-500" : isNegative ? "bg-red-500" : "bg-slate-500"
                      )}
                      style={{
                        width: `${Math.min(Math.abs(item.momentum) * 500, 100)}%`,
                        left: isNegative ? undefined : "50%",
                        right: isNegative ? "50%" : undefined,
                      }}
                    />
                    <div className="absolute left-1/2 top-0 h-full w-px bg-border" />
                  </div>
                </div>

                <span
                  className={cn(
                    "flex w-20 items-center justify-end gap-1 font-mono text-xs",
                    isPositive ? "text-emerald-400" : isNegative ? "text-red-400" : "text-muted-foreground"
                  )}
                >
                  {isPositive ? <ArrowUp className="h-3 w-3" /> : isNegative ? <ArrowDown className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
                  {item.momentum >= 0 ? "+" : ""}{item.momentum.toFixed(4)}
                </span>
              </Link>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
