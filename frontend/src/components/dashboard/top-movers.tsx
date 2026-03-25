"use client";

import Link from "next/link";
import { TrendingDown, TrendingUp } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SentimentBadge } from "@/components/shared/sentiment-badge";
import { useCompanies } from "@/hooks/use-market-data";

export function TopMovers() {
  const { data, isLoading } = useCompanies();

  if (isLoading || !data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Top Movers</CardTitle>
        </CardHeader>
        <CardContent className="flex h-[300px] items-center justify-center text-muted-foreground">
          Loading...
        </CardContent>
      </Card>
    );
  }

  const withScores = data.companies.filter((c) => c.avg_score !== null);
  const sorted = [...withScores].sort(
    (a, b) => (b.avg_score ?? 0) - (a.avg_score ?? 0)
  );
  const topBullish = sorted.slice(0, 5);
  const topBearish = sorted.slice(-5).reverse();

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Movers</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h4 className="mb-2 flex items-center gap-1 text-xs font-medium text-emerald-400">
            <TrendingUp className="h-3 w-3" /> Most Bullish
          </h4>
          <div className="space-y-1">
            {topBullish.length === 0 && (
              <p className="text-xs text-muted-foreground">No data yet</p>
            )}
            {topBullish.map((c) => (
              <Link
                key={c.symbol}
                href={`/companies/${c.symbol.toLowerCase()}`}
                className="flex items-center justify-between rounded px-2 py-1 text-sm hover:bg-muted/50"
              >
                <span className="font-mono font-medium">{c.symbol}</span>
                <SentimentBadge label="positive" score={c.avg_score ?? 0} />
              </Link>
            ))}
          </div>
        </div>
        <div>
          <h4 className="mb-2 flex items-center gap-1 text-xs font-medium text-red-400">
            <TrendingDown className="h-3 w-3" /> Most Bearish
          </h4>
          <div className="space-y-1">
            {topBearish.length === 0 && (
              <p className="text-xs text-muted-foreground">No data yet</p>
            )}
            {topBearish.map((c) => (
              <Link
                key={c.symbol}
                href={`/companies/${c.symbol.toLowerCase()}`}
                className="flex items-center justify-between rounded px-2 py-1 text-sm hover:bg-muted/50"
              >
                <span className="font-mono font-medium">{c.symbol}</span>
                <SentimentBadge label="negative" score={c.avg_score ?? 0} />
              </Link>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
