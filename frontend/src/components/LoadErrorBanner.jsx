import Button from "./Button";
import Icon from "./Icon";

/** Inline banner for non-404 load failures (throttle, auth, network, server). */
export default function LoadErrorBanner({ error, onRetry, resource = "data" }) {
  if (!error) return null;
  if (error.code === "not_found" || error.status === 404) return null;

  const throttled = error.code === "rate_limit_exceeded" || error.status === 429;
  const title = throttled ? "Temporarily rate-limited" : `Couldn’t load ${resource}`;
  const detail = throttled
    ? "Your saved data may still be on the server. Wait a moment, then retry — don’t regenerate unless you need a fresh report."
    : error.message || "Something went wrong while loading.";

  return (
    <div
      className={`mb-md rounded-lg border px-md py-md flex flex-col sm:flex-row sm:items-center gap-sm ${
        throttled ? "border-warning/50 bg-warning/10" : "border-error/40 bg-error-container/40"
      }`}
    >
      <div className="flex items-start gap-sm flex-1 min-w-0">
        <Icon
          name={throttled ? "schedule" : "error"}
          size={18}
          className={`shrink-0 mt-0.5 ${throttled ? "text-warning" : "text-error"}`}
        />
        <div className="min-w-0">
          <p className={`text-[13px] font-semibold ${throttled ? "text-warning" : "text-error"}`}>{title}</p>
          <p className="text-[12px] text-on-surface-variant mt-1 leading-relaxed">{detail}</p>
        </div>
      </div>
      {onRetry && (
        <Button variant="subtle" size="sm" icon="refresh" onClick={onRetry} className="shrink-0">
          Retry
        </Button>
      )}
    </div>
  );
}
