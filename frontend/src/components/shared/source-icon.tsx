import { DollarSign, MessageSquare, Newspaper } from "lucide-react";
import { cn } from "@/lib/utils";

const SOURCE_CONFIG: Record<string, { icon: typeof MessageSquare; color: string; label: string }> = {
  reddit: { icon: MessageSquare, color: "text-orange-500", label: "Reddit" },
  news: { icon: Newspaper, color: "text-blue-500", label: "News" },
  stocktwits: { icon: DollarSign, color: "text-green-500", label: "StockTwits" },
};

export function SourceIcon({
  source,
  size = 16,
  showLabel = false,
  className,
}: {
  source: string;
  size?: number;
  showLabel?: boolean;
  className?: string;
}) {
  const config = SOURCE_CONFIG[source] || SOURCE_CONFIG.news;
  const Icon = config.icon;

  return (
    <span className={cn("inline-flex items-center gap-1", className)}>
      <Icon size={size} className={config.color} />
      {showLabel && <span className="text-xs text-muted-foreground">{config.label}</span>}
    </span>
  );
}
