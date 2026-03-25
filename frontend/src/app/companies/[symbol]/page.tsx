"use client";

import { use } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Brain } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { SentimentBadge } from "@/components/shared/sentiment-badge";
import { SentimentTimeseries } from "@/components/charts/sentiment-timeseries";
import { SourceBreakdown } from "@/components/charts/source-breakdown";
import { PriceSentimentOverlay } from "@/components/charts/price-sentiment-overlay";
import { SourceArticles } from "@/components/company/source-articles";
import {
  useCompanyDetail,
  useCompanyTimeseries,
  useCompanyPrices,
} from "@/hooks/use-market-data";
import { useCompanySummary } from "@/hooks/use-analyst";
import { cn } from "@/lib/utils";

export default function CompanyProfilePage({
  params,
}: {
  params: Promise<{ symbol: string }>;
}) {
  const { symbol } = use(params);
  const { data: company, isLoading } = useCompanyDetail(symbol);
  const { data: timeseries } = useCompanyTimeseries(symbol, "7d");
  const { data: prices } = useCompanyPrices(symbol, 30);
  const { data: summary } = useCompanySummary(symbol);

  if (isLoading || !company) {
    return (
      <div className="flex h-64 items-center justify-center text-muted-foreground">
        Loading {symbol.toUpperCase()}...
      </div>
    );
  }

  const priceUp = company.price_change !== null && company.price_change > 0;
  const priceDown = company.price_change !== null && company.price_change < 0;

  return (
    <div className="space-y-6">
      {/* Header with price */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">{company.symbol}</h1>
            <p className="text-muted-foreground">{company.name}</p>
          </div>
          {company.avg_score !== null && (
            <SentimentBadge
              label={company.avg_score > 0.2 ? "positive" : company.avg_score < -0.2 ? "negative" : "neutral"}
              score={company.avg_score}
              className="text-sm"
            />
          )}
        </div>
        {company.price !== null && (
          <div className="text-right">
            <div className="font-mono text-2xl font-bold">${company.price.toFixed(2)}</div>
            <div
              className={cn(
                "font-mono text-sm",
                priceUp && "text-[#4AF6C3]",
                priceDown && "text-[#FF433D]",
                !priceUp && !priceDown && "text-muted-foreground"
              )}
            >
              {company.price_change !== null
                ? `${company.price_change >= 0 ? "+" : ""}${company.price_change.toFixed(2)}%`
                : ""}
              {company.price_date && (
                <span className="ml-2 text-xs text-muted-foreground">{company.price_date}</span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Key metrics */}
      <div className="grid gap-4 md:grid-cols-5">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">Sentiment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-mono text-xl font-bold">
              {company.avg_score !== null
                ? `${company.avg_score >= 0 ? "+" : ""}${company.avg_score.toFixed(3)}`
                : "N/A"}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">Price</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-mono text-xl font-bold">
              {company.price !== null ? `$${company.price.toFixed(2)}` : "N/A"}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">Volume</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-mono text-xl font-bold">{company.volume}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">Momentum</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-mono text-xl font-bold">
              {company.momentum !== null
                ? `${company.momentum >= 0 ? "+" : ""}${company.momentum.toFixed(3)}`
                : "N/A"}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">Confidence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="font-mono text-xl font-bold">
              {company.confidence !== null ? `${(company.confidence * 100).toFixed(0)}%` : "N/A"}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Price vs Sentiment overlay — full width */}
      <PriceSentimentOverlay
        prices={prices?.prices ?? []}
        sentiment={timeseries?.data ?? []}
        symbol={company.symbol}
      />

      {/* Sentiment timeline + Source breakdown */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <SentimentTimeseries data={timeseries?.data ?? []} title="Sentiment Timeline (7d)" />
        </div>
        <SourceBreakdown
          data={{
            reddit_avg: company.reddit_avg,
            reddit_volume: company.reddit_volume,
            news_avg: company.news_avg,
            news_volume: company.news_volume,
            stocktwits_avg: company.stocktwits_avg,
            stocktwits_volume: company.stocktwits_volume,
          }}
        />
      </div>

      {/* AI Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-4 w-4" />
            AI Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          {summary?.summary && !summary.summary.includes("No summary") ? (
            <div className="prose prose-sm prose-invert max-w-none">
              <ReactMarkdown>{summary.summary}</ReactMarkdown>
              {summary.generated_at && (
                <p className="mt-2 text-[10px] text-muted-foreground">
                  Generated {new Date(summary.generated_at).toLocaleString()}
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No AI summary yet. Generate one from the Control Panel or wait for the scheduled run.
            </p>
          )}
        </CardContent>
      </Card>

      {/* Source Articles — the actual evidence */}
      <SourceArticles symbol={symbol} />
    </div>
  );
}
