/** Shared chat history cache and in-flight GET dedupe (Q2). */

const cache = new Map();
const inflight = new Map();

function key(userId) {
  return Number(userId);
}

export function peekChat(userId) {
  const id = key(userId);
  if (!cache.has(id)) return undefined;
  return cache.get(id);
}

export function setChatCache(userId, history) {
  const id = key(userId);
  const rows = Array.isArray(history) ? history : [];
  cache.set(id, rows);
  return rows;
}

export function invalidateChat(userId) {
  const id = key(userId);
  cache.delete(id);
  inflight.delete(id);
}

export function loadChatHistory(userId, fetcher) {
  const id = key(userId);
  if (cache.has(id)) return Promise.resolve(cache.get(id));
  if (inflight.has(id)) return inflight.get(id);

  const promise = fetcher(`/chat/history/${id}`)
    .then((data) => {
      const rows = setChatCache(id, data?.history || []);
      inflight.delete(id);
      return rows;
    })
    .catch((err) => {
      inflight.delete(id);
      throw err;
    });

  inflight.set(id, promise);
  return promise;
}
