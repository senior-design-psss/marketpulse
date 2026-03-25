"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SentimentBadge } from "@/components/shared/sentiment-badge";
import { useCompanies } from "@/hooks/use-market-data";
import { INDUSTRY_COLORS } from "@/lib/constants";

export default function CompaniesPage() {
  const { data, isLoading } = useCompanies();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Companies</h1>
        <p className="text-muted-foreground">
          Track sentiment across {data?.companies.length ?? "40+"}  companies
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>All Tracked Companies</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex h-[400px] items-center justify-center text-muted-foreground">
              Loading...
            </div>
          ) : (
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs text-muted-foreground">
                    <th className="px-3 py-2 font-medium">Symbol</th>
                    <th className="px-3 py-2 font-medium">Name</th>
                    <th className="px-3 py-2 font-medium">Industries</th>
                    <th className="px-3 py-2 font-medium text-right">Score</th>
                    <th className="px-3 py-2 font-medium text-right">Momentum</th>
                    <th className="px-3 py-2 font-medium text-right">Volume</th>
                    <th className="px-3 py-2 font-medium text-right">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.companies.map((comp) => (
                    <tr
                      key={comp.symbol}
                      className="border-b border-border/50 hover:bg-muted/50"
                    >
                      <td className="px-3 py-2">
                        <Link
                          href={`/companies/${comp.symbol.toLowerCase()}`}
                          className="font-mono font-bold text-primary hover:underline"
                        >
                          {comp.symbol}
                        </Link>
                      </td>
                      <td className="px-3 py-2 text-muted-foreground">
                        {comp.name}
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex gap-1">
                          {comp.industries.map((ind) => (
                            <Badge
                              key={ind}
                              variant="outline"
                              className="text-[10px]"
                              style={{
                                borderColor: INDUSTRY_COLORS[ind] ?? "#6b7280",
                                color: INDUSTRY_COLORS[ind] ?? "#6b7280",
                              }}
                            >
                              {ind}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="px-3 py-2 text-right">
                        {comp.avg_score !== null ? (
                          <SentimentBadge
                            label={
                              comp.avg_score > 0.2
                                ? "positive"
                                : comp.avg_score < -0.2
                                  ? "negative"
                                  : "neutral"
                            }
                            score={comp.avg_score}
                          />
                        ) : (
                          <span className="text-muted-foreground">--</span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-xs">
                        {comp.momentum !== null
                          ? `${comp.momentum >= 0 ? "+" : ""}${comp.momentum.toFixed(3)}`
                          : "--"}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-xs text-muted-foreground">
                        {comp.volume}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-xs">
                        {comp.confidence !== null
                          ? `${(comp.confidence * 100).toFixed(0)}%`
                          : "--"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
