"use client";

import Link from "next/link";
import { useCompanies } from "@/hooks/use-market-data";
import { cn } from "@/lib/utils";

export function QuoteBoard() {
  const { data, isLoading } = useCompanies();

  if (isLoading || !data) {
    return (
      <div className="flex h-full items-center justify-center text-[11px] text-muted-foreground">
        Loading...
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto overflow-x-hidden">
      <table className="bb-dense w-full min-w-0">
        <thead>
          <tr className="border-b border-[#1E1E1E] text-left text-[#FFA028]">
            <th className="sticky top-0 z-10 bg-[#0D1117] px-2 py-1">Ticker</th>
            <th className="sticky top-0 z-10 bg-[#0D1117] px-2 py-1 text-right">Price</th>
            <th className="sticky top-0 z-10 bg-[#0D1117] px-2 py-1 text-right hidden sm:table-cell">Chg%</th>
            <th className="sticky top-0 z-10 bg-[#0D1117] px-2 py-1 text-right">Sent.</th>
            <th className="sticky top-0 z-10 bg-[#0D1117] px-2 py-1 text-right hidden md:table-cell">Mom.</th>
            <th className="sticky top-0 z-10 bg-[#0D1117] px-2 py-1 text-right hidden lg:table-cell">Vol</th>
            <th className="sticky top-0 z-10 bg-[#0D1117] px-2 py-1 text-center hidden md:table-cell">Signal</th>
          </tr>
        </thead>
        <tbody>
          {data.companies
            .sort((a, b) => (b.volume || 0) - (a.volume || 0))
            .map((c) => {
              const score = c.avg_score;
              const sentPos = score !== null && score > 0.05;
              const sentNeg = score !== null && score < -0.05;
              const pricePos = c.price_change !== null && c.price_change > 0;
              const priceNeg = c.price_change !== null && c.price_change < 0;

              let signal = "—";
              let signalColor = "text-[#666666]";
              if (score !== null && c.price_change !== null) {
                const agree =
                  (score > 0.05 && c.price_change > 0) ||
                  (score < -0.05 && c.price_change < 0);
                const disagree =
                  (score > 0.05 && c.price_change < -0.5) ||
                  (score < -0.05 && c.price_change > 0.5);
                if (agree) {
                  signal = "ALIGN";
                  signalColor = "text-[#4AF6C3]";
                } else if (disagree) {
                  signal = "DIVERGE";
                  signalColor = "text-[#FEE334]";
                } else {
                  signal = "NTRL";
                }
              }

              return (
                <tr
                  key={c.symbol}
                  className="border-b border-[#0A0A0A] hover:bg-[#141414]"
                >
                  <td className="max-w-0 px-2 py-0.5">
                    <Link
                      href={`/companies/${c.symbol.toLowerCase()}`}
                      className="block truncate font-bold text-[#D7D7D7] hover:text-[#FFA028]"
                    >
                      {c.symbol}
                    </Link>
                  </td>
                  <td className="px-2 py-0.5 text-right text-[#D7D7D7]">
                    {c.price !== null ? `$${c.price.toFixed(2)}` : "—"}
                  </td>
                  <td
                    className={cn(
                      "px-2 py-0.5 text-right hidden sm:table-cell",
                      pricePos && "text-[#4AF6C3]",
                      priceNeg && "text-[#FF433D]",
                      !pricePos && !priceNeg && "text-[#ACACAE]"
                    )}
                  >
                    {c.price_change !== null
                      ? `${c.price_change >= 0 ? "+" : ""}${c.price_change.toFixed(1)}%`
                      : "—"}
                  </td>
                  <td
                    className={cn(
                      "px-2 py-0.5 text-right",
                      sentPos && "text-[#4AF6C3]",
                      sentNeg && "text-[#FF433D]",
                      !sentPos && !sentNeg && "text-[#ACACAE]"
                    )}
                  >
                    {score !== null
                      ? `${score >= 0 ? "+" : ""}${score.toFixed(2)}`
                      : "—"}
                  </td>
                  <td
                    className={cn(
                      "px-2 py-0.5 text-right hidden md:table-cell",
                      c.momentum !== null && c.momentum > 0 && "text-[#4AF6C3]",
                      c.momentum !== null && c.momentum < 0 && "text-[#FF433D]",
                      (c.momentum === null || c.momentum === 0) && "text-[#ACACAE]"
                    )}
                  >
                    {c.momentum !== null
                      ? `${c.momentum >= 0 ? "+" : ""}${c.momentum.toFixed(3)}`
                      : "—"}
                  </td>
                  <td className="px-2 py-0.5 text-right text-[#ACACAE] hidden lg:table-cell">
                    {c.volume || 0}
                  </td>
                  <td
                    className={cn(
                      "px-2 py-0.5 text-center text-[10px] hidden md:table-cell",
                      signalColor
                    )}
                  >
                    {signal}
                  </td>
                </tr>
              );
            })}
        </tbody>
      </table>
    </div>
  );
}
