"use client";

import { Share2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EntityGraphViz } from "@/components/graph/entity-graph";
import { useEntityGraph } from "@/hooks/use-graph";

export default function GraphPage() {
  const { data, isLoading } = useEntityGraph();

  const industryCount = data?.nodes.filter((n) => n.node_type === "industry").length ?? 0;
  const companyCount = data?.nodes.filter((n) => n.node_type === "company").length ?? 0;
  const coMentions = data?.edges.filter((e) => e.edge_type === "co_mention").length ?? 0;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Share2 className="h-6 w-6 text-[#FFA028]" />
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Entity Graph</h1>
          <p className="text-muted-foreground">
            {industryCount} industries, {companyCount} companies, {coMentions} co-mention links
          </p>
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-x-6 gap-y-2 rounded border border-[#1E1E1E] bg-[#0A0A0A] p-3 font-mono text-[11px]">
        <div className="flex items-center gap-2">
          <span className="inline-block h-4 w-4 rounded-full border-2 border-[#FFA028] bg-[#3B82F6]" />
          <span className="text-[#ACACAE]">Industry hub (large, colored by sector)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full bg-[#66BB6A]" />
          <span className="text-[#ACACAE]">Company positive</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full bg-[#475569]" />
          <span className="text-[#ACACAE]">Company neutral</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full bg-[#E57373]" />
          <span className="text-[#ACACAE]">Company negative</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-0.5 w-4 bg-[#333333]" style={{ borderTop: "1.5px dashed #333" }} />
          <span className="text-[#ACACAE]">Industry → Company</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-block h-0.5 w-4 bg-[#FFA028]" />
          <span className="text-[#ACACAE]">Co-mention link</span>
        </div>
      </div>

      <Card>
        <CardHeader className="py-2">
          <CardTitle className="font-mono text-xs uppercase tracking-wider text-[#FFA028]">
            GRAPH — Industry &amp; Company Network
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[650px] p-0">
          {isLoading ? (
            <div className="flex h-full items-center justify-center text-muted-foreground">
              Loading graph...
            </div>
          ) : (
            <EntityGraphViz nodes={data?.nodes ?? []} edges={data?.edges ?? []} />
          )}
        </CardContent>
      </Card>

      <p className="font-mono text-[10px] text-muted-foreground">
        Click industry hubs → industry page. Click companies → company profile. Drag nodes to rearrange. Scroll to zoom. Hover for sentiment details.
      </p>
    </div>
  );
}
