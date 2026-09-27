import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch, apiFetchRaw } from "../config/api";
import { formatApiErrorMessage, toastTypeForError } from "../lib/apiErrors";
import {
  invalidateReport,
  loadReport,
  peekReport,
  setReportCache,
} from "../lib/reportStore";
import { isActiveJob, nextReportState } from "../lib/reportPoll";

/* Only toast true "no report" once per profile across revisits. */
const shownNoReportToast = new Set();
const shownThrottleToast = new Set();
const POLL_MS = 2000;
const POLL_BUDGET_MS = 120000;

function notify(showToast, err, fallback) {
  const type = toastTypeForError(err);
  if (!type) return;
  showToast?.(formatApiErrorMessage(err, fallback), type);
}

export default function useReport(userId, showToast) {
  const cached = userId != null ? peekReport(userId) : undefined;
  const [report, setReport] = useState(() =>
    cached && cached.ai_report ? cached : null
  );
  const [fetching, setFetching] = useState(() => cached === undefined && userId != null);
  const [generating, setGenerating] = useState(() => isActiveJob(cached?.job));
  const [loadError, setLoadError] = useState(null);
  const pollGeneration = useRef(0);

  const applySettled = useCallback((raw) => {
    if (raw?.ai_report) {
      const normalised = setReportCache(userId, raw);
      setReport(normalised);
      setLoadError(null);
      return normalised;
    }
    return null;
  }, [userId]);

  const pollJob = useCallback(async (generation) => {
    const started = Date.now();
    while (pollGeneration.current === generation && Date.now() - started < POLL_BUDGET_MS) {
      try {
        const raw = await apiFetch(`/report/${userId}`);
        if (pollGeneration.current !== generation) return;
        const next = nextReportState(
          { phase: "generating", report: null, generation },
          { type: "snapshot", body: raw },
        );
        if (next.action === "stop" && next.error) {
          if (next.report?.ai_report) applySettled(next.report);
          showToast?.(
            next.error === "worker_lost"
              ? "Report generation took too long. Try again."
              : "Report generation failed. Your previous report is unchanged.",
            "error"
          );
          setGenerating(false);
          return;
        }
        if (next.action === "stop") {
          applySettled(next.report);
          shownNoReportToast.delete(userId);
          if (next.report?.pdf_ready === false) {
            showToast?.("Report saved — PDF will be created when you download", "warning");
          } else {
            showToast?.("Report generated", "success");
          }
          setGenerating(false);
          return;
        }
      } catch (err) {
        if (pollGeneration.current !== generation) return;
        if (err?.code === "rate_limit_exceeded" || err?.status === 429) {
          notify(showToast, err, "Too many report requests. Please wait and retry.");
        } else if (!(err?.code === "not_found" || err?.status === 404)) {
          notify(showToast, err, "Could not load report");
          setGenerating(false);
          return;
        }
      }
      await new Promise((resolve) => setTimeout(resolve, POLL_MS));
    }
    if (pollGeneration.current === generation) {
      const timedOut = nextReportState(
        { phase: "generating", report: null, generation },
        { type: "timeout" },
      );
      if (timedOut.action === "stop") {
        showToast?.("Report generation took too long. Try again.", "error");
        setGenerating(false);
      }
    }
  }, [applySettled, showToast, userId]);

  useEffect(() => {
    let cancelled = false;
    const generation = ++pollGeneration.current;
    const load = async () => {
      const hit = peekReport(userId);
      if (hit !== undefined && !isActiveJob(hit?.job)) {
        setReport(hit && hit.ai_report ? hit : null);
        setFetching(false);
        setGenerating(false);
        setLoadError(hit ? null : { code: "not_found", status: 404 });
        return;
      }

      setFetching(hit === undefined);
      setLoadError(null);
      try {
        const d = await loadReport(userId, apiFetch);
        if (cancelled) return;
        if (d?.ai_report) setReport(d);
        shownThrottleToast.delete(userId);
        if (isActiveJob(d?.job)) {
          setGenerating(true);
          pollJob(generation);
        } else {
          setGenerating(false);
        }
      } catch (err) {
        if (cancelled) return;
        setLoadError(err);
        setGenerating(false);

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
      pollGeneration.current += 1;
    };
  }, [userId, showToast, pollJob]);

  const generate = useCallback(async () => {
    const next = nextReportState(
      { phase: generating ? "generating" : "idle", generation: pollGeneration.current },
      { type: "enqueue" },
    );
    if (next.action === "ignore") return;
    setGenerating(true);
    try {
      pollGeneration.current = next.generation;
      await apiFetch("/generate-report", {
        method: "POST",
        body: JSON.stringify({ user_id: userId }),
      });
      invalidateReport(userId);
      shownThrottleToast.delete(userId);
      shownThrottleToast.delete(`load-${userId}`);
      pollJob(next.generation);
    } catch (e) {
      setGenerating(false);
      notify(showToast, e, "Could not generate report");
    }
  }, [generating, pollJob, userId, showToast]);

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
      setReport(d && d.ai_report ? d : null);
      if (isActiveJob(d?.job)) setGenerating(true);
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
