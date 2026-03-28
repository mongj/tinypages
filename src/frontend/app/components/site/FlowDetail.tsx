import type { Flow } from "../../types/flows";
import { CategoryPill } from "./CategoryPill";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { EntryPointBadge } from "./EntryPointBadge";
import { BlockerCard } from "./BlockerCard";
import { StepTimeline } from "./StepTimeline";

export function FlowDetail({ flow }: { flow: Flow }) {
  const activeBlockers = flow.blockers.filter((b) => b.type !== "none");

  return (
    <div>
      {/* Flow header */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold text-text-primary mb-2">
          {flow.name}
        </h2>
        <div className="flex items-center gap-2 flex-wrap">
          <CategoryPill category={flow.intent_category} />
          <ConfidenceBadge confidence={flow.confidence} />
        </div>
      </div>

      {/* Entry points */}
      {flow.entry_points.length > 0 && (
        <section className="mb-6">
          <h3 className="text-sm font-medium text-text-secondary uppercase tracking-wide mb-3">
            Entry Points
          </h3>
          <div className="flex flex-wrap gap-2">
            {flow.entry_points.map((entry, i) => (
              <EntryPointBadge key={i} entry={entry} />
            ))}
          </div>
        </section>
      )}

      {/* Blockers */}
      {activeBlockers.length > 0 && (
        <section className="mb-6">
          <h3 className="text-sm font-medium text-text-secondary uppercase tracking-wide mb-3">
            Blockers
          </h3>
          <div className="space-y-2">
            {activeBlockers.map((blocker, i) => (
              <BlockerCard key={i} blocker={blocker} />
            ))}
          </div>
        </section>
      )}

      {/* Steps */}
      {flow.steps.length > 0 && (
        <section className="mb-6">
          <h3 className="text-sm font-medium text-text-secondary uppercase tracking-wide mb-3">
            Steps
          </h3>
          <StepTimeline steps={flow.steps} />
        </section>
      )}

      {/* Evidence */}
      {flow.evidence && (
        <section className="mb-6">
          <h3 className="text-sm font-medium text-text-secondary uppercase tracking-wide mb-3">
            Evidence
          </h3>
          <div className="rounded-lg border border-border bg-bg-secondary p-4 text-sm space-y-3">
            {flow.evidence.urls_seen.length > 0 && (
              <div>
                <span className="text-text-muted text-xs uppercase tracking-wide">
                  URLs observed
                </span>
                <div className="mt-1 space-y-1">
                  {flow.evidence.urls_seen.map((url, i) => (
                    <a
                      key={i}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-accent-teal hover:underline font-mono text-xs truncate"
                    >
                      {url}
                    </a>
                  ))}
                </div>
              </div>
            )}
            {flow.evidence.labels_seen.length > 0 && (
              <div>
                <span className="text-text-muted text-xs uppercase tracking-wide">
                  Labels
                </span>
                <div className="mt-1 flex flex-wrap gap-1">
                  {flow.evidence.labels_seen.map((label, i) => (
                    <span
                      key={i}
                      className="inline-flex px-2 py-0.5 rounded bg-bg text-xs text-text-secondary border border-border"
                    >
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {flow.evidence.notes && (
              <div>
                <span className="text-text-muted text-xs uppercase tracking-wide">
                  Notes
                </span>
                <p className="mt-1 text-text-secondary">
                  {flow.evidence.notes}
                </p>
              </div>
            )}
          </div>
        </section>
      )}
    </div>
  );
}
