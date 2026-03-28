import type { Blocker } from "../../types/flows";

function blockerStyle(type: string): string {
  if (type === "captcha" || type === "blocked") {
    return "border-danger/30 bg-red-50 text-red-800";
  }
  return "border-warning/30 bg-accent-amber-light text-amber-800";
}

function blockerLabel(type: string): string {
  const labels: Record<string, string> = {
    captcha: "CAPTCHA",
    login_required: "Login Required",
    payment_required: "Payment Required",
    blocked: "Blocked",
    unknown: "Unknown",
  };
  return labels[type] ?? type;
}

export function BlockerCard({ blocker }: { blocker: Blocker }) {
  if (blocker.type === "none") return null;

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-lg border ${blockerStyle(blocker.type)}`}
    >
      <span className="text-sm font-medium shrink-0">
        {blockerLabel(blocker.type)}
      </span>
      <span className="text-sm">{blocker.detail}</span>
    </div>
  );
}
