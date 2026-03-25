"use client";

import { useState } from "react";
import { ExternalLink, ChevronLeft, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { SentimentBadge } from "@/components/shared/sentiment-badge";
import { SourceIcon } from "@/components/shared/source-icon";
import { useCompanySources } from "@/hooks/use-market-data";
import { cn } from "@/lib/utils";

export function SourceArticles({ symbol }: { symbol: string }) {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useCompanySources(symbol, page);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Source Articles & Posts</span>
          {data && (
            <Badge variant="outline" className="font-mono text-xs">
              {data.total} total
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
            Loading sources...
          </div>
        ) : !data?.items.length ? (
          <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
            No source articles found for {symbol}. Try ingesting data from the Control Panel.
          </div>
        ) : (
          <div className="space-y-0 divide-y divide-border/50">
            {data.items.map((article) => {
              const score = article.ensemble_score;
              const isPositive = score > 0.1;
              const isNegative = score < -0.1;

              return (
                <div key={article.id} className="py-3 first:pt-0 last:pb-0">
                  <div className="flex items-start gap-3">
                    <SourceIcon source={article.source} size={16} className="mt-1 shrink-0" />
                    <div className="min-w-0 flex-1">
                      {/* Header row */}
                      <div className="flex items-center gap-2 flex-wrap">
                        <SentimentBadge label={article.ensemble_label} score={score} />
                        <Badge variant="outline" className="text-[10px]">
                          {article.source}
                          {article.subreddit && ` · r/${article.subreddit}`}
                        </Badge>
                        <span className="text-[10px] text-muted-foreground">
                          {article.published_at
                            ? new Date(article.published_at).toLocaleString()
                            : ""}
                        </span>
                        {article.url && (
                          <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-muted-foreground hover:text-primary"
                          >
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>

                      {/* Title */}
                      {article.title && (
                        <p className="mt-1 text-sm font-medium">{article.title}</p>
                      )}

                      {/* Body excerpt */}
                      <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                        {article.body}
                      </p>

                      {/* Score details */}
                      <div className="mt-2 flex flex-wrap gap-3 font-mono text-[10px] text-muted-foreground">
                        <span>
                          Ensemble:{" "}
                          <span className={cn(isPositive && "text-[#4AF6C3]", isNegative && "text-[#FF433D]")}>
                            {score >= 0 ? "+" : ""}{score.toFixed(3)}
                          </span>
                        </span>
                        {article.finbert_label && (
                          <span>
                            FinBERT: {article.finbert_label}
                            {article.finbert_positive !== null && (
                              <> ({(article.finbert_positive * 100).toFixed(0)}% pos)</>
                            )}
                          </span>
                        )}
                        {article.llm_score !== null && (
                          <span>LLM: {article.llm_score >= 0 ? "+" : ""}{article.llm_score.toFixed(2)}</span>
                        )}
                        <span>Conf: {(article.ensemble_confidence * 100).toFixed(0)}%</span>
                      </div>

                      {/* LLM reasoning */}
                      {article.llm_reasoning && (
                        <p className="mt-1 rounded bg-muted/50 px-2 py-1 text-[11px] italic text-muted-foreground">
                          AI: {article.llm_reasoning}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination */}
        {data && data.total > 20 && (
          <div className="mt-4 flex items-center justify-between border-t pt-3">
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
                <ChevronLeft className="h-3 w-3" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage((p) => p + 1)}
                disabled={page * 20 >= data.total}
              >
                <ChevronRight className="h-3 w-3" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
