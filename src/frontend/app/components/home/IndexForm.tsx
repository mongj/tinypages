"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { startIndexing, getJob, type Job } from "../../lib/api";

type Phase = "idle" | "submitting" | "polling" | "completed" | "failed";

const STATUS_LABELS: Record<string, string> = {
  pending: "Queued",
  running: "Indexing",
  completed: "Done",
  failed: "Failed",
};

export function IndexForm() {
  const [url, setUrl] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => stopPolling();
  }, [stopPolling]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!url.trim()) return;

    setError(null);
    setPhase("submitting");
    setJob(null);

    try {
      const res = await startIndexing(url.trim());
      setJob({
        job_id: res.job_id,
        page_url: res.url,
        status: "pending",
      });
      setPhase("polling");

      // Poll every 3 seconds
      intervalRef.current = setInterval(async () => {
        try {
          const updated = await getJob(res.job_id);
          setJob(updated);
          if (updated.status === "completed" || updated.status === "failed") {
            stopPolling();
            setPhase(updated.status === "completed" ? "completed" : "failed");
          }
        } catch {
          // Keep polling on transient errors
        }
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
      setPhase("failed");
    }
  }

  function handleReset() {
    stopPolling();
    setPhase("idle");
    setJob(null);
    setError(null);
    setUrl("");
  }

  const isSubmitting = phase === "submitting";
  const isPolling = phase === "polling";
  const isWorking = isSubmitting || isPolling;

  return (
    <div className="rounded-lg border border-border bg-bg p-5">
      <form onSubmit={handleSubmit} className="flex gap-3">
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="Enter a URL to index (e.g. wikipedia.org)"
          disabled={isWorking}
          className="flex-1 rounded-md border border-border bg-bg-secondary px-3 py-2 text-sm text-text-primary placeholder:text-text-muted outline-none focus:border-accent-teal focus:ring-1 focus:ring-accent-teal disabled:opacity-50"
        />
        {phase === "completed" || phase === "failed" ? (
          <button
            type="button"
            onClick={handleReset}
            className="rounded-md bg-bg-secondary border border-border px-4 py-2 text-sm font-medium text-text-primary hover:bg-border transition-colors"
          >
            New
          </button>
        ) : (
          <button
            type="submit"
            disabled={isWorking}
            className="rounded-md bg-accent-teal px-4 py-2 text-sm font-medium text-white hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {isSubmitting ? "Starting..." : isPolling ? "Indexing..." : "Index"}
          </button>
        )}
      </form>

      {/* Job status */}
      {job && (
        <div className="mt-4 flex items-center gap-3 text-sm">
          <StatusDot status={job.status} />
          <span className="text-text-secondary">
            {STATUS_LABELS[job.status] || job.status}
          </span>
          <span className="text-text-muted font-mono text-xs truncate">
            {job.page_url}
          </span>
          {phase === "completed" && (
            <a
              href={`/site/${new URL(job.page_url).host}`}
              className="ml-auto text-accent-teal hover:underline text-xs font-medium"
            >
              View site &rarr;
            </a>
          )}
        </div>
      )}

      {/* Progress bar for active jobs */}
      {isPolling && (
        <div className="mt-3 h-1 rounded-full bg-bg-secondary overflow-hidden">
          <div className="h-full bg-accent-teal rounded-full animate-pulse w-2/3" />
        </div>
      )}

      {error && (
        <p className="mt-3 text-sm text-danger">{error}</p>
      )}
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const color =
    status === "completed"
      ? "bg-success"
      : status === "failed"
        ? "bg-danger"
        : status === "running"
          ? "bg-accent-teal animate-pulse"
          : "bg-text-muted";

  return <span className={`inline-block w-2 h-2 rounded-full ${color}`} />;
}
