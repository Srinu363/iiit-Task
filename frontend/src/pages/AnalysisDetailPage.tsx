/** Detail page for a single analysis result — IQ Detect SaaS Dashboard. */
import { useParams, Link } from "react-router-dom";
import { useAnalysisDetail } from "../hooks/useAnalysis";
import ResultsPanel from "../components/results/ResultsPanel";
import { Spinner, Alert } from "../components/ui";

export default function AnalysisDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, error } = useAnalysisDetail(id || "");

  if (isLoading) {
    return (
      <div className="flex justify-center py-28">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-4 max-w-lg mx-auto py-12">
        <Alert variant="error">
          {(error as Error)?.message || "The requested analysis report was not found."}
        </Alert>
        <Link
          to="/history"
          className="inline-flex items-center gap-2 text-sm font-semibold text-[#5145FF] hover:text-[#4335E6]"
        >
          ← Return to Analysis History
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#E2E8F0]">
        <Link
          to="/history"
          className="inline-flex items-center gap-1.5 text-xs sm:text-sm font-semibold text-slate-600 hover:text-[#5145FF] transition-colors"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to History
        </Link>
        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span className="rounded bg-white px-2 py-0.5 border border-[#E2E8F0] text-slate-600">
            SHA: {data.file_hash?.slice(0, 12)}…
          </span>
          {data.created_at && (
            <span className="text-slate-400">{new Date(data.created_at).toLocaleDateString()}</span>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between">
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#111827]">
          {data.filename}
        </h1>
      </div>

      <ResultsPanel result={data} />
    </div>
  );
}
