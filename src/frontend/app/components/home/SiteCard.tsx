import Link from "next/link";
import type { SiteMeta } from "../../types/flows";

export function SiteCard({ meta }: { meta: SiteMeta }) {
  return (
    <Link
      href={`/site/${meta.slug}`}
      className="group block rounded-lg border border-border bg-bg p-5 hover:border-accent-teal/40 hover:shadow-sm transition-all"
    >
      <div className="flex items-center gap-3 mb-3">
        <img
          src={`https://www.google.com/s2/favicons?domain=${meta.host}&sz=32`}
          alt=""
          className="w-5 h-5"
        />
        <h3 className="font-semibold text-text-primary group-hover:text-accent-teal transition-colors">
          {meta.name}
        </h3>
      </div>
      {meta.one_line_summary ? (
        <p className="text-sm text-text-secondary mb-3 line-clamp-2">
          {meta.one_line_summary}
        </p>
      ) : (
        <p className="text-sm text-text-muted mb-3">{meta.host}</p>
      )}
      <div className="flex items-center gap-3 text-xs text-text-secondary">
        <span>
          <strong className="text-text-primary">{meta.flowCount}</strong> flows
        </span>
        <span className="text-border">|</span>
        <span>
          <strong className="text-text-primary">{meta.scoutCount}</strong> explorations
        </span>
        <span className="text-border">|</span>
        <span>
          {new Date(meta.created_at).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
          })}
        </span>
      </div>
    </Link>
  );
}
