"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search } from "lucide-react";
import { useCompanies, useIndustries } from "@/hooks/use-market-data";
import { cn } from "@/lib/utils";

interface SearchResult {
  type: "company" | "industry" | "page";
  label: string;
  sublabel: string;
  href: string;
  score?: number | null;
}

const PAGES: SearchResult[] = [
  { type: "page", label: "Dashboard", sublabel: "Market overview", href: "/" },
  { type: "page", label: "Live Feed", sublabel: "Sentiment stream", href: "/feed" },
  { type: "page", label: "AI Analyst", sublabel: "Briefings & signals", href: "/analyst" },
  { type: "page", label: "Entity Graph", sublabel: "Company network", href: "/graph" },
];

export function GoBar() {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const { data: companiesData } = useCompanies();
  const { data: industriesData } = useIndustries();

  // Build search results
  const results: SearchResult[] = [];
  const q = query.toLowerCase().trim();

  if (q.length > 0) {
    // Companies
    const companies = (companiesData?.companies ?? [])
      .filter(
        (c) =>
          c.symbol.toLowerCase().includes(q) ||
          c.name.toLowerCase().includes(q)
      )
      .slice(0, 5)
      .map((c) => ({
        type: "company" as const,
        label: c.symbol,
        sublabel: c.name,
        href: `/companies/${c.symbol.toLowerCase()}`,
        score: c.avg_score,
      }));
    results.push(...companies);

    // Industries
    const industries = (industriesData?.industries ?? [])
      .filter((i) => i.name.toLowerCase().includes(q) || i.slug.includes(q))
      .slice(0, 3)
      .map((i) => ({
        type: "industry" as const,
        label: i.name,
        sublabel: `${i.volume} items`,
        href: `/industries/${i.slug}`,
        score: i.avg_score,
      }));
    results.push(...industries);

    // Pages
    const pages = PAGES.filter(
      (p) => p.label.toLowerCase().includes(q) || p.sublabel.toLowerCase().includes(q)
    );
    results.push(...pages);
  }

  // Global keyboard shortcut
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        inputRef.current?.focus();
        setOpen(true);
      }
      if (e.key === "Escape") {
        setOpen(false);
        inputRef.current?.blur();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelected((s) => Math.min(s + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelected((s) => Math.max(s - 1, 0));
    } else if (e.key === "Enter" && results[selected]) {
      router.push(results[selected].href);
      setQuery("");
      setOpen(false);
      inputRef.current?.blur();
    }
  };

  return (
    <div className="relative min-w-0 flex-1">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setSelected(0); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onBlur={() => setTimeout(() => setOpen(false), 200)}
          onKeyDown={handleKeyDown}
          placeholder="Search companies, industries... (⌘K)"
          className="h-8 w-full min-w-0 rounded border border-border bg-[#0D1117] pl-9 pr-3 font-mono text-xs text-[#FFA028] placeholder:text-[#666666] focus:border-[#FFA028] focus:outline-none dark:bg-[#0D1117] sm:pr-11"
        />
        <kbd className="absolute right-3 top-1/2 hidden -translate-y-1/2 rounded border border-border px-1 font-mono text-[9px] text-muted-foreground sm:block">
          ⌘K
        </kbd>
      </div>

      {/* Dropdown */}
      {open && results.length > 0 && (
        <div className="absolute left-0 top-full z-50 mt-1 w-full max-w-full overflow-hidden rounded border border-[#333333] bg-[#141414] shadow-xl">
          {results.map((r, i) => (
            <button
              key={`${r.type}-${r.label}`}
              className={cn(
                "flex w-full min-w-0 items-center justify-between gap-2 px-3 py-2 text-left text-xs",
                i === selected ? "bg-[#1E2A3A]" : "hover:bg-[#1A1A1A]"
              )}
              onMouseDown={() => {
                router.push(r.href);
                setQuery("");
                setOpen(false);
              }}
              onMouseEnter={() => setSelected(i)}
            >
              <div className="flex min-w-0 items-center gap-2 sm:gap-3">
                <span className="hidden w-16 font-mono text-[10px] uppercase text-[#FFA028] sm:block">
                  {r.type === "company" ? "EQUITY" : r.type === "industry" ? "SECTOR" : "FUNC"}
                </span>
                <span className="shrink-0 font-mono font-bold text-[#D7D7D7]">{r.label}</span>
                <span className="truncate text-[#ACACAE]">{r.sublabel}</span>
              </div>
              {r.score !== undefined && r.score !== null && (
                <span
                  className={cn(
                    "shrink-0 font-mono text-[10px]",
                    r.score > 0 ? "text-[#4AF6C3]" : r.score < 0 ? "text-[#FF433D]" : "text-[#ACACAE]"
                  )}
                >
                  {r.score >= 0 ? "+" : ""}{r.score.toFixed(3)}
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
