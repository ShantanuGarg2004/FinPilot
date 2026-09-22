import Icon from "./Icon";
import Spinner from "./Spinner";

const VARIANTS = {
  primary:
    "bg-primary text-on-primary font-semibold hover:bg-primary-container active:scale-[0.98] disabled:opacity-40 disabled:cursor-default",
  container:
    "bg-info/15 text-info border border-info/30 font-semibold hover:bg-info/25 active:scale-[0.98] disabled:opacity-40 disabled:cursor-default",
  ghost:
    "bg-surface-container text-on-surface hover:bg-surface-container-high disabled:opacity-40 disabled:cursor-default",
  outline:
    "border border-primary/40 text-primary hover:bg-primary/10 disabled:opacity-40 disabled:cursor-default",
  subtle:
    "bg-transparent border border-outline text-on-surface-variant hover:text-on-surface hover:border-primary/40 disabled:opacity-40 disabled:cursor-default",
  danger:
    "bg-transparent text-on-surface-variant hover:text-error disabled:opacity-40 disabled:cursor-default",
};

const SIZES = {
  sm: "px-3 py-1.5 text-[12px] rounded-lg gap-1.5",
  md: "px-4 py-2 text-[13px] rounded-lg gap-1.5",
  lg: "px-5 py-2.5 text-[14px] rounded-lg gap-2",
};

export default function Button({
  children,
  variant = "primary",
  size = "md",
  icon,
  iconFill = false,
  trailingIcon,
  loading = false,
  loadingText,
  className = "",
  disabled,
  ...rest
}) {
  return (
    <button
      disabled={disabled || loading}
      className={`inline-flex items-center justify-center transition-all ${VARIANTS[variant]} ${SIZES[size]} ${className}`}
      {...rest}
    >
      {loading ? (
        <>
          <Spinner size={14} />
          {loadingText || children}
        </>
      ) : (
        <>
          {icon && <Icon name={icon} size={16} fill={iconFill} />}
          {children}
          {trailingIcon && <Icon name={trailingIcon} size={16} />}
        </>
      )}
    </button>
  );
}
