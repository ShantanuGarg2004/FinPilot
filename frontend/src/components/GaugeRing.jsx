import { useEffect, useId, useState } from "react";

export default function GaugeRing({
  value = 0,
  max = 100,
  size = 192,
  stroke = 12,
  color = "#18B981",
  gradient = false,
  label,
  sublabel,
  valueClassName = "font-currency-xl text-currency-xl",
}) {
  const r = size / 2 - stroke;
  const cx = size / 2;
  const circ = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(1, (Number(value) || 0) / max));

  const [offset, setOffset] = useState(circ);
  const gradId = `grad-${useId()}`;

  useEffect(() => {
    const t = setTimeout(() => setOffset(circ - pct * circ), 80);
    return () => clearTimeout(t);
  }, [circ, pct]);

  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg className="w-full h-full -rotate-90" viewBox={`0 0 ${size} ${size}`}>
        {gradient && (
          <defs>
            <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#22C995" />
              <stop offset="100%" stopColor="#18B981" />
            </linearGradient>
          </defs>
        )}
        <circle cx={cx} cy={cx} r={r} fill="transparent" stroke="rgba(244,247,251,0.08)" strokeWidth={stroke} />
        <circle
          cx={cx}
          cy={cx}
          r={r}
          fill="transparent"
          stroke={gradient ? `url(#${gradId})` : color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          className="transition-[stroke-dashoffset] duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        {label != null ? (
          label
        ) : (
          <span className={gradient ? `${valueClassName} accent-gradient-text` : valueClassName} style={gradient ? {} : { color }}>
            {Math.round(Number(value) || 0)}
          </span>
        )}
        {sublabel && (
          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider mt-1">
            {sublabel}
          </span>
        )}
      </div>
    </div>
  );
}
