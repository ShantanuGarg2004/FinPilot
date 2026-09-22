import { useCallback, useState } from "react";
import { ToastContext } from "./toast-context";

const STYLES = {
  success: "bg-surface-container border-primary text-primary",
  error: "bg-error-container border-error text-error",
  warning: "bg-surface-container border-warning text-warning",
  info: "bg-surface-container border-outline text-on-surface-variant",
};

const TTL = {
  success: 3200,
  error: 4500,
  warning: 5500,
  info: 4000,
};

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const showToast = useCallback((message, type = "success") => {
    if (!message) return;
    const tone = STYLES[type] ? type : "success";
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, message, type: tone }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), TTL[tone] || 3500);
  }, []);

  return (
    <ToastContext.Provider value={showToast}>
      {children}
      <div className="fixed bottom-gutter right-gutter z-[9999] flex flex-col gap-2">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`animate-slideInRight max-w-[360px] rounded-lg px-md py-2.5 text-sm border shadow-panel ${STYLES[t.type]}`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
