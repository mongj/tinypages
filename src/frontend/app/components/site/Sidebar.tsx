"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { Flow } from "../../types/flows";
import { FlowSidebarItem } from "./FlowSidebarItem";

const CATEGORY_ORDER = [
  "browse",
  "auth",
  "account",
  "commerce",
  "buy",
  "support",
  "legal",
  "other",
];

const CATEGORY_LABELS: Record<string, string> = {
  browse: "Browsing",
  auth: "Authentication",
  account: "Account",
  commerce: "Commerce",
  buy: "Purchase",
  support: "Support",
  legal: "Legal",
  other: "Other",
};

function groupByCategory(flows: Flow[]): { category: string; flows: Flow[] }[] {
  const groups = new Map<string, Flow[]>();
  for (const flow of flows) {
    const cat = flow.intent_category || "other";
    if (!groups.has(cat)) groups.set(cat, []);
    groups.get(cat)!.push(flow);
  }

  return CATEGORY_ORDER.filter((cat) => groups.has(cat)).map((cat) => ({
    category: cat,
    flows: groups.get(cat)!,
  }));
}

export function Sidebar({
  flows,
  slug,
}: {
  flows: Flow[];
  slug: string;
}) {
  const pathname = usePathname();
  // Extract flowId from /site/:slug/:flowId
  const segments = pathname.split("/");
  const activeFlowId = segments.length >= 4 ? segments[3] : undefined;
  const isOverview = !activeFlowId;
  const groups = groupByCategory(flows);

  return (
    <aside className="w-64 shrink-0 border-r border-border bg-bg-sidebar overflow-y-auto h-[calc(100vh-3.5rem)] sticky top-14">
      <div className="py-4">
        <Link
          href={`/site/${slug}`}
          className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors border-l-2 mb-2 ${
            isOverview
              ? "border-accent-teal bg-accent-teal-light text-text-primary font-medium"
              : "border-transparent hover:bg-bg-secondary text-text-secondary hover:text-text-primary"
          }`}
        >
          Overview
        </Link>
        <div className="mx-4 border-t border-border mb-2" />
        {groups.map((group) => (
          <div key={group.category} className="mb-4">
            <h3 className="px-4 mb-1 text-xs font-medium uppercase tracking-wide text-text-muted">
              {CATEGORY_LABELS[group.category] ?? group.category}
            </h3>
            {group.flows.map((flow) => (
              <FlowSidebarItem
                key={flow.id}
                flow={flow}
                slug={slug}
                isActive={flow.id === activeFlowId}
              />
            ))}
          </div>
        ))}
      </div>
    </aside>
  );
}
