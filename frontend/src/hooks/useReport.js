import { useCallback, useEffect, useState } from "react";
import { apiFetch, apiFetchRaw } from "../config/api";
import { formatApiErrorMessage, toastTypeForError } from "../lib/apiErrors";

/* Only toast true "no report" once per profile across revisits. */
const shownNoReportToast = new Set();
const shownThrottleToast = new Set();

function normalise(payload) {
  const health = payload?.health || {};
  if (!health.pillar_scores) health.pillar_scores = {};
  return { health, ai_report: payload?.ai_report };
}

function notify(showToast, err, fallback) {
  const type = toastTypeForError(err);
  if (!type) return;
  showToast?.(formatApiErrorMessage(err, fallback), type);
}

export default function useReport(userId, showToast) {
  const [report, setReport] = useState(null);
  const [fetching, setFetching] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setFetching(true);
      setLoadError(null);
      try {
        const d = await apiFetch(`/report/${userId}`);
        if (!cancelled) {
          setReport(normalise(d));
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
      setReport(normalise(data));
      setLoadError(null);
      shownNoReportToast.delete(userId);
      shownThrottleToast.delete(userId);
      shownThrottleToast.delete(`load-${userId}`);
      showToast?.("Report generated", "success");
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
    } catch (e) {
      if (e?.code === "not_found" || e?.status === 404) {
        showToast?.("No PDF available — generate a report first.", "info");
      } else {
        notify(showToast, e, "Could not download report");
      }
    }
  }, [userId, showToast]);

  const retryLoad = useCallback(async () => {
    shownThrottleToast.delete(`load-${userId}`);
    setFetching(true);
    setLoadError(null);
    try {
      const d = await apiFetch(`/report/${userId}`);
      setReport(normalise(d));
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
