/* Thin wrapper around Google Material Symbols (loaded in index.html).
   Usage: <Icon name="dashboard" /> or <Icon name="star" fill size={20} /> */
export default function Icon({ name, size, fill = false, weight, className = "", style, ...rest }) {
  const settings = [
    `'FILL' ${fill ? 1 : 0}`,
    `'wght' ${weight ?? 400}`,
    "'GRAD' 0",
    `'opsz' ${size ?? 24}`,
  ].join(", ");
  return (
    <span
      className={`material-symbols-outlined select-none ${className}`}
      style={{ fontSize: size ? `${size}px` : undefined, fontVariationSettings: settings, ...style }}
      aria-hidden="true"
      {...rest}
    >
      {name}
    </span>
  );
}
