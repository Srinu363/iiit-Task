/** Main analyze page — upload + results — IQ Detect SaaS Dashboard. */
import { useState } from "react";
import Dropzone from "../components/upload/Dropzone";
import ResultsPanel from "../components/results/ResultsPanel";
import { useAnalyze } from "../hooks/useAnalysis";
import { Spinner, Alert } from "../components/ui";
import type { AnalysisResult } from "../types/analysis";

export default function AnalyzePage() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const analyze = useAnalyze();

  const handleFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);

    analyze.mutate(file, {
      onSuccess: (data) => setResult(data),
    });
  };

  const handleReset = () => {
    setResult(null);
    setPreview(null);
    analyze.reset();
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* ── 3A. Page Introduction Header ───────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-[#E2E8F0]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-[#EEF0FF] px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-[#5145FF] border border-[#D7DCFF]">
              <span className="h-1.5 w-1.5 rounded-full bg-[#5145FF] animate-pulse" />
              AI Image Assessment
            </span>
            {result && (
              <span className="text-[11px] font-mono text-slate-400 bg-white px-2 py-0.5 rounded border border-[#E2E8F0]">
                ID: {result.id?.slice(0, 10)}…
              </span>
            )}
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-[#111827] tracking-tight">
            Image Quality Analysis
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-0.5 max-w-xl">
            {result
              ? "Comprehensive visual fidelity report, detected quality issues, and statistical feature deviations."
              : "Upload any photograph to evaluate sharpness, noise, exposure flaws, and compression defects."}
          </p>
        </div>

        {/* Action Button */}
        {result && (
          <div className="shrink-0">
            <button
              onClick={handleReset}
              className="inline-flex items-center gap-2 rounded-xl bg-white border border-[#E2E8F0] hover:border-[#5145FF]/40 hover:bg-[#EEF0FF]/40 px-4 py-2.5 text-xs sm:text-sm font-bold text-slate-700 hover:text-[#5145FF] shadow-xs transition-all active:scale-[0.98]"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Analyze Another Image
            </button>
          </div>
        )}
      </div>

      {/* Upload Dropzone */}
      {!result && !analyze.isPending && (
        <Dropzone onFileSelect={handleFile} disabled={analyze.isPending} />
      )}

      {/* Loading state card */}
      {analyze.isPending && (
        <div className="dashboard-card p-12 sm:p-16 text-center space-y-5">
          <div className="flex justify-center">
            <Spinner size="lg" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-[#111827]">Evaluating Image Quality…</h3>
            <p className="mt-1.5 text-sm text-slate-500 max-w-md mx-auto">
              Extracting 23 spatial and frequency-domain features, running gradient-boosted trees,
              calibrating probabilities, and analyzing benchmark deviations.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-2 text-xs font-mono text-slate-500 pt-2">
            <span className="rounded-md bg-[#F7F9FC] px-2.5 py-1 border border-[#E2E8F0]">Laplacian Variance</span>
            <span className="rounded-md bg-[#F7F9FC] px-2.5 py-1 border border-[#E2E8F0]">Immerkaer Noise (σ)</span>
            <span className="rounded-md bg-[#F7F9FC] px-2.5 py-1 border border-[#E2E8F0]">FFT High-Freq Ratio</span>
            <span className="rounded-md bg-[#F7F9FC] px-2.5 py-1 border border-[#E2E8F0]">Isolation Forest Anomaly</span>
          </div>
        </div>
      )}

      {/* Error alert */}
      {analyze.isError && (
        <Alert variant="error">
          <div className="flex items-center gap-2">
            <span>Analysis failed:</span>
            <span className="font-semibold">{(analyze.error as Error)?.message || "Internal server error"}</span>
          </div>
        </Alert>
      )}

      {/* Results view */}
      {result && (
        <ResultsPanel result={result} imagePreview={preview || undefined} />
      )}
    </div>
  );
}
