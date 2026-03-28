import type { EntryPoint } from "../../types/flows";

export function EntryPointBadge({ entry }: { entry: EntryPoint }) {
  return (
    <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-border bg-bg-secondary text-sm">
      {entry.url ? (
        <a
          href={entry.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-accent-teal hover:underline"
        >
          {entry.label}
        </a>
      ) : (
        <span className="text-text-primary">{entry.label}</span>
      )}
      <span className="text-xs text-text-muted font-mono">{entry.location}</span>
    </div>
  );
}
