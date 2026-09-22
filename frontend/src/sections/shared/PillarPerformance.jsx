import { PILLAR_META, pctColor } from "../../lib/format";
import ProgressBar from "../../components/ProgressBar";

export default function PillarPerformance({ pillarScores = {}, variant = "list" }) {
  const rows = PILLAR_META.map((p) => {
    const score = pillarScores?.[p.key] ?? 0;
    const pct = p.max > 0 ? Math.round((score / p.max) * 100) : 0;
    return { ...p, score, pct, color: pctColor(pct) };
  });

  if (variant === "grid") {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-md">
        {rows.map((r) => (
          <div
            key={r.key}
            className="bg-surface-container-low px-md py-md rounded-lg border border-outline/60 hover:border-primary/25 transition-all"
          >
            <div className="flex justify-between items-center mb-2.5">
              <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">{r.label}</span>
              <span className="text-[12px] font-semibold tabular-nums" style={{ color: r.color }}>
                {r.pct}%
              </span>
            </div>
            <ProgressBar pct={r.pct} color={r.color} height={5} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-sm">
      {rows.map((r) => (
        <div key={r.key}>
          <div className="flex justify-between font-label-sm text-label-sm text-on-surface-variant mb-1">
            <span>{r.label}</span>
            <span style={{ color: r.color }}>
              {r.score}
              <span className="text-on-surface-variant/50">/{r.max}</span>
            </span>
          </div>
          <ProgressBar pct={r.pct} color={r.color} height={5} />
        </div>
      ))}
    </div>
  );
}
