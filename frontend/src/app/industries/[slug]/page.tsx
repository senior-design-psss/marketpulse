"use client";

import { use } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SentimentBadge } from "@/components/shared/sentiment-badge";
import { SentimentRadarChart } from "@/components/charts/radar-chart";
import { useIndustryHeatmap, useIndustryRadar } from "@/hooks/use-market-data";

export default function IndustryDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const { data: heatmapData, isLoading: heatmapLoading } = useIndustryHeatmap(slug);
  const { data: radarData } = useIndustryRadar(slug);

  const industryName = heatmapData?.industry.name ?? slug.replace("-", " ");

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold capitalize tracking-tight">
          {industryName}
        </h1>
        <p className="text-muted-foreground">
          Deep dive into sector sentiment
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <SentimentRadarChart
          companies={radarData?.companies ?? []}
          title="Multi-Source Comparison"
        />

        <Card>
          <CardHeader>
            <CardTitle>Companies in Sector</CardTitle>
          </CardHeader>
          <CardContent>
            {heatmapLoading ? (
              <div className="flex h-[360px] items-center justify-center text-muted-foreground">
                Loading...
              </div>
            ) : !heatmapData?.companies.length ? (
              <div className="flex h-[360px] items-center justify-center text-muted-foreground">
                No data yet
              </div>
            ) : (
              <div className="max-h-[360px] overflow-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left text-xs text-muted-foreground">
                      <th className="px-2 py-2 font-medium">Symbol</th>
                      <th className="px-2 py-2 font-medium">Name</th>
                      <th className="px-2 py-2 font-medium text-right">Score</th>
                      <th className="px-2 py-2 font-medium text-right">Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {heatmapData.companies
                      .sort((a, b) => b.score - a.score)
                      .map((comp) => (
                        <tr
                          key={comp.symbol}
                          className="border-b border-border/50 hover:bg-muted/50"
                        >
                          <td className="px-2 py-2">
                            <Link
                              href={`/companies/${comp.symbol.toLowerCase()}`}
                              className="font-mono font-medium text-primary hover:underline"
                            >
                              {comp.symbol}
                            </Link>
                          </td>
                          <td className="px-2 py-2 text-muted-foreground">
                            {comp.name}
                          </td>
                          <td className="px-2 py-2 text-right">
                            <SentimentBadge
                              label={
                                comp.score > 0.2
                                  ? "positive"
                                  : comp.score < -0.2
                                    ? "negative"
                                    : "neutral"
                              }
                              score={comp.score}
                            />
                          </td>
                          <td className="px-2 py-2 text-right font-mono text-muted-foreground">
                            {comp.volume}
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
    </div>
  );
}
