/** Full AI Analytics Results Panel — IQ Detect Premium White Analytics SaaS. */
import { useState } from "react";
import type { AnalysisResult } from "../../types/analysis";
import ScoreGauge from "./ScoreGauge";
import IssueCard from "./IssueCard";
import { Badge } from "../ui";

interface ResultsPanelProps {
  result: AnalysisResult;
  imagePreview?: string;
}

const FEATURE_DESCRIPTIONS: Record<string, string> = {
  laplacian_variance: "Edge gradient variance. Low values indicate blurriness; high values indicate sharp detail.",
  tenengrad: "Sobel-based gradient magnitude measuring sharpness along edge contours.",
  fft_high_freq_ratio: "Energy ratio in the high-frequency spectrum. High values indicate fine textures or noise.",
  blur_extent: "Edge width measurement across gradient transitions. Higher values denote softer edges.",
  luminance_mean: "Average pixel intensity (0–255). Indicates overall image lighting.",
  luminance_std: "Standard deviation of pixel luminance across the entire image.",
  dark_clip_pct: "Percentage of severely underexposed shadow pixels clipped to near black (<10).",
  bright_clip_pct: "Percentage of severely overexposed highlight pixels clipped to near white (>245).",
  luminance_skewness: "Third statistical moment of intensity. Negative skew indicates heavy shadow bias.",
  immerkaer_noise: "Fast homogeneous-patch noise variance estimation (σ). High values indicate sensor grain.",
  wavelet_noise: "High-frequency wavelet subband noise level estimation.",
  flat_patch_variance: "Variance in the smoothest image patches; indicates background noise floor.",
  blockiness: "Periodic 8x8 block boundary discontinuity typical of lossy JPEG compression.",
  ringing: "High-frequency overshoot ripples near high-contrast edges.",
  rms_contrast: "Root-mean-square pixel intensity contrast across the scene.",
  michelson_contrast: "Luminance dynamic range contrast index ((max-min)/(max+min)).",
  colorfulness: "Hasler-Süsstrunk color saturation and chromatic richness index.",
  saturation_mean: "Average HSV color saturation level across all pixels.",
  saturation_std: "Standard deviation of color saturation across the image.",
  lbp_uniformity: "Local Binary Pattern texture consistency and pattern regularity.",
  entropy: "Shannon entropy measuring information density and texture complexity.",
  color_temp: "Correlated color temperature estimation across color channels.",
};

const FEATURE_DOMAINS: Record<string, string> = {
  laplacian_variance: "Sharpness",
  tenengrad: "Sharpness",
  fft_high_freq_ratio: "Frequency",
  blur_extent: "Sharpness",
  luminance_mean: "Exposure",
  luminance_std: "Exposure",
  dark_clip_pct: "Clipping",
  bright_clip_pct: "Clipping",
  luminance_skewness: "Exposure",
  immerkaer_noise: "Noise",
  wavelet_noise: "Noise",
  flat_patch_variance: "Noise",
  blockiness: "Compression",
  ringing: "Compression",
  rms_contrast: "Contrast",
  michelson_contrast: "Contrast",
  colorfulness: "Color",
  saturation_mean: "Color",
  saturation_std: "Color",
  lbp_uniformity: "Texture",
  entropy: "Texture",
};

export default function ResultsPanel({ result, imagePreview }: ResultsPanelProps) {
  const [activeTab, setActiveTab] = useState<"influencers" | "benchmarks" | "comparison">("influencers");
  const [hoveredFeature, setHoveredFeature] = useState<string | null>(null);

  const importanceData = (result.feature_importance || []).map((f) => ({
    name: f.feature.replace(/_/g, " "),
    key: f.feature,
    deviation: +(f.deviation * 100).toFixed(1),
    raw: f.value,
    ref: f.reference,
    domain: FEATURE_DOMAINS[f.feature] || "Quality",
  }));

  // Key KPI Cards (Top 6 overall quality indicators)
  const kpiMetrics = [
    {
      label: "Overall Quality",
      value: `${Math.round(result.quality_score)} / 100`,
      badge: result.quality_label,
      description: "Calibrated model quality index derived from multi-domain feature assessment",
      icon: "🎯",
      color:
        result.quality_score >= 65
          ? "text-[#16A34A]"
          : result.quality_score >= 35
          ? "text-[#F59E0B]"
          : "text-[#EF4444]",
      ref: undefined,
      unit: "",
    },
    {
      label: "Sharpness Index",
      value: (result.image_stats?.laplacian_variance ?? 0).toFixed(1),
      unit: "var",
      ref: result.feature_importance?.find((f) => f.feature === "laplacian_variance")?.reference,
      description: "Laplacian edge gradient variance across high-frequency spatial boundaries",
      icon: "🔍",
    },
    {
      label: "Mean Luminance",
      value: (result.image_stats?.luminance_mean ?? 0).toFixed(1),
      unit: "/ 255",
      ref: result.feature_importance?.find((f) => f.feature === "luminance_mean")?.reference,
      description: "Average scene brightness and photometric exposure level",
      icon: "☀️",
    },
    {
      label: "Noise Variance (σ)",
      value: (result.image_stats?.immerkaer_noise ?? 0).toFixed(2),
      unit: "std",
      ref: result.feature_importance?.find((f) => f.feature === "immerkaer_noise")?.reference,
      description: "Homogeneous patch noise floor and sensor grain variance",
      icon: "📡",
    },
    {
      label: "RMS Contrast",
      value: (result.image_stats?.rms_contrast ?? 0).toFixed(1),
      unit: "rms",
      ref: result.feature_importance?.find((f) => f.feature === "rms_contrast")?.reference,
      description: "Standard deviation of pixel intensity distribution",
      icon: "🌓",
    },
    {
      label: "Blockiness Index",
      value: (result.image_stats?.blockiness ?? 0).toFixed(2),
      unit: "idx",
      ref: result.feature_importance?.find((f) => f.feature === "blockiness")?.reference,
      description: "Periodic 8×8 block boundary steps typical of lossy JPEG compression",
      icon: "📦",
    },
  ];

  // Full measured CV metrics grouped by domain
  const cvGroups = [
    {
      title: "Sharpness & Frequency Domain",
      icon: "⚡",
      metrics: [
        { key: "laplacian_variance", label: "Laplacian Variance", unit: "" },
        { key: "tenengrad", label: "Tenengrad Gradient", unit: "" },
        { key: "fft_high_freq_ratio", label: "FFT High-Freq Ratio", unit: "" },
        { key: "blur_extent", label: "Edge Width Extent", unit: "px" },
      ],
    },
    {
      title: "Exposure & Luminance",
      icon: "☀️",
      metrics: [
        { key: "luminance_mean", label: "Mean Luminance", unit: "" },
        { key: "luminance_std", label: "Luminance Std Dev", unit: "" },
        { key: "dark_clip_pct", label: "Shadow Clip (<10)", unit: "%" },
        { key: "bright_clip_pct", label: "Highlight Clip (>245)", unit: "%" },
        { key: "luminance_skewness", label: "Intensity Skewness", unit: "" },
      ],
    },
    {
      title: "Noise & Compression Artifacts",
      icon: "📡",
      metrics: [
        { key: "immerkaer_noise", label: "Immerkaer Noise (σ)", unit: "" },
        { key: "wavelet_noise", label: "Wavelet Noise Subband", unit: "" },
        { key: "flat_patch_variance", label: "Flat Patch Variance", unit: "" },
        { key: "blockiness", label: "Blockiness Index", unit: "" },
        { key: "ringing", label: "Ringing Artifacts", unit: "" },
      ],
    },
    {
      title: "Color, Contrast & Texture",
      icon: "🎨",
      metrics: [
        { key: "rms_contrast", label: "RMS Contrast", unit: "" },
        { key: "michelson_contrast", label: "Michelson Contrast", unit: "" },
        { key: "colorfulness", label: "Colorfulness Index", unit: "" },
        { key: "saturation_mean", label: "Saturation Mean", unit: "" },
        { key: "saturation_std", label: "Saturation Std Dev", unit: "" },
        { key: "lbp_uniformity", label: "LBP Uniformity", unit: "" },
      ],
    },
  ];

  return (
    <div className="animate-fade-in space-y-8 w-full min-w-0">
      {/* ── 1. Main Analyzed Image & Quality Score Hero Panel ─────────────── */}
      <section className="dashboard-card overflow-hidden p-6 sm:p-8 lg:p-10 w-full min-w-0">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-10 items-center">
          {/* Left Column: Analyzed Image Preview & Dimensions */}
          <div className="lg:col-span-5 flex flex-col items-center sm:items-start gap-4 w-full min-w-0">
            <div className="w-full relative overflow-hidden rounded-2xl border border-[#E2E8F0] bg-[#F7F9FC] p-3 flex items-center justify-center min-h-[260px] max-h-[380px] shadow-2xs">
              {imagePreview ? (
                <img
                  src={imagePreview}
                  alt={result.filename || "Analyzed file"}
                  className="max-h-[340px] w-auto max-w-full rounded-xl object-contain transition-transform duration-300 hover:scale-[1.01]"
                />
              ) : (
                <div className="flex flex-col items-center justify-center py-16 text-slate-400">
                  <svg className="h-14 w-14 text-slate-300 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span className="text-xs font-semibold text-slate-500">Image preview unavailable</span>
                  <span className="text-[11px] text-slate-400 mt-0.5">Metadata and features preserved</span>
                </div>
              )}
            </div>

            {/* Image Metadata Bar */}
            <div className="w-full flex flex-wrap items-center justify-between gap-2 px-1 text-xs">
              <span className="font-semibold text-slate-800 truncate max-w-[260px]" title={result.filename}>
                {result.filename}
              </span>
              <div className="flex items-center gap-2 text-slate-500 font-mono text-[11px]">
                {result.image_stats?.width && result.image_stats?.height && (
                  <span className="rounded-lg bg-[#F7F9FC] px-2.5 py-1 border border-[#E2E8F0] font-semibold text-slate-700">
                    {result.image_stats.width} × {result.image_stats.height} px
                  </span>
                )}
                {result.file_hash && (
                  <span className="rounded-lg bg-[#F7F9FC] px-2.5 py-1 border border-[#E2E8F0] text-slate-500">
                    SHA: {result.file_hash.slice(0, 8)}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: Overall Quality Assessment & Gauge */}
          <div className="lg:col-span-7 flex flex-col justify-center border-t lg:border-t-0 lg:border-l border-[#E2E8F0] pt-6 lg:pt-0 lg:pl-10 w-full min-w-0">
            <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 sm:gap-8">
              {/* Circular Score Gauge */}
              <div className="shrink-0">
                <ScoreGauge score={result.quality_score} size={160} />
              </div>

              {/* Assessment Narrative */}
              <div className="flex-1 text-center sm:text-left space-y-3.5 min-w-0">
                <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                  <Badge label={result.quality_label} />
                  {result.cached && (
                    <span className="inline-flex items-center rounded-lg bg-[#F7F9FC] px-2.5 py-0.5 text-[11px] font-semibold text-slate-600 border border-[#E2E8F0]">
                      Cached Hit
                    </span>
                  )}
                  {result.anomaly_score !== null && result.anomaly_score !== undefined && (
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-0.5 text-[11px] font-semibold border ${
                        result.anomaly_score > 0.6
                          ? "bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]"
                          : "bg-[#F7F9FC] text-slate-600 border-[#E2E8F0]"
                      }`}
                    >
                      <span className="h-1.5 w-1.5 rounded-full bg-current" />
                      Anomaly Index: {(result.anomaly_score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                <h3 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-[#111827] tracking-tight">
                  {result.quality_label === "ACCEPTABLE" && "High Visual Quality • Pristine Fidelity"}
                  {result.quality_label === "DEGRADED" && "Noticeable Quality Degradation"}
                  {result.quality_label === "DEFECTIVE" && "Severe Image Quality Defects Detected"}
                </h3>

                <p className="text-sm text-slate-600 leading-relaxed max-w-2xl">
                  {result.quality_label === "ACCEPTABLE" &&
                    "The analyzed image maintains sharp edge gradients, balanced dynamic range, and clean homogeneous noise levels consistent with calibrated reference standards."}
                  {result.quality_label === "DEGRADED" &&
                    "Visual degradation detected across key spatial or frequency parameters. Edge sharpness or photometric exposure exhibits moderate deviation from clean benchmarks."}
                  {result.quality_label === "DEFECTIVE" &&
                    "The image exhibits severe quality anomalies such as acute blur, high sensor noise variance, extreme shadow/highlight clipping, or noticeable compression discontinuities."}
                </p>

                {/* Engine Metadata Details */}
                <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2.5 pt-1 text-xs font-mono text-slate-500">
                  <span className="flex items-center gap-1.5 rounded-lg bg-[#F7F9FC] px-3 py-1.5 border border-[#E2E8F0] font-medium text-slate-700">
                    <svg className="h-3.5 w-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    Latency: {result.latency_ms?.toFixed(0)} ms
                  </span>
                  <span className="rounded-lg bg-[#F7F9FC] px-3 py-1.5 border border-[#E2E8F0] font-medium text-slate-700">
                    Engine: LightGBM v{result.model_version || "1.0.0"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 2. Quality Overview KPI Summary Grid ─────────────────────────── */}
      <section className="w-full min-w-0">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h2 className="text-sm sm:text-base font-bold uppercase tracking-wider text-slate-600">
              Quality KPI Summary
            </h2>
            <span className="hidden sm:inline-block rounded-md bg-[#EEF0FF] text-[#5145FF] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider border border-[#D7DCFF]">
              Core Assessment Indicators
            </span>
          </div>
          <span className="text-xs text-slate-400">Equalized 6-Metric Overview</span>
        </div>

        <div className="kpi-grid">
          {kpiMetrics.map((kpi, idx) => (
            <div key={idx} className="kpi-card card-lift">
              <div>
                <div className="flex items-start justify-between gap-2">
                  <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 leading-tight">
                    {kpi.label}
                  </span>
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-[#F7F9FC] border border-[#E2E8F0] text-sm select-none">
                    {kpi.icon}
                  </span>
                </div>

                <div className="mt-3">
                  <div className="flex items-baseline gap-1.5">
                    <span className={`text-2xl sm:text-3xl font-extrabold tracking-tight ${kpi.color || "text-[#111827]"}`}>
                      {kpi.value}
                    </span>
                    {kpi.unit && <span className="text-xs text-slate-400 font-semibold">{kpi.unit}</span>}
                  </div>

                  {kpi.badge && (
                    <div className="mt-2">
                      <Badge label={kpi.badge} />
                    </div>
                  )}

                  {kpi.ref !== undefined && (
                    <div className="mt-2 inline-flex items-center gap-1.5 text-[11px] font-mono text-slate-600 bg-[#F7F9FC] px-2.5 py-1 rounded-md border border-[#E2E8F0]">
                      <span className="text-slate-400">benchmark:</span>
                      <strong className="text-slate-800">
                        {typeof kpi.ref === "number" ? kpi.ref.toFixed(1) : kpi.ref}
                      </strong>
                    </div>
                  )}
                </div>
              </div>

              <p className="mt-3 text-xs text-slate-500 leading-relaxed border-t border-[#F1F4F9] pt-2.5">
                {kpi.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── 3. Specific Detected Quality Flaws (if any) ──────────────────── */}
      {result.issues && result.issues.length > 0 && (
        <section className="w-full min-w-0">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base sm:text-lg font-bold text-[#111827] tracking-tight flex items-center gap-2">
              Detected Quality Flaws
              <span className="rounded-full bg-[#FEF2F2] text-[#991B1B] px-2.5 py-0.5 text-xs font-bold border border-[#FECACA]">
                {result.issues.length} {result.issues.length === 1 ? "defect" : "defects"}
              </span>
            </h2>
            <span className="text-xs text-slate-400">Classified by calibrated LightGBM</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {result.issues.map((issue, idx) => (
              <IssueCard key={`${issue.type}-${idx}`} issue={issue} />
            ))}
          </div>
        </section>
      )}

      {/* ── 4. Automated Diagnostic Summary ─────────────────────────────── */}
      <section className="dashboard-card p-6 sm:p-8 w-full min-w-0">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 mb-5 border-b border-[#E2E8F0]">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#EEF0FF] text-[#5145FF] border border-[#D7DCFF]">
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h2 className="text-base sm:text-lg font-bold text-[#111827] tracking-tight">
                Automated Diagnostic Summary
              </h2>
              <p className="text-xs text-slate-500">Heuristic reasoning and model explanation findings</p>
            </div>
          </div>
          <span className="self-start sm:self-auto text-xs font-semibold text-slate-600 bg-[#F7F9FC] px-3 py-1.5 rounded-lg border border-[#E2E8F0]">
            {result.explanations?.length || 0} observations logged
          </span>
        </div>

        {result.explanations && result.explanations.length > 0 ? (
          <div className="space-y-3">
            {result.explanations.map((exp, i) => {
              const isDefectWarning =
                exp.toLowerCase().includes("severe") ||
                exp.toLowerCase().includes("high") ||
                exp.toLowerCase().includes("significant");
              const isModerateWarning =
                exp.toLowerCase().includes("moderate") ||
                exp.toLowerCase().includes("slight") ||
                exp.toLowerCase().includes("elevated");

              return (
                <div
                  key={i}
                  className={`flex items-start gap-3.5 rounded-xl p-4 border transition-colors ${
                    isDefectWarning
                      ? "bg-[#FEF2F2]/80 border-[#FECACA] text-[#991B1B]"
                      : isModerateWarning
                      ? "bg-[#FFFBEB]/80 border-[#FDE68A] text-[#92400E]"
                      : "bg-[#F7F9FC] border-[#E2E8F0] text-slate-700"
                  }`}
                >
                  <span className="mt-0.5 text-base shrink-0 select-none">
                    {isDefectWarning ? "⚠️" : isModerateWarning ? "⚡" : "✓"}
                  </span>
                  <span className="text-sm font-medium leading-relaxed">{exp}</span>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="py-8 text-center text-slate-400 text-sm">
            No specific diagnostic remarks generated for this image.
          </div>
        )}
      </section>

      {/* ── 5. Top Quality Influencers & Benchmark Analysis ─────────────── */}
      <section className="dashboard-card p-6 sm:p-8 w-full min-w-0">
        {/* Header & Tab Selector */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 mb-6 border-b border-[#E2E8F0]">
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg sm:text-xl font-extrabold text-[#111827] tracking-tight">
                Top Quality Influencers &amp; Benchmark Analysis
              </h2>
              <span className="hidden sm:inline-block rounded-md bg-[#EEF0FF] text-[#5145FF] px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider border border-[#D7DCFF]">
                Statistical Deviations
              </span>
            </div>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 max-w-2xl leading-relaxed">
              Relative magnitude of feature deviation from the benchmark median computed across clean reference images.
            </p>
          </div>

          {/* View Mode Toggle */}
          <div className="flex items-center self-start sm:self-auto rounded-xl bg-[#F7F9FC] p-1 border border-[#E2E8F0]">
            <button
              onClick={() => setActiveTab("influencers")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "influencers"
                  ? "bg-white text-[#5145FF] shadow-2xs border border-[#E2E8F0]"
                  : "text-slate-600 hover:text-gray-900 border border-transparent"
              }`}
            >
              Deviation Scale (%)
            </button>
            <button
              onClick={() => setActiveTab("benchmarks")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "benchmarks"
                  ? "bg-white text-[#5145FF] shadow-2xs border border-[#E2E8F0]"
                  : "text-slate-600 hover:text-gray-900 border border-transparent"
              }`}
            >
              Actual vs. Benchmark
            </button>
            <button
              onClick={() => setActiveTab("comparison")}
              className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === "comparison"
                  ? "bg-white text-[#5145FF] shadow-2xs border border-[#E2E8F0]"
                  : "text-slate-600 hover:text-gray-900 border border-transparent"
              }`}
            >
              Benchmark Comparison
            </button>
          </div>
        </div>

        {/* Tab 1: Full-Width Horizontal Bar Chart with Deviation Scale */}
        {activeTab === "influencers" && (
          <div className="space-y-6 w-full min-w-0">
            {/* Chart Legend / Scale Guide */}
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-slate-500 font-medium pb-2 border-b border-[#F1F4F9]">
              <span className="font-semibold text-slate-700">Feature Metric &amp; Description</span>
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#EF4444]" /> Critical Deviation (&gt;50%)
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#F59E0B]" /> Moderate (25–50%)
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="h-2 w-2 rounded-full bg-[#5145FF]" /> Minor (&lt;25%)
                </span>
              </div>
            </div>

            {/* Horizontal Bar List Using Full-Width Responsive 3-Column Grid Rows */}
            <div className="space-y-3">
              {importanceData.map((item) => {
                const maxDev = Math.max(...importanceData.map((d) => d.deviation), 100);
                const barWidth = Math.min(100, Math.max(6, (item.deviation / maxDev) * 100));

                const isCritical = item.deviation >= 50;
                const isModerate = item.deviation >= 25 && item.deviation < 50;

                const gradientClass = isCritical
                  ? "from-[#EF4444] to-[#DC2626]"
                  : isModerate
                  ? "from-[#F59E0B] to-[#D97706]"
                  : "from-[#5145FF] to-[#6366F1]";

                const badgeClass = isCritical
                  ? "bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]"
                  : isModerate
                  ? "bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]"
                  : "bg-[#EEF0FF] text-[#4335E6] border-[#D7DCFF]";

                const isHovered = hoveredFeature === item.key;
                const description = FEATURE_DESCRIPTIONS[item.key];

                return (
                  <div
                    key={item.key}
                    onMouseEnter={() => setHoveredFeature(item.key)}
                    onMouseLeave={() => setHoveredFeature(null)}
                    className="influencer-row"
                  >
                    {/* Column 1: Feature Metric Label & Domain */}
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-[#111827] capitalize tracking-tight text-sm">
                          {item.name}
                        </span>
                        <span className="rounded bg-[#F7F9FC] px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 border border-[#E2E8F0]">
                          {item.domain}
                        </span>
                      </div>
                      {description && (
                        <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed" title={description}>
                          {description}
                        </p>
                      )}
                    </div>

                    {/* Column 2: Wide Horizontal Bar Track with Scale Ticks */}
                    <div className="w-full min-w-0">
                      <div className="influencer-bar-track">
                        <div
                          className={`influencer-bar-fill bg-gradient-to-r ${gradientClass}`}
                          style={{ width: `${barWidth}%` }}
                        />
                      </div>
                      {/* Scale guide markers */}
                      <div className="flex justify-between items-center text-[10px] text-slate-400 font-mono mt-1 px-0.5">
                        <span>0%</span>
                        <span>25%</span>
                        <span>50%</span>
                        <span>75%</span>
                        <span>100%+</span>
                      </div>
                    </div>

                    {/* Column 3: Aligned Numerical Details & Badge */}
                    <div className="flex items-center justify-between sm:justify-end gap-3 font-mono text-xs shrink-0">
                      <div className="text-left sm:text-right">
                        <div className="text-slate-600">
                          actual: <strong className="text-slate-900">{typeof item.raw === "number" ? item.raw.toFixed(2) : item.raw}</strong>
                        </div>
                        <div className="text-slate-400 text-[11px]">
                          ref: {typeof item.ref === "number" ? item.ref.toFixed(2) : item.ref}
                        </div>
                      </div>
                      <span className={`font-bold px-2.5 py-1 rounded-lg border text-xs ${badgeClass}`}>
                        +{item.deviation}%
                      </span>
                    </div>

                    {/* Rich Expandable Details on Hover */}
                    {isHovered && description && (
                      <div className="col-span-1 lg:col-span-3 mt-2 rounded-xl bg-white p-3.5 border border-[#E2E8F0] shadow-md text-xs text-slate-600 flex items-start gap-2.5 animate-fade-in">
                        <span className="text-base">💡</span>
                        <div className="space-y-1">
                          <p>
                            <strong className="text-slate-900 font-semibold">{item.name}:</strong> {description}
                          </p>
                          <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-slate-500 pt-1">
                            <span>Measured: <strong className="text-slate-800">{typeof item.raw === "number" ? item.raw.toFixed(3) : item.raw}</strong></span>
                            <span>Clean Reference Median: <strong className="text-slate-800">{typeof item.ref === "number" ? item.ref.toFixed(3) : item.ref}</strong></span>
                            <span className="font-bold text-[#5145FF]">Relative Deviation: +{item.deviation}%</span>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab 2: Actual vs. Benchmark Comparison Table */}
        {activeTab === "benchmarks" && (
          <div className="overflow-x-auto rounded-xl border border-[#E2E8F0]">
            <table className="w-full text-left text-xs sm:text-sm font-medium text-slate-600">
              <thead>
                <tr className="bg-[#F7F9FC] border-b border-[#E2E8F0] text-slate-500 font-bold uppercase tracking-wider text-[11px]">
                  <th className="px-5 py-3.5">Feature Metric</th>
                  <th className="px-4 py-3.5">Domain</th>
                  <th className="px-4 py-3.5">Measured Value</th>
                  <th className="px-4 py-3.5">Clean Benchmark Ref</th>
                  <th className="px-4 py-3.5">Calculated Variance</th>
                  <th className="px-5 py-3.5 text-right">Relative Deviation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#EEF2F7]">
                {importanceData.map((item) => {
                  const rawNum = typeof item.raw === "number" ? item.raw : parseFloat(item.raw);
                  const refNum = typeof item.ref === "number" ? item.ref : parseFloat(item.ref);
                  const variance = !isNaN(rawNum) && !isNaN(refNum) ? (rawNum - refNum).toFixed(3) : "N/A";
                  const isPositive = !isNaN(rawNum) && !isNaN(refNum) && rawNum >= refNum;

                  return (
                    <tr key={item.key} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-5 py-3.5 font-semibold text-slate-900 capitalize">
                        {item.name}
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="rounded bg-[#F7F9FC] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-500 border border-[#E2E8F0]">
                          {item.domain}
                        </span>
                      </td>
                      <td className="px-4 py-3.5 font-mono text-slate-900 font-semibold">
                        {typeof item.raw === "number" ? item.raw.toFixed(3) : item.raw}
                      </td>
                      <td className="px-4 py-3.5 font-mono text-slate-500">
                        {typeof item.ref === "number" ? item.ref.toFixed(3) : item.ref}
                      </td>
                      <td className="px-4 py-3.5 font-mono">
                        <span className={isPositive ? "text-[#EF4444] font-semibold" : "text-[#16A34A] font-semibold"}>
                          {isPositive ? `+${variance}` : variance}
                        </span>
                      </td>
                      <td className="px-5 py-3.5 text-right font-mono font-bold text-slate-900">
                        +{item.deviation}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Tab 3: Normalized Benchmark Comparison Visualizer */}
        {activeTab === "comparison" && (
          <div className="space-y-6">
            <div className="rounded-xl bg-[#F7F9FC] p-4 border border-[#E2E8F0] text-xs text-slate-600 leading-relaxed">
              <span className="font-bold text-slate-800">Analytical Benchmark Comparison:</span> Displays measured values normalized against clean baseline reference medians (where 100% represents the clean reference standard). Bars extending significantly beyond 100% indicate anomalous deviation.
            </div>

            <div className="space-y-5">
              {importanceData.map((item) => {
                const rawNum = typeof item.raw === "number" ? item.raw : parseFloat(item.raw);
                const refNum = typeof item.ref === "number" ? item.ref : parseFloat(item.ref);
                const ratio = !isNaN(rawNum) && !isNaN(refNum) && refNum > 0 ? (rawNum / refNum) * 100 : 100;
                const normalizedWidth = Math.min(100, Math.max(10, (ratio / 200) * 100));

                return (
                  <div key={item.key} className="space-y-1.5">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-800 capitalize">
                        {item.name}
                      </span>
                      <span className="font-mono text-slate-500">
                        {ratio.toFixed(1)}% of clean baseline
                      </span>
                    </div>

                    <div className="h-4 w-full rounded-full bg-[#EEF2F7] border border-[#E2E8F0] overflow-hidden relative">
                      {/* Reference line at 50% (representing 100% of baseline in a 200% scale) */}
                      <div className="absolute top-0 bottom-0 left-1/2 w-0.5 bg-slate-400 z-10" title="100% Clean Baseline" />
                      <div
                        className={`h-full rounded-full transition-all duration-700 ${
                          ratio > 140
                            ? "bg-[#EF4444]"
                            : ratio > 115
                            ? "bg-[#F59E0B]"
                            : "bg-[#5145FF]"
                        }`}
                        style={{ width: `${normalizedWidth}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </section>

      {/* ── 6. Measured Computer Vision Metrics (Domain Grouped) ───────── */}
      <section className="dashboard-card p-6 sm:p-8 w-full min-w-0 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-[#E2E8F0]">
          <div>
            <h2 className="text-lg sm:text-xl font-extrabold text-[#111827] tracking-tight">
              Standardized Computer Vision Metrics
            </h2>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Rigorous parameter extraction across spatial gradients, intensity histograms, frequency spectrum, and wavelets.
            </p>
          </div>
          <span className="text-xs font-mono font-semibold text-slate-600 bg-[#F7F9FC] px-3 py-1.5 rounded-lg border border-[#E2E8F0]">
            23 Extracted Features
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
          {cvGroups.map((group, gIdx) => (
            <div key={gIdx} className="rounded-2xl border border-[#E2E8F0] bg-[#F7F9FC]/60 p-5 space-y-3.5 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between pb-2 border-b border-[#E2E8F0]">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                    <span>{group.icon}</span>
                    <span>{group.title}</span>
                  </h3>
                  <span className="text-[10px] text-slate-400 font-mono font-semibold">domain {gIdx + 1}</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 mt-3">
                  {group.metrics.map(({ key, label, unit }) => {
                    const val = result.image_stats?.[key];
                    if (val === undefined) return null;

                    return (
                      <div
                        key={key}
                        className="rounded-xl border border-[#E2E8F0] bg-white p-3 card-lift shadow-2xs"
                        title={FEATURE_DESCRIPTIONS[key] || label}
                      >
                        <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400 truncate">
                          {label}
                        </p>
                        <p className="mt-1.5 text-base sm:text-lg font-extrabold text-[#111827] font-mono tracking-tight">
                          {typeof val === "number" ? (val > 100 ? Math.round(val) : val.toFixed(2)) : val}
                          {unit && <span className="text-[11px] font-normal text-slate-400 ml-1">{unit}</span>}
                        </p>
                      </div>
                    );
                  })}
                </div>
              </div>

              <p className="text-[10px] text-slate-400 pt-2 border-t border-[#E2E8F0]">
                Calibrated local OpenCV pipeline
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
