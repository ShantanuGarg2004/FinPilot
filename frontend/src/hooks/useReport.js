import { useCallback, useEffect, useState } from "react";
import { apiFetch, apiFetchRaw } from "../config/api";
import { formatApiErrorMessage, toastTypeForError } from "../lib/apiErrors";
import {
  invalidateReport,
  loadReport,
  peekReport,
  setReportCache,
} from "../lib/reportStore";

/* Only toast true "no report" once per profile across revisits. */
const shownNoReportToast = new Set();
const shownThrottleToast = new Set();

function notify(showToast, err, fallback) {
  const type = toastTypeForError(err);
  if (!type) return;
  showToast?.(formatApiErrorMessage(err, fallback), type);
}

export default function useReport(userId, showToast) {
  const cached = userId != null ? peekReport(userId) : undefined;
  const [report, setReport] = useState(() =>
    cached === undefined ? null : cached
  );
  const [fetching, setFetching] = useState(() => cached === undefined && userId != null);
  const [generating, setGenerating] = useState(false);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const hit = peekReport(userId);
      if (hit !== undefined) {
        setReport(hit);
        setFetching(false);
        setLoadError(hit ? null : { code: "not_found", status: 404 });
        return;
      }

      setFetching(true);
      setLoadError(null);
      try {
        const d = await loadReport(userId, apiFetch);
        if (!cancelled) {
          setReport(d);
          shownThrottleToast.delete(userId);
        }
      } catch (err) {
        if (cancelled) return;
        setLoadError(err);

        if (err?.code === "not_found" || err?.status === 404) {
          setReport(null);
          if (!shownNoReportToast.has(userId)) {
            shownNoReportToast.add(userId);
            showToast?.("No report yet — click Generate to create one", "info");
          }
        } else if (err?.code === "rate_limit_exceeded" || err?.status === 429) {
          if (!shownThrottleToast.has(`load-${userId}`)) {
            shownThrottleToast.add(`load-${userId}`);
            notify(showToast, err, "Too many report requests. Please wait and retry.");
          }
        } else {
          notify(showToast, err, "Could not load report");
        }
      } finally {
        if (!cancelled) setFetching(false);
      }
    };
    if (userId != null) load();
    return () => {
      cancelled = true;
    };
  }, [userId, showToast]);

  const generate = useCallback(async () => {
    setGenerating(true);
    try {
      const data = await apiFetch("/generate-report", {
        method: "POST",
        body: JSON.stringify({ user_id: userId }),
      });
      const normalised = setReportCache(userId, data);
      setReport(normalised);
      setLoadError(null);
      shownNoReportToast.delete(userId);
      shownThrottleToast.delete(userId);
      shownThrottleToast.delete(`load-${userId}`);
      if (data?.pdf_ready === false) {
        showToast?.(
          "Report saved — PDF will be created when you download",
          "warning"
        );
      } else {
        showToast?.("Report generated", "success");
      }
    } catch (e) {
      notify(showToast, e, "Could not generate report");
    } finally {
      setGenerating(false);
    }
  }, [userId, showToast]);

  const download = useCallback(async () => {
    try {
      const res = await apiFetchRaw(`/download-report/${userId}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `financial_report_profile_${userId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      // Download may have regenerated PDF — refresh cache flag
      const current = peekReport(userId);
      if (current && current.pdf_ready === false) {
        setReportCache(userId, { ...current, pdf_ready: true, pdf_error: null });
        setReport((r) => (r ? { ...r, pdf_ready: true, pdf_error: null } : r));
      }
    } catch (e) {
      if (e?.code === "not_found" || e?.status === 404) {
        showToast?.("No PDF available — generate a report first.", "info");
      } else if (e?.code === "pdf_unavailable") {
        showToast?.("PDF could not be built from the saved report. Try regenerating.", "error");
      } else {
        notify(showToast, e, "Could not download report");
      }
    }
  }, [userId, showToast]);

  const retryLoad = useCallback(async () => {
    shownThrottleToast.delete(`load-${userId}`);
    invalidateReport(userId);
    setFetching(true);
    setLoadError(null);
    try {
      const d = await loadReport(userId, apiFetch);
      setReport(d);
    } catch (err) {
      setLoadError(err);
      if (err?.code === "not_found" || err?.status === 404) {
        setReport(null);
      } else {
        notify(showToast, err, "Could not load report");
      }
    } finally {
      setFetching(false);
    }
  }, [userId, showToast]);

  return { report, fetching, generating, generate, download, loadError, retryLoad };
}
