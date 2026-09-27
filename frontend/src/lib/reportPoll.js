/** Report poll decisions. No React, so node --test can import this file. */

export function isActiveJob(job) {
  return Boolean(job && (job.status === "queued" || job.status === "running"));
}

/**
 * Next poll state.
 * An accepted enqueue (the generate call returned) starts polling.
 * A second enqueue while a poll is already running is ignored.
 * A snapshot with no active job and report text stops and shows that report.
 * A failed job stops, keeps the previous report text, and carries the error.
 * A timeout stops and keeps the previous report.
 */
export function nextReportState(state, event) {
  const report = state?.report ?? null;
  const generation = state?.generation ?? 0;
  const generating = state?.phase === "generating";

  if (event?.type === "enqueue") {
    if (generating) {
      return { phase: "generating", report, generation, error: null, action: "ignore" };
    }
    return {
      phase: "generating",
      report,
      generation: generation + 1,
      error: null,
      action: "poll",
    };
  }

  if (event?.type === "timeout") {
    return { phase: "idle", report, generation, error: "timeout", action: "stop" };
  }

  if (event?.type === "snapshot") {
    const body = event.body || {};
    const job = body.job;
    if (job?.status === "failed") {
      const kept = body.ai_report ? body : report;
      return {
        phase: "idle",
        report: kept,
        generation,
        error: job.error_code || "failed",
        action: "stop",
      };
    }
    if (!isActiveJob(job) && body.ai_report) {
      return { phase: "idle", report: body, generation, error: null, action: "stop" };
    }
    return { phase: "generating", report, generation, error: null, action: "poll" };
  }

  return { phase: state?.phase || "idle", report, generation, error: null, action: "ignore" };
}
