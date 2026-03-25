"use client";

import Link from "next/link";
import { useSentimentFeed } from "@/hooks/use-market-data";
import { cn } from "@/lib/utils";

const SOURCE_ABBR: Record<string, string> = {
  reddit: "RDT",
  news: "NEWS",

};

export function NewsWire() {
  const { data, isLoading } = useSentimentFeed(1, "all", "all");

  if (isLoading || !data) {
    return (
      <div className="flex h-full items-center justify-center text-[11px] text-muted-foreground">
        Loading wire...
      </div>
    );
  }

  if (!data.items.length) {
    return (
      <div className="flex h-full items-center justify-center text-[11px] text-muted-foreground">
        No items yet
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto overflow-x-hidden font-mono text-[11px]">
      {data.items.map((item, idx) => {
        const time = new Date(item.scored_at).toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          hour12: false,
        });
        const source = SOURCE_ABBR[item.source] || item.source.toUpperCase();
        const score = item.ensemble_score;
        const isPositive = score > 0.15;
        const isNegative = score < -0.15;

        return (
          <div
            key={item.id}
            className={cn(
              "wire-item-enter flex min-w-0 items-baseline gap-2 border-b border-[#0A0A0A] px-2 py-1.5 hover:bg-[#141414]",
              idx === 0 && "bg-[#0A0A0A]"
            )}
          >
            <span className="shrink-0 text-[#666666]">{time}</span>
            <span className="shrink-0 text-[#FFA028]">{source}</span>
            {item.company_symbol && (
              <Link
                href={`/companies/${item.company_symbol.toLowerCase()}`}
                className="shrink-0 font-bold text-[#4DC7F9] hover:underline"
              >
                {item.company_symbol}
              </Link>
            )}
            <span
              className={cn(
                "min-w-0 flex-1 truncate",
                isPositive && "text-[#4AF6C3]",
                isNegative && "text-[#FF433D]",
                !isPositive && !isNegative && "text-[#D7D7D7]"
              )}
            >
              {item.title || item.body_excerpt}
            </span>
            <span
              className={cn(
                "shrink-0 tabular-nums",
                isPositive && "text-[#4AF6C3]",
                isNegative && "text-[#FF433D]",
                !isPositive && !isNegative && "text-[#ACACAE]"
              )}
            >
              {score >= 0 ? "+" : ""}{score.toFixed(2)}
            </span>
          </div>
        );
      })}
    </div>
  );
}
