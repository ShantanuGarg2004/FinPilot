/** Which sign-in created a history entry. The back button must not paint another one. */

export const EPOCH_KEY = "finpilot.sessionEpoch";
export const ACCOUNT_KEY = "finpilot.sessionAccountId";
export const ACTIVE_USER_KEY = "finpilot.activeUserId";

export function entryMatchesEpoch(state, epoch) {
  return Boolean(epoch) && Boolean(state) && state.epoch === epoch;
}

export function pathForForeignEntry(epoch, profileId) {
  if (!epoch) return "/";
  const id = Number(profileId);
  if (profileId != null && profileId !== "" && Number.isFinite(id)) return "/dashboard";
  return "/profile";
}

export function makeHistoryState(epoch, accountId) {
  return {
    epoch: epoch || null,
    accountId: accountId == null || accountId === "" ? null : String(accountId),
  };
}

function storage() {
  try {
    if (typeof sessionStorage === "undefined") return null;
    return sessionStorage;
  } catch {
    return null;
  }
}

export function readEpoch() {
  return storage()?.getItem(EPOCH_KEY) || "";
}

export function readAccountId() {
  return storage()?.getItem(ACCOUNT_KEY) || "";
}

export function readStoredUserId() {
  const raw = storage()?.getItem(ACTIVE_USER_KEY);
  if (!raw) return null;
  const id = Number(raw);
  return Number.isFinite(id) ? id : null;
}

export function writeStoredUserId(id) {
  const store = storage();
  if (!store) return;
  try {
    if (id != null) store.setItem(ACTIVE_USER_KEY, String(id));
    else store.removeItem(ACTIVE_USER_KEY);
  } catch {
    /* private mode / blocked storage */
  }
}

export function startSession(accountId) {
  const epoch = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
  const store = storage();
  if (!store) return epoch;
  try {
    store.setItem(EPOCH_KEY, epoch);
    store.setItem(ACCOUNT_KEY, String(accountId));
    store.removeItem(ACTIVE_USER_KEY);
  } catch {
    /* private mode / blocked storage */
  }
  return epoch;
}

export function endSession() {
  const store = storage();
  if (!store) return;
  try {
    store.removeItem(EPOCH_KEY);
    store.removeItem(ACCOUNT_KEY);
    store.removeItem(ACTIVE_USER_KEY);
  } catch {
    /* private mode / blocked storage */
  }
}

export function currentHistoryState() {
  return makeHistoryState(readEpoch(), readAccountId());
}

export function currentEntryMatches() {
  return entryMatchesEpoch(
    typeof history !== "undefined" ? history.state : null,
    readEpoch()
  );
}
