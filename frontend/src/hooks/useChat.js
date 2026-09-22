import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../config/api";
import { formatApiErrorMessage, toastTypeForError } from "../lib/apiErrors";

function notify(showToast, err, fallback) {
  const type = toastTypeForError(err);
  if (!type) return;
  showToast?.(formatApiErrorMessage(err, fallback), type);
}

export default function useChat(userId, showToast) {
  const [messages, setMessages] = useState([]);
  const [fetching, setFetching] = useState(true);
  const [sending, setSending] = useState(false);
  const [loadError, setLoadError] = useState(null);
  const bottomRef = useRef(null);

  const loadHistory = useCallback(async () => {
    setFetching(true);
    setLoadError(null);
    try {
      const data = await apiFetch(`/chat/history/${userId}`);
      setMessages(data.history || []);
    } catch (e) {
      setLoadError(e);
      if (e?.code !== "rate_limit_exceeded") {
        notify(showToast, e, "Could not load chat history");
      } else {
        notify(showToast, e, "Chat history temporarily throttled");
      }
    } finally {
      setFetching(false);
    }
  }, [userId, showToast]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setFetching(true);
      setLoadError(null);
      try {
        const data = await apiFetch(`/chat/history/${userId}`);
        if (!cancelled) setMessages(data.history || []);
      } catch (e) {
        if (cancelled) return;
        setLoadError(e);
        notify(showToast, e, "Could not load chat history");
      } finally {
        if (!cancelled) setFetching(false);
      }
    })();
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
      setMessages((m) => [...m, { role: "user", message: q }]);
      setSending(true);
      try {
        const data = await apiFetch("/chat", {
          method: "POST",
          body: JSON.stringify({ user_id: userId, query: q }),
        });
        setMessages((m) => [...m, { role: "ai", message: data.response }]);
      } catch (e) {
        notify(showToast, e, "Could not send message");
        const failMsg =
          e?.code === "rate_limit_exceeded"
            ? "Advisor is rate-limited right now. Please wait a moment and try again."
            : "Sorry, something went wrong. Please try again.";
        setMessages((m) => [...m, { role: "ai", message: failMsg }]);
      } finally {
        setSending(false);
      }
    },
    [userId, sending, showToast]
  );

  const clear = useCallback(async () => {
    try {
      await apiFetch(`/chat/history/${userId}`, { method: "DELETE" });
      setMessages([]);
      setLoadError(null);
      showToast?.("Chat cleared", "success");
    } catch (e) {
      notify(showToast, e, "Could not clear chat");
    }
  }, [userId, showToast]);

  return { messages, fetching, sending, send, clear, bottomRef, loadError, retryLoad: loadHistory };
}
