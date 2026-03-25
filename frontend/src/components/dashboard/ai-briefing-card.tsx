"use client";

import Link from "next/link";
import { Brain } from "lucide-react";
import { useLatestBriefing } from "@/hooks/use-analyst";

export function AIBriefingCard() {
  const { data } = useLatestBriefing();
  const briefing = data?.briefing;

  return (
    <div className="h-full min-w-0 p-3 font-mono text-[11px]">
      {briefing ? (
        <div className="space-y-2">
          <p className="line-clamp-2 text-xs font-bold text-[#FFA028]">{briefing.title}</p>
          <p className="line-clamp-7 leading-relaxed text-[#D7D7D7]">
            {briefing.content.replace(/[#*_\[\]]/g, "").slice(0, 400)}
          </p>
          <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
            <span className="text-[10px] text-[#666666]">
              {new Date(briefing.generated_at).toLocaleTimeString("en-US", { hour12: false })}
              {" "}&middot; {briefing.items_analyzed} items
            </span>
            <Link
              href="/analyst"
              className="shrink-0 text-[10px] text-[#4DC7F9] hover:underline"
            >
              FULL REPORT &gt;
            </Link>
          </div>
        </div>
      ) : (
        <div className="flex h-full flex-col items-center justify-center gap-2 text-[#666666]">
          <Brain className="h-6 w-6 opacity-30" />
          <p>Awaiting first briefing</p>
          <p className="text-[9px]">Generated every 6 hours</p>
        </div>
      )}
    </div>
  );
}
