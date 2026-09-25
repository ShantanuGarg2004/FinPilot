import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../config/api";
import { formatApiErrorMessage, toastTypeForError } from "../lib/apiErrors";
import { invalidateChat, loadChatHistory, peekChat, setChatCache } from "../lib/chatStore";

function notify(showToast, err, fallback) {
  const type = toastTypeForError(err);
  if (!type) return;
  showToast?.(formatApiErrorMessage(err, fallback), type);
}

export default function useChat(userId, showToast) {
  const cached = userId != null ? peekChat(userId) : undefined;
  const [messages, setMessages] = useState(() => cached || []);
  const [fetching, setFetching] = useState(() => cached === undefined && userId != null);
  const [sending, setSending] = useState(false);
  const [loadError, setLoadError] = useState(null);
  const bottomRef = useRef(null);
  const epoch = useRef(0);

  const applyHistory = useCallback((rows) => {
    setMessages(rows || []);
    setChatCache(userId, rows || []);
  }, [userId]);

  const loadHistory = useCallback(async () => {
    invalidateChat(userId);
    setFetching(true);
    setLoadError(null);
    try {
      const rows = await loadChatHistory(userId, apiFetch);
      setMessages(rows);
    } catch (e) {
      setLoadError(e);
      notify(showToast, e, "Could not load chat history");
    } finally {
      setFetching(false);
    }
  }, [userId, showToast]);

  useEffect(() => {
    epoch.current += 1;
    let cancelled = false;
    const hit = peekChat(userId);
    if (hit !== undefined) {
      setMessages(hit);
      setFetching(false);
      setLoadError(null);
      return undefined;
    }
    setFetching(true);
    setLoadError(null);
    loadChatHistory(userId, apiFetch)
      .then((rows) => {
        if (!cancelled) setMessages(rows);
      })
      .catch((e) => {
        if (cancelled) return;
        setLoadError(e);
        notify(showToast, e, "Could not load chat history");
      })
      .finally(() => {
        if (!cancelled) setFetching(false);
      });
    return () => {
      cancelled = true;
    };
  }, [userId, showToast]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = useCallback(
    async (text) => {
      const q = (text || "").trim();
      if (!q || sending) return;
      const ticket = epoch.current;
      setMessages((m) => [...m, { role: "user", message: q }]);
      setSending(true);
      try {
        const data = await apiFetch("/chat", {
          method: "POST",
          body: JSON.stringify({ user_id: userId, query: q }),
        });
        if (ticket !== epoch.current) return;
        setMessages((m) => {
          const next = [...m, { role: "ai", message: data.response }];
          setChatCache(userId, next);
          return next;
        });
      } catch (e) {
        if (ticket !== epoch.current) return;
        setMessages((m) => (m.length && m[m.length - 1]?.message === q ? m.slice(0, -1) : m));
        notify(showToast, e, "Could not send message");
      } finally {
        if (ticket === epoch.current) setSending(false);
      }
    },
    [userId, sending, showToast]
  );

  const clear = useCallback(async () => {
    epoch.current += 1;
    try {
      await apiFetch(`/chat/history/${userId}`, { method: "DELETE" });
      applyHistory([]);
      setLoadError(null);
      setSending(false);
      showToast?.("Chat cleared", "success");
    } catch (e) {
      notify(showToast, e, "Could not clear chat");
    }
  }, [userId, showToast, applyHistory]);

  return { messages, fetching, sending, send, clear, bottomRef, loadError, retryLoad: loadHistory };
}
