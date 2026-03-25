"use client";

import { Brain, AlertTriangle, TrendingUp, ArrowUpRight, ArrowDownRight } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useLatestBriefing, useBriefingsList } from "@/hooks/use-analyst";
import { useAnomalies, usePredictiveSignals } from "@/hooks/use-analytics";
import { cn } from "@/lib/utils";

export default function AnalystPage() {
  const { data: latest } = useLatestBriefing();
  const { data: history } = useBriefingsList(10);
  const { data: anomalies } = useAnomalies();
  const { data: predictive } = usePredictiveSignals();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Brain className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">AI Analyst</h1>
          <p className="text-muted-foreground">
            AI-generated market briefings, risk alerts, and predictive signals
          </p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {/* Main briefing */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>{latest?.briefing?.title ?? "Latest Market Briefing"}</span>
              {latest?.briefing?.generated_at && (
                <span className="text-xs font-normal text-muted-foreground">
                  {new Date(latest.briefing.generated_at).toLocaleString()}
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {latest?.briefing ? (
              <ScrollArea className="h-[500px] pr-4">
                <div className="prose prose-sm prose-invert max-w-none">
                  <ReactMarkdown>{latest.briefing.content}</ReactMarkdown>
                </div>
              </ScrollArea>
            ) : (
              <div className="flex h-[500px] flex-col items-center justify-center gap-3 text-muted-foreground">
                <Brain className="h-12 w-12 opacity-30" />
                <p>No briefings generated yet.</p>
                <p className="text-xs">Briefings are generated every 6 hours once data flows in.</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Risk Alerts */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Risk Alerts
              </CardTitle>
            </CardHeader>
            <CardContent>
              {anomalies?.alerts.length ? (
                <div className="space-y-3">
                  {anomalies.alerts.slice(0, 5).map((alert) => (
                    <div key={alert.id} className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-[10px]",
                            alert.severity === "critical" && "border-red-500 text-red-400",
                            alert.severity === "high" && "border-red-400 text-red-400",
                            alert.severity === "medium" && "border-amber-400 text-amber-400",
                            alert.severity === "low" && "border-yellow-400 text-yellow-400"
                          )}
                        >
                          {alert.severity}
                        </Badge>
                        <span className="text-xs font-medium">{alert.company_symbol}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{alert.title}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No active alerts</p>
              )}
            </CardContent>
          </Card>

          {/* Predictive Signals */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Predictive Signals
              </CardTitle>
            </CardHeader>
            <CardContent>
              {predictive?.signals.length ? (
                <div className="space-y-3">
                  {predictive.signals.slice(0, 5).map((sig) => (
                    <div key={sig.id} className="flex items-start gap-2">
                      {sig.direction === "bullish" ? (
                        <ArrowUpRight className="mt-0.5 h-4 w-4 shrink-0 text-emerald-400" />
                      ) : (
                        <ArrowDownRight className="mt-0.5 h-4 w-4 shrink-0 text-red-400" />
                      )}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold">{sig.symbol}</span>
                          <Badge variant="outline" className="text-[10px]">
                            {(sig.strength * 100).toFixed(0)}% strength
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{sig.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">
                  No signals yet — needs 14+ days of data
                </p>
              )}
            </CardContent>
          </Card>

          {/* Briefing History */}
          <Card>
            <CardHeader>
              <CardTitle>Briefing History</CardTitle>
            </CardHeader>
            <CardContent>
              {history?.briefings.length ? (
                <div className="space-y-2">
                  {history.briefings.map((b) => (
                    <div key={b.id} className="border-b border-border/50 pb-2 last:border-0">
                      <p className="text-xs font-medium">{b.title}</p>
                      <p className="text-[10px] text-muted-foreground">
                        {new Date(b.generated_at).toLocaleString()} &middot;{" "}
                        {b.items_analyzed} items
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No briefing history</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
