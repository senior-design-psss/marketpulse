import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

const LABEL_STYLES: Record<string, string> = {
  very_positive: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  positive: "bg-green-500/20 text-green-400 border-green-500/30",
  neutral: "bg-slate-500/20 text-slate-400 border-slate-500/30",
  negative: "bg-red-500/20 text-red-400 border-red-500/30",
  very_negative: "bg-red-600/20 text-red-500 border-red-600/30",
  bullish: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  bearish: "bg-red-500/20 text-red-400 border-red-500/30",
};

export function SentimentBadge({
  label,
  score,
  className,
}: {
  label: string;
  score?: number;
  className?: string;
}) {
  const style = LABEL_STYLES[label] || LABEL_STYLES.neutral;

  return (
    <Badge variant="outline" className={cn(style, "font-mono text-xs", className)}>
      {score !== undefined ? `${score >= 0 ? "+" : ""}${score.toFixed(2)}` : label.replace("_", " ")}
    </Badge>
  );
}
