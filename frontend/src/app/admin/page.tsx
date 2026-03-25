"use client";

import { useState } from "react";
import {
  Database,
  Download,
  Brain,
  BarChart3,
  DollarSign,
  TrendingUp,
  Radio,
  Newspaper,
  Loader2,
  CheckCircle2,
  XCircle,
  Settings,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function post(endpoint: string) {
  const res = await fetch(`${API}${endpoint}`, { method: "POST" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export default function AdminPage() {
  const queryClient = useQueryClient();
  const [log, setLog] = useState<{ text: string; type: "info" | "success" | "error" }[]>([]);
  const [running, setRunning] = useState<string | null>(null);

  const { data: status, refetch: refetchStatus } = useQuery({
    queryKey: ["admin-status"],
    queryFn: () => apiFetch<Record<string, number>>("/debug/status"),
    refetchInterval: 5_000,
  });

  const addLog = (text: string, type: "info" | "success" | "error" = "info") => {
    setLog((prev) => [{ text, type }, ...prev].slice(0, 50));
  };

  const runAction = async (name: string, endpoint: string) => {
    setRunning(name);
    addLog(`Starting: ${name}...`);
    try {
      const data = await post(endpoint);
      addLog(`${name}: ${JSON.stringify(data)}`, "success");
      queryClient.invalidateQueries();
      refetchStatus();
    } catch (err) {
      addLog(`${name} FAILED: ${err}`, "error");
    }
    setRunning(null);
  };

  const runFullPipeline = async () => {
    const steps = [
      { name: "Ingest News", endpoint: "/debug/ingest/news" },
      { name: "Process Sentiment", endpoint: "/debug/process" },
      { name: "Run Analytics", endpoint: "/debug/analytics" },
      { name: "Fetch Prices", endpoint: "/debug/prices" },
    ];
    for (const s of steps) {
      await runAction(s.name, s.endpoint);
    }
    addLog("Full pipeline complete!", "success");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Settings className="h-6 w-6 text-[#FFA028]" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Control Panel</h1>
          <p className="text-muted-foreground">
            Trigger ingestion, processing, and analytics
          </p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left column: Actions */}
        <div className="space-y-4 lg:col-span-2">
          {/* System Status */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Database className="h-4 w-4 text-[#FFA028]" />
                System Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              {status ? (
                <div className="grid grid-cols-2 gap-2 font-mono text-sm sm:grid-cols-4">
                  {Object.entries(status).map(([key, val]) => (
                    <div key={key} className="rounded bg-muted/50 px-3 py-2">
                      <div className="text-[10px] uppercase text-muted-foreground">{key}</div>
                      <div className="text-lg font-bold">{val}</div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Loading...</p>
              )}
            </CardContent>
          </Card>

          {/* Quick Pipeline */}
          <Card>
            <CardContent className="pt-6">
              <Button
                className="w-full bg-[#FFA028] text-black hover:bg-[#FFB04E] font-mono font-bold text-sm h-12"
                onClick={runFullPipeline}
                disabled={running !== null}
              >
                {running ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" />{running}</>
                ) : (
                  <><Zap className="mr-2 h-4 w-4" />Run Full Pipeline (Ingest → Process → Analytics → Prices)</>
                )}
              </Button>
            </CardContent>
          </Card>

          {/* Ingestion */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Download className="h-4 w-4 text-[#4AF6C3]" />
                Data Ingestion
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-5">
                <ActionBtn icon={Newspaper} label="News" desc="RSS feeds (16 sources)" onClick={() => runAction("Ingest News", "/debug/ingest/news")} running={running} />
                <ActionBtn icon={Radio} label="Reddit" desc="Public JSON (7 subs)" onClick={() => runAction("Ingest Reddit", "/debug/ingest/reddit")} running={running} />
                <ActionBtn icon={DollarSign} label="StockTwits" desc="20 tickers, pre-labeled" onClick={() => runAction("Ingest StockTwits", "/debug/ingest/stocktwits")} running={running} />
                <ActionBtn icon={Download} label="All Sources" desc="Everything" onClick={() => runAction("Ingest All", "/debug/ingest")} running={running} />
              </div>
            </CardContent>
          </Card>

          {/* Processing */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Brain className="h-4 w-4 text-[#0068FF]" />
                Processing &amp; Analytics
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                <ActionBtn icon={Brain} label="Sentiment" desc="FinBERT + LLM scoring" onClick={() => runAction("Process Sentiment", "/debug/process")} running={running} />
                <ActionBtn icon={BarChart3} label="Analytics" desc="Aggregates, momentum, anomalies" onClick={() => runAction("Run Analytics", "/debug/analytics")} running={running} />
                <ActionBtn icon={TrendingUp} label="Predictive" desc="Sentiment-price correlation" onClick={() => runAction("Predictive Signals", "/debug/predictive")} running={running} />
              </div>
            </CardContent>
          </Card>

          {/* Market + AI */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <DollarSign className="h-4 w-4 text-[#FEE334]" />
                Market Data &amp; AI
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2 sm:grid-cols-2">
                <ActionBtn icon={DollarSign} label="Fetch Prices" desc="30 days via Yahoo Finance" onClick={() => runAction("Fetch Prices", "/debug/prices")} running={running} />
                <ActionBtn icon={Brain} label="AI Briefing" desc="Generate market report" onClick={() => runAction("Generate Briefing", "/debug/briefing")} running={running} />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right column: Activity Log */}
        <Card className="lg:row-span-full">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-sm">
              Activity Log
              <Button variant="ghost" size="sm" onClick={() => setLog([])}>
                Clear
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[600px] overflow-auto space-y-1 font-mono text-[11px]">
              {log.length === 0 && (
                <p className="text-muted-foreground">No activity yet. Click a button to start.</p>
              )}
              {log.map((entry, i) => (
                <div
                  key={i}
                  className={
                    entry.type === "success"
                      ? "text-[#4AF6C3]"
                      : entry.type === "error"
                        ? "text-[#FF433D]"
                        : "text-muted-foreground"
                  }
                >
                  <span className="text-[#666666]">
                    {new Date().toLocaleTimeString("en-US", { hour12: false })}
                  </span>{" "}
                  {entry.type === "success" && <CheckCircle2 className="mr-1 inline h-3 w-3" />}
                  {entry.type === "error" && <XCircle className="mr-1 inline h-3 w-3" />}
                  {entry.text}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function ActionBtn({
  icon: Icon,
  label,
  desc,
  onClick,
  running,
}: {
  icon: typeof Database;
  label: string;
  desc: string;
  onClick: () => void;
  running: string | null;
}) {
  const isRunning = running !== null;
  return (
    <button
      onClick={onClick}
      disabled={isRunning}
      className="flex items-start gap-3 rounded-lg border border-border bg-card p-3 text-left transition-colors hover:bg-accent disabled:opacity-50"
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-[#FFA028]" />
      <div>
        <div className="text-sm font-bold">{label}</div>
        <div className="text-[11px] text-muted-foreground">{desc}</div>
      </div>
    </button>
  );
}
