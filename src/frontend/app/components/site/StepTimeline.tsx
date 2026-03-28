import type { Step } from "../../types/flows";

const ACTION_COLORS: Record<string, string> = {
  click: "bg-accent-teal/10 text-accent-teal",
  navigate: "bg-blue-50 text-blue-600",
  type: "bg-purple-50 text-purple-600",
  scroll: "bg-gray-100 text-gray-600",
  submit: "bg-accent-amber-light text-amber-700",
  other: "bg-gray-100 text-gray-500",
};

export function StepTimeline({ steps }: { steps: Step[] }) {
  if (steps.length === 0) return null;

  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-4 top-6 bottom-2 w-px bg-border" />

      <div className="space-y-0">
        {steps.map((step, i) => (
          <div key={step.order} className="relative flex items-start gap-4 py-3">
            {/* Numbered circle */}
            <div className="relative z-10 flex items-center justify-center w-8 h-8 rounded-full bg-accent-teal text-white text-xs font-semibold shrink-0">
              {step.order}
            </div>

            <div className="flex flex-col gap-1 pt-1 min-w-0">
              <div className="flex items-center gap-2">
                <span
                  className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-mono font-medium uppercase ${ACTION_COLORS[step.action] ?? ACTION_COLORS.other}`}
                >
                  {step.action}
                </span>
              </div>
              <p className="text-sm text-text-primary leading-relaxed">
                {step.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
