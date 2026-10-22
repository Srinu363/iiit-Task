/** Issue card showing detected quality issue with severity and confidence — IQ Detect Dashboard. */
import type { Issue } from "../../types/analysis";
import { Badge } from "../ui";

const issueIcons: Record<string, string> = {
  blur: "🔍",
  underexposure: "🌑",
  overexposure: "☀️",
  noise: "📡",
  compression_artifact: "📦",
  low_contrast: "🌫️",
  corruption: "⚠️",
  potential_defect: "🔴",
};

export default function IssueCard({ issue }: { issue: Issue }) {
  const icon = issueIcons[issue.type] || "⚠️";
  const pct = Math.round(issue.confidence * 100);

  const barGradient =
    issue.severity === "high"
      ? "from-[#EF4444] to-[#DC2626]"
      : issue.severity === "medium"
      ? "from-[#F59E0B] to-[#D97706]"
      : "from-[#5145FF] to-[#4335E6]";

  return (
    <div className="animate-fade-in card-lift rounded-2xl border border-[#E8EDF5] bg-white p-5 shadow-xs">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#F7F9FC] border border-[#E8EDF5] text-xl shadow-2xs">
            <span role="img" aria-label={issue.type}>{icon}</span>
          </div>
          <div>
            <p className="font-bold text-[#111827] text-sm sm:text-base capitalize tracking-tight">
              {issue.type.replace(/_/g, " ")}
            </p>
            <div className="mt-1 flex items-center gap-2">
              <Badge label={issue.severity} />
              {issue.uncertain && (
                <span
                  className="inline-flex items-center gap-1 rounded-md bg-[#FFFBEB] px-2 py-0.5 text-[11px] font-semibold text-[#92400E] border border-[#FDE68A]"
                  title="Prediction is near decision threshold"
                >
                  <span>⚡</span> Boundary Case
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="text-right">
          <span className="text-lg font-extrabold text-[#111827] tracking-tight">{pct}%</span>
          <p className="text-[10px] font-bold text-[#94A3B8] uppercase tracking-wider">Confidence</p>
        </div>
      </div>

      {/* Confidence bar */}
      <div className="mt-4">
        <div className="h-2 w-full overflow-hidden rounded-full bg-[#F1F4F9] border border-[#E8EDF5]">
          <div
            className={`h-full rounded-full bg-gradient-to-r ${barGradient} transition-all duration-700`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
}
