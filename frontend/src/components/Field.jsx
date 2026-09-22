const LABEL = "font-label-sm text-label-sm uppercase text-on-surface-variant tracking-wider block mb-1.5 font-medium";
const CONTROL =
  "w-full bg-surface border border-outline rounded-lg px-3 py-2.5 text-body-md text-on-surface font-medium " +
  "focus:outline-none focus:border-primary focus:shadow-[0_0_0_3px_rgba(24,185,129,0.15)] transition-all " +
  "placeholder:text-on-surface-variant/45";

export function TextField({ label, prefix, className = "", ...rest }) {
  return (
    <div className={className}>
      {label && <label className={LABEL}>{label}</label>}
      <div className="relative">
        {prefix && (
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[12px]">
            {prefix}
          </span>
        )}
        <input className={`${CONTROL} ${prefix ? "pl-7" : ""}`} {...rest} />
      </div>
    </div>
  );
}

export function TextArea({ label, className = "", rows = 3, ...rest }) {
  return (
    <div className={className}>
      {label && <label className={LABEL}>{label}</label>}
      <textarea className={`${CONTROL} resize-y`} rows={rows} {...rest} />
    </div>
  );
}

export function SelectField({ label, children, className = "", ...rest }) {
  return (
    <div className={className}>
      {label && <label className={LABEL}>{label}</label>}
      <select className={`${CONTROL} appearance-none`} {...rest}>
        {children}
      </select>
    </div>
  );
}

export function RangeField({ label, value, displayValue, min, max, step, onChange, className = "" }) {
  return (
    <div className={className}>
      {label && <label className={LABEL}>{label}</label>}
      <div className="flex items-center gap-3">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={onChange}
          className="flex-grow h-1.5 bg-surface-container-highest rounded-full appearance-none cursor-pointer accent-primary"
        />
        {displayValue != null && (
          <span className="font-headline-md text-headline-md text-primary w-10 text-center">{displayValue}</span>
        )}
      </div>
    </div>
  );
}
