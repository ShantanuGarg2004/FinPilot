export default function Spinner({ size = 16, className = "" }) {
  return (
    <span
      className={`inline-block rounded-full border-outline border-t-primary animate-spin ${className}`}
      style={{ width: size, height: size, borderWidth: Math.max(2, Math.round(size / 8)) }}
    />
  );
}
