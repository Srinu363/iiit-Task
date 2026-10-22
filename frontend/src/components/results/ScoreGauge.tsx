/** Circular gauge for quality score display — IQ Detect Premium SaaS. */

interface ScoreGaugeProps {
  score: number;
  size?: number;
}

export default function ScoreGauge({ score, size = 160 }: ScoreGaugeProps) {
  const strokeWidth = 10;
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.max(0, Math.min(100, score));
  const progress = (clampedScore / 100) * circumference;
  const center = size / 2;

  const color =
    clampedScore >= 65 ? "#10B981" : clampedScore >= 35 ? "#F59E0B" : "#EF4444";
  const glowColor =
    clampedScore >= 65 ? "rgba(16, 185, 129, 0.18)" : clampedScore >= 35 ? "rgba(245, 158, 11, 0.18)" : "rgba(239, 68, 68, 0.18)";

  return (
    <div
      className="relative inline-flex items-center justify-center p-3 rounded-2xl bg-white shadow-xs border border-[#E8EDF5]"
      style={{ width: size, height: size }}
    >
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90">
        {/* Outer subtle guide track */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#F1F4F9"
          strokeWidth={strokeWidth}
        />
        {/* Track border dashes */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="#E2E8F0"
          strokeWidth={strokeWidth}
          strokeDasharray="2 6"
        />
        {/* Progress arc */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          style={{
            filter: `drop-shadow(0 2px 6px ${glowColor})`,
            transition: "stroke-dashoffset 1s cubic-bezier(0.16, 1, 0.3, 1)",
          }}
        />
      </svg>
      <div className="absolute flex flex-col items-center select-none text-center">
        <span className="text-3xl font-extrabold tracking-tight text-[#111827]">
          {Math.round(clampedScore)}
        </span>
        <span className="text-[10px] font-bold tracking-wider uppercase text-[#94A3B8] -mt-0.5">
          Out of 100
        </span>
      </div>
    </div>
  );
}
