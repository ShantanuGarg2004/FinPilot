/** Last goal simulation per profile, kept across page changes (Q2). */

const results = new Map();

function key(userId) {
  return Number(userId);
}

export function peekGoal(userId) {
  const id = key(userId);
  if (!results.has(id)) return null;
  return results.get(id);
}

export function setGoal(userId, result) {
  const id = key(userId);
  results.set(id, result);
  return result;
}

export function invalidateGoal(userId) {
  results.delete(key(userId));
}
