/** Analysis history page with table, filters, and pagination — IQ Detect SaaS Dashboard. */
import { useState } from "react";
import { Link } from "react-router-dom";
import { useHistory, useDeleteAnalysis } from "../hooks/useAnalysis";
import { Badge, Button, Spinner, EmptyState } from "../components/ui";

const LABELS = ["", "ACCEPTABLE", "DEGRADED", "DEFECTIVE"] as const;

export default function HistoryPage() {
  const [page, setPage] = useState(1);
  const [label, setLabel] = useState("");
  const { data, isLoading, error } = useHistory(page, 20, label || undefined);
  const deleteMut = useDeleteAnalysis();

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header and Filter */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-[#E2E8F0]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[#EEF0FF] px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#5145FF] border border-[#D7DCFF]">
              Assessment Log
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#111827]">
            Analysis History
          </h1>
          <p className="mt-0.5 text-xs sm:text-sm text-slate-500">
            {data ? `${data.total} recorded image assessment${data.total !== 1 ? "s" : ""}` : "Loading repository…"}
          </p>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-2.5">
          <label htmlFor="filter-label" className="text-xs sm:text-sm font-semibold text-slate-600">
            Filter Classification:
          </label>
          <select
            id="filter-label"
            value={label}
            onChange={(e) => { setLabel(e.target.value); setPage(1); }}
            className="rounded-xl border border-[#E2E8F0] bg-white px-3.5 py-2 text-xs sm:text-sm font-semibold text-slate-800 shadow-2xs transition-colors hover:border-slate-300 focus:border-[#5145FF] focus:outline-none focus:ring-2 focus:ring-[#5145FF]/20"
          >
            <option value="">All Classifications</option>
            {LABELS.filter(Boolean).map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </div>
      </div>

      {isLoading && (
        <div className="flex justify-center py-24">
          <Spinner size="lg" />
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-[#FECACA] bg-[#FEF2F2] p-4 text-sm text-[#991B1B]">
          Failed to load analysis history: {(error as Error)?.message || "Internal error"}
        </div>
      )}

      {data && data.items.length === 0 && (
        <EmptyState
          title="No analyses found"
          description={label ? `No past records matching classification "${label}".` : "Upload an image on the Analyze page to begin."}
          icon={
            <svg className="h-10 w-10 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          }
        />
      )}

      {data && data.items.length > 0 && (
        <div className="space-y-4">
          <div className="overflow-hidden rounded-2xl border border-[#E2E8F0] bg-white shadow-2xs">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-[#E2E8F0] bg-[#F7F9FC] text-[11px] font-bold uppercase tracking-wider text-slate-500">
                    <th className="px-5 py-3.5 text-left">Filename</th>
                    <th className="px-4 py-3.5 text-center">Quality Score</th>
                    <th className="px-4 py-3.5 text-center">Classification</th>
                    <th className="px-4 py-3.5 text-center">Issues</th>
                    <th className="px-4 py-3.5 text-left">Timestamp</th>
                    <th className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F1F4F9]">
                  {data.items.map((item) => (
                    <tr key={item.id} className="transition-colors hover:bg-slate-50/70">
                      <td className="px-5 py-4">
                        <Link
                          to={`/analysis/${item.id}`}
                          className="font-semibold text-[#111827] hover:text-[#5145FF] transition-colors flex items-center gap-2 group"
                        >
                          <svg className="h-4 w-4 text-slate-400 group-hover:text-[#5145FF] transition-colors shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <span className="truncate max-w-[200px] sm:max-w-xs">{item.filename}</span>
                        </Link>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <span className={`inline-block font-extrabold text-base ${
                          item.quality_score >= 65 ? "text-[#10B981]" :
                          item.quality_score >= 35 ? "text-[#F59E0B]" : "text-[#EF4444]"
                        }`}>
                          {Math.round(item.quality_score)}
                        </span>
                        <span className="text-[10px] text-slate-400 ml-0.5">/100</span>
                      </td>
                      <td className="px-4 py-4 text-center">
                        <Badge label={item.quality_label} />
                      </td>
                      <td className="px-4 py-4 text-center">
                        {item.issues.length > 0 ? (
                          <span className="inline-flex items-center rounded-full bg-[#EEF0FF] text-[#5145FF] px-2 py-0.5 text-xs font-bold border border-[#D7DCFF]">
                            {item.issues.length}
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400 font-medium">None</span>
                        )}
                      </td>
                      <td className="px-4 py-4 text-slate-500 text-xs font-mono">
                        {item.created_at ? new Date(item.created_at).toLocaleString(undefined, {
                          month: "short", day: "numeric", hour: "2-digit", minute: "2-digit"
                        }) : "—"}
                      </td>
                      <td className="px-5 py-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Link to={`/analysis/${item.id}`}>
                            <Button variant="secondary" className="!px-3 !py-1 text-xs">
                              Details
                            </Button>
                          </Link>
                          <button
                            className="rounded-lg p-1.5 text-slate-400 hover:text-[#EF4444] hover:bg-[#FEF2F2] transition-colors"
                            title="Delete record"
                            onClick={() => { if (confirm("Delete this analysis record?")) deleteMut.mutate(item.id); }}
                          >
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {data.total_pages > 1 && (
            <div className="flex items-center justify-between pt-2">
              <span className="text-xs text-slate-500 font-medium">
                Showing page <strong className="text-slate-800">{data.page}</strong> of <strong className="text-slate-800">{data.total_pages}</strong>
              </span>
              <div className="flex items-center gap-2">
                <Button variant="secondary" disabled={page <= 1} onClick={() => setPage(page - 1)} className="!py-1.5 text-xs">
                  ← Previous
                </Button>
                <Button variant="secondary" disabled={page >= data.total_pages} onClick={() => setPage(page + 1)} className="!py-1.5 text-xs">
                  Next →
                </Button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
