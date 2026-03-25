"use client";

import { useCompanies } from "@/hooks/use-market-data";
import { cn } from "@/lib/utils";

export function SentimentTicker() {
  const { data } = useCompanies();

  if (!data?.companies.length) return null;

  const items = data.companies
    .filter((c) => c.avg_score !== null)
    .sort((a, b) => Math.abs(b.avg_score ?? 0) - Math.abs(a.avg_score ?? 0))
    .slice(0, 20);

  // Duplicate for infinite scroll illusion
  const doubled = [...items, ...items];

  return (
    <div className="overflow-hidden border-y border-[#1E1E1E] bg-[#0A0A0A] py-1">
      <div className="ticker-tape flex gap-6 whitespace-nowrap font-mono text-[11px]">
        {doubled.map((c, i) => {
          const score = c.avg_score ?? 0;
          const isPos = score > 0.05;
          const isNeg = score < -0.05;

          return (
            <span key={`${c.symbol}-${i}`} className="inline-flex items-center gap-1">
              <span className="font-bold text-[#D7D7D7]">{c.symbol}</span>
              <span
                className={cn(
                  isPos && "text-[#4AF6C3]",
                  isNeg && "text-[#FF433D]",
                  !isPos && !isNeg && "text-[#ACACAE]"
                )}
              >
                {score >= 0 ? "+" : ""}{score.toFixed(3)}
              </span>
            </span>
          );
        })}
      </div>
    </div>
  );
}
