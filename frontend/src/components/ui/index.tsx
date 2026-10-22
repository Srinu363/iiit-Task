/** Reusable UI primitives — IQ Detect Premium White Analytics SaaS. */
import type { ReactNode } from "react";

/* ── Spinner ─────────────────────────────────────────────────── */
export function Spinner({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const px = { sm: "h-4 w-4 border-2", md: "h-8 w-8 border-[2.5px]", lg: "h-12 w-12 border-3" }[size];
  return (
    <div
      className={`${px} animate-spin rounded-full border-slate-200 border-t-[#5145FF]`}
      role="status"
    >
      <span className="sr-only">Loading…</span>
    </div>
  );
}

/* ── Alert ────────────────────────────────────────────────────── */
type AlertVariant = "info" | "success" | "warning" | "error";
const alertStyles: Record<AlertVariant, string> = {
  info: "border-[#D7DCFF] bg-[#EEF0FF] text-[#3730A3] shadow-2xs",
  success: "border-[#A7F3D0] bg-[#ECFDF5] text-[#065F46] shadow-2xs",
  warning: "border-[#FDE68A] bg-[#FFFBEB] text-[#92400E] shadow-2xs",
  error: "border-[#FECACA] bg-[#FEF2F2] text-[#991B1B] shadow-2xs",
};

export function Alert({ variant = "info", children }: { variant?: AlertVariant; children: ReactNode }) {
  return (
    <div className={`rounded-xl border px-4 py-3 text-sm font-medium transition-all ${alertStyles[variant]}`} role="alert">
      {children}
    </div>
  );
}

/* ── Button ──────────────────────────────────────────────────── */
type BtnVariant = "primary" | "secondary" | "danger" | "ghost";
const btnStyles: Record<BtnVariant, string> = {
  primary: "bg-[#5145FF] hover:bg-[#4335E6] text-white shadow-sm shadow-[#5145FF]/20 hover:shadow-md hover:shadow-[#5145FF]/25 active:scale-[0.98]",
  secondary: "bg-white hover:bg-slate-50 text-slate-700 border border-[#E8EDF5] hover:border-slate-300 shadow-2xs active:scale-[0.98]",
  danger: "bg-[#FEF2F2] hover:bg-[#FEE2E2] text-[#991B1B] border border-[#FECACA] active:scale-[0.98]",
  ghost: "hover:bg-slate-100 text-slate-600 hover:text-gray-900 active:scale-[0.98]",
};

export function Button({
  variant = "primary", children, disabled, className = "", ...props
}: { variant?: BtnVariant; children: ReactNode; disabled?: boolean; className?: string } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-[#5145FF]/40 disabled:opacity-50 disabled:cursor-not-allowed ${btnStyles[variant]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}

/* ── Skeleton loader ─────────────────────────────────────────── */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`animate-pulse rounded-xl bg-slate-200/60 ${className}`} />;
}

/* ── EmptyState ──────────────────────────────────────────────── */
export function EmptyState({ icon, title, description }: { icon?: ReactNode; title: string; description?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center rounded-2xl border border-dashed border-[#E8EDF5] bg-white">
      {icon && <div className="mb-4 text-slate-400 p-3.5 rounded-2xl bg-[#F7F9FC] border border-[#E8EDF5]">{icon}</div>}
      <h3 className="text-base font-bold text-[#111827]">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>}
    </div>
  );
}

/* ── Badge ───────────────────────────────────────────────────── */
const badgeColors: Record<string, string> = {
  ACCEPTABLE: "bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0] shadow-2xs",
  DEGRADED: "bg-[#FFFBEB] text-[#92400E] border-[#FDE68A] shadow-2xs",
  DEFECTIVE: "bg-[#FEF2F2] text-[#991B1B] border-[#FECACA] shadow-2xs",
  low: "bg-[#EEF0FF] text-[#4335E6] border-[#D7DCFF]",
  medium: "bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]",
  high: "bg-[#FEF2F2] text-[#991B1B] border-[#FECACA]",
};

export function Badge({ label }: { label: string }) {
  const style = badgeColors[label] || "bg-slate-100 text-slate-700 border-slate-200";
  return (
    <span className={`inline-flex items-center rounded-lg border px-2.5 py-0.5 text-xs font-bold tracking-wide ${style}`}>
      {label}
    </span>
  );
}
