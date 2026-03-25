"use client";

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SentimentBadge } from "@/components/shared/sentiment-badge";
import { useIndustries } from "@/hooks/use-market-data";

export default function IndustriesPage() {
  const { data, isLoading } = useIndustries();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Industries</h1>
        <p className="text-muted-foreground">
          Sector-level sentiment analysis across all tracked industries
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {isLoading
          ? Array.from({ length: 10 }).map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardHeader>
                  <div className="h-5 w-32 rounded bg-muted" />
                </CardHeader>
                <CardContent>
                  <div className="h-4 w-48 rounded bg-muted" />
                </CardContent>
              </Card>
            ))
          : data?.industries.map((industry) => (
              <Link key={industry.slug} href={`/industries/${industry.slug}`}>
                <Card className="cursor-pointer transition-colors hover:bg-muted/50">
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="text-lg">{industry.name}</CardTitle>
                    <div
                      className="h-3 w-3 rounded-full"
                      style={{ backgroundColor: industry.display_color ?? "#6b7280" }}
                    />
                  </CardHeader>
                  <CardContent className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      {industry.volume} items scored
                    </div>
                    {industry.avg_score !== null && (
                      <SentimentBadge
                        label={
                          industry.avg_score > 0.2
                            ? "positive"
                            : industry.avg_score < -0.2
                              ? "negative"
                              : "neutral"
                        }
                        score={industry.avg_score}
                      />
                    )}
                  </CardContent>
                </Card>
              </Link>
            ))}
      </div>
    </div>
  );
}
