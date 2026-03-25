"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { IndustryHeatmap } from "@/components/dashboard/industry-heatmap";
import { MarketPulseGauge } from "@/components/dashboard/market-pulse-gauge";
import { AnomalyBanner } from "@/components/dashboard/anomaly-banner";
import { AIBriefingCard } from "@/components/dashboard/ai-briefing-card";
import { QuoteBoard } from "@/components/dashboard/quote-board";
import { NewsWire } from "@/components/dashboard/news-wire";
import { SentimentTicker } from "@/components/dashboard/sentiment-ticker";
import { StatsOverview } from "@/components/dashboard/stats-overview";

export default function DashboardPage() {
  return (
    <div className="mx-auto flex w-full max-w-7xl min-w-0 flex-col gap-3 lg:gap-4">
      {/* Ticker tape */}
      <div className="-mx-4 -mt-4 sm:mx-0 sm:mt-0">
        <SentimentTicker />
      </div>

      {/* Stats bar */}
      <StatsOverview />

      {/* Anomaly alerts */}
      <AnomalyBanner />

      {/* Market Map — full width */}
      <Card>
        <CardHeader className="py-2">
          <CardTitle className="font-mono text-xs uppercase tracking-wider text-[#FFA028]">
            MMAP — Industry Sentiment Map
          </CardTitle>
        </CardHeader>
        <CardContent className="min-w-0 p-2">
          <IndustryHeatmap />
        </CardContent>
      </Card>

      {/* Gauge + AI Briefing */}
      <div className="grid min-w-0 gap-3 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)] xl:gap-4">
        <Card className="min-w-0">
          <CardHeader className="py-2">
            <CardTitle className="font-mono text-xs uppercase tracking-wider text-[#FFA028]">
              PULSE — Market Sentiment
            </CardTitle>
          </CardHeader>
          <CardContent className="min-w-0 p-2">
            <MarketPulseGauge />
          </CardContent>
        </Card>
        <Card className="min-w-0">
          <CardHeader className="py-2">
            <CardTitle className="font-mono text-xs uppercase tracking-wider text-[#FFA028]">
              AI — Market Briefing
            </CardTitle>
          </CardHeader>
          <CardContent className="min-w-0 p-2">
            <AIBriefingCard />
          </CardContent>
        </Card>
      </div>

      {/* Monitor + Wire */}
      <div className="grid min-w-0 gap-3 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,0.85fr)] xl:gap-4">
        <Card className="min-w-0">
          <CardHeader className="py-2">
            <CardTitle className="font-mono text-xs uppercase tracking-wider text-[#FFA028]">
              MONITOR — Watchlist &amp; Prices
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[380px] min-w-0 overflow-auto p-0 sm:h-[420px]">
            <QuoteBoard />
          </CardContent>
        </Card>

        <Card className="min-w-0">
          <CardHeader className="py-2">
            <CardTitle className="font-mono text-xs uppercase tracking-wider text-[#FFA028]">
              TOP — News Wire
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[340px] min-w-0 overflow-auto p-0 sm:h-[420px]">
            <NewsWire />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
