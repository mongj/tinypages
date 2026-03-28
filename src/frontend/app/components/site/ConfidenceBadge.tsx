function confidenceStyle(confidence: number): string {
  if (confidence >= 0.9) return "bg-green-50 text-green-700";
  if (confidence >= 0.7) return "bg-accent-amber-light text-amber-700";
  return "bg-red-50 text-red-700";
}

export function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${confidenceStyle(confidence)}`}
    >
      {pct}% confidence
    </span>
  );
}
