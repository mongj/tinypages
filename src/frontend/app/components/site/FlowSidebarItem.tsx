"use client";

import Link from "next/link";
import type { Flow } from "../../types/flows";

function confidenceColor(confidence: number): string {
  if (confidence >= 0.9) return "bg-success";
  if (confidence >= 0.7) return "bg-warning";
  return "bg-danger";
}

export function FlowSidebarItem({
  flow,
  slug,
  isActive,
}: {
  flow: Flow;
  slug: string;
  isActive: boolean;
}) {
  return (
    <Link
      href={`/site/${slug}/${flow.id}`}
      className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors border-l-2 ${
        isActive
          ? "border-accent-teal bg-accent-teal-light text-text-primary font-medium"
          : "border-transparent hover:bg-bg-secondary text-text-secondary hover:text-text-primary"
      }`}
    >
      <span
        className={`w-2 h-2 rounded-full shrink-0 ${confidenceColor(flow.confidence)}`}
      />
      <span className="truncate">{flow.name}</span>
    </Link>
  );
}
