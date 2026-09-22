import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "../config/api";
import { formatApiErrorMessage, toastTypeForError } from "../lib/apiErrors";

function notify(showToast, err, fallback) {
  const type = toastTypeForError(err);
  if (!type) return;
  showToast?.(formatApiErrorMessage(err, fallback), type);
}

/* Loads the saved profiles list and exposes reload + delete helpers. */
export default function useProfiles(showToast) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await apiFetch("/users");
      setUsers(data.users || []);
    } catch (e) {
      setLoadError(e);
      notify(showToast, e, "Could not load profiles");
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await apiFetch("/users");
        if (!cancelled) {
          setUsers(data.users || []);
          setLoadError(null);
        }
      } catch (e) {
        if (!cancelled) {
          setLoadError(e);
          notify(showToast, e, "Could not load profiles");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [showToast]);

  const remove = useCallback(async (id) => {
    await apiFetch(`/profile/${id}`, { method: "DELETE" });
    setUsers((u) => u.filter((x) => x.id !== id));
  }, []);

  return { users, loading, reload, remove, setUsers, loadError };
}
