import type { SiteFlows, SiteMeta } from "../../types/flows";

export function SiteOverview({
  meta,
  flows,
}: {
  meta: SiteMeta;
  flows: SiteFlows;
}) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-3 mb-2">
        <img
          src={`https://www.google.com/s2/favicons?domain=${meta.host}&sz=32`}
          alt=""
          className="w-6 h-6"
        />
        <h1 className="text-2xl font-semibold text-text-primary">
          {meta.name}
        </h1>
      </div>
      <a
        href={meta.seed_url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm text-accent-teal hover:underline"
      >
        {meta.seed_url}
      </a>
      {flows.site_understanding && (
        <p className="mt-2 text-sm text-text-secondary leading-relaxed">
          {flows.site_understanding.one_line_summary}
        </p>
      )}
      <div className="mt-3 flex items-center gap-4 text-sm text-text-secondary">
        <span>
          <strong className="text-text-primary">{flows.merge_count}</strong>{" "}
          flows discovered
        </span>
        <span className="text-border">|</span>
        <span>
          <strong className="text-text-primary">{flows.source_runs}</strong>{" "}
          scout runs
        </span>
        <span className="text-border">|</span>
        <span>
          Indexed{" "}
          {new Date(flows.created_at).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
          })}
        </span>
      </div>
      {flows.site_understanding && (
        <div className="mt-6 space-y-4">
          <div>
            <h3 className="text-sm font-medium text-text-primary mb-1">
              About
            </h3>
            <p className="text-sm text-text-secondary leading-relaxed whitespace-pre-line">
              {flows.site_understanding.what_the_site_does}
            </p>
          </div>
          {flows.site_understanding.offerings.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-text-primary mb-1">
                Offerings
              </h3>
              <ul className="text-sm text-text-secondary space-y-1">
                {flows.site_understanding.offerings.map((o) => (
                  <li key={o} className="flex items-start gap-2">
                    <span className="text-accent-teal mt-0.5">&#8226;</span>
                    {o}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {flows.site_understanding.primary_audiences.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-text-primary mb-1">
                Primary Audiences
              </h3>
              <div className="flex flex-wrap gap-2">
                {flows.site_understanding.primary_audiences.map((a) => (
                  <span
                    key={a}
                    className="text-xs px-2 py-1 rounded-full bg-bg-sidebar text-text-secondary"
                  >
                    {a}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
