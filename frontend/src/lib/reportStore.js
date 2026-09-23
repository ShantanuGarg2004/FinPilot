/**
 * Shared report cache + in-flight GET dedupe (Wave 2.8–2.9).
 * Dashboard and Advisory share one fetch per profile.
 */

const cache = new Map(); // userId -> normalised payload | null (404)
const inflight = new Map(); // userId -> Promise

function key(userId) {
  return Number(userId);
}

export function normaliseReport(payload) {
  if (!payload) return null;
  const health = payload.health || {};
  if (!health.pillar_scores) health.pillar_scores = {};
  return {
    health,
    ai_report: payload.ai_report,
    pdf_ready:
      payload.pdf_ready === undefined
        ? Boolean(payload.ai_report)
        : Boolean(payload.pdf_ready),
    pdf_error: payload.pdf_error || null,
  };
}

/** Return cached report without fetching (undefined = miss). */
export function peekReport(userId) {
  const id = key(userId);
  if (!cache.has(id)) return undefined;
  return cache.get(id);
}

export function setReportCache(userId, payload) {
  const id = key(userId);
  const data = payload == null ? null : normaliseReport(payload);
  cache.set(id, data);
  return data;
}

export function invalidateReport(userId) {
  const id = key(userId);
  cache.delete(id);
  inflight.delete(id);
}

/**
 * @param {number} userId
 * @param {(path: string) => Promise<object>} fetcher  typically apiFetch
 */
export function loadReport(userId, fetcher) {
  const id = key(userId);
  if (cache.has(id)) {
    return Promise.resolve(cache.get(id));
  }
  if (inflight.has(id)) {
    return inflight.get(id);
  }

  const promise = fetcher(`/report/${id}`)
    .then((raw) => {
      const data = setReportCache(id, raw);
      inflight.delete(id);
      return data;
    })
    .catch((err) => {
      inflight.delete(id);
      if (err?.code === "not_found" || err?.status === 404) {
        cache.set(id, null);
      }
      throw err;
    });

  inflight.set(id, promise);
  return promise;
}

/** Test helper */
export function _resetReportStore() {
  cache.clear();
  inflight.clear();
}
