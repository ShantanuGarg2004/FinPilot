export default function ProgressBar({ pct, color = "#18B981", height = 6, glow = false }) {
  const clamped = Math.max(0, Math.min(100, Number(pct) || 0));
  return (
    <div
      className="w-full bg-surface-container-highest rounded-full overflow-hidden"
      style={{ height }}
    >
      <div
        className="h-full rounded-full transition-[width] duration-1000 ease-out"
        style={{
          width: `${clamped}%`,
          background: color,
          boxShadow: glow ? `0 0 8px ${color}66` : undefined,
        }}
      />
    </div>
  );
}
