"use client";

import { useState } from "react";
import Link from "next/link";
import { Radio, ChevronLeft, ChevronRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SentimentBadge } from "@/components/shared/sentiment-badge";
import { SourceIcon } from "@/components/shared/source-icon";
import { useSentimentFeed } from "@/hooks/use-market-data";
import type { Source } from "@/types/api";

const SOURCES: { label: string; value: Source | "all" }[] = [
  { label: "All", value: "all" },
  { label: "Reddit", value: "reddit" },
  { label: "News", value: "news" },
  { label: "StockTwits", value: "stocktwits" },
];

const LABELS = [
  { label: "All", value: "all" },
  { label: "Bullish", value: "positive" },
  { label: "Bearish", value: "negative" },
  { label: "Neutral", value: "neutral" },
];

export default function FeedPage() {
  const [page, setPage] = useState(1);
  const [source, setSource] = useState<Source | "all">("all");
  const [label, setLabel] = useState("all");

  const { data, isLoading } = useSentimentFeed(page, source, label);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Radio className="h-6 w-6 text-primary" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Live Feed</h1>
          <p className="text-muted-foreground">
            Real-time sentiment stream &middot; {data?.total ?? 0} total items
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="flex gap-1">
          <span className="mr-1 self-center text-xs text-muted-foreground">Source:</span>
          {SOURCES.map((s) => (
            <Badge
              key={s.value}
              variant={source === s.value ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => { setSource(s.value); setPage(1); }}
            >
              {s.label}
            </Badge>
          ))}
        </div>
        <div className="flex gap-1">
          <span className="mr-1 self-center text-xs text-muted-foreground">Sentiment:</span>
          {LABELS.map((l) => (
            <Badge
              key={l.value}
              variant={label === l.value ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => { setLabel(l.value); setPage(1); }}
            >
              {l.label}
            </Badge>
          ))}
        </div>
      </div>

      {/* Feed */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex h-[500px] items-center justify-center text-muted-foreground">
              Loading feed...
            </div>
          ) : !data?.items.length ? (
            <div className="flex h-[500px] items-center justify-center text-muted-foreground">
              No items match your filters
            </div>
          ) : (
            <div className="divide-y">
              {data.items.map((item) => (
                <div
                  key={item.id}
                  className="flex gap-3 px-4 py-3 transition-colors hover:bg-muted/30"
                >
                  <SourceIcon source={item.source} size={18} className="mt-1 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      {item.company_symbol && (
                        <Link
                          href={`/companies/${item.company_symbol.toLowerCase()}`}
                          className="font-mono text-sm font-bold text-primary hover:underline"
                        >
                          {item.company_symbol}
                        </Link>
                      )}
                      <SentimentBadge label={item.ensemble_label} score={item.ensemble_score} />
                      <span className="text-[10px] text-muted-foreground">
                        {new Date(item.scored_at).toLocaleTimeString()}
                      </span>
                    </div>
                    {item.title && (
                      <p className="mt-0.5 text-sm font-medium">{item.title}</p>
                    )}
                    <p className="mt-0.5 text-xs text-muted-foreground line-clamp-2">
                      {item.body_excerpt}
                    </p>
                    {item.llm_reasoning && (
                      <p className="mt-1 text-[10px] italic text-muted-foreground">
                        AI: {item.llm_reasoning}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {data && data.total > 20 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Page {page} of {Math.ceil(data.total / 20)}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              <ChevronLeft className="h-4 w-4" /> Prev
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={page * 20 >= data.total}
            >
              Next <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
