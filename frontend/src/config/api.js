import { ApiError, toApiError } from "../lib/apiErrors";

/* Central API configuration shared by every data hook and page. */
export const API_BASE = import.meta.env.VITE_API_URL || "/api";
export const headers = {
  "Content-Type": "application/json",
};

/* Small fetch helper that normalises the backend's error shape into ApiError. */
export async function apiFetch(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      credentials: "include",
      headers: { ...headers, ...(options.headers || {}) },
    });
  } catch (err) {
    throw toApiError(err);
  }

  let data = null;
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    try {
      data = await res.json();
    } catch {
      data = null;
    }
  } else if (!res.ok) {
    try {
      data = { error: await res.text() };
    } catch {
      data = null;
    }
  } else {
    try {
      data = await res.json();
    } catch {
      data = null;
    }
  }

  if (!res.ok) {
    const error = toApiError(new Error("request failed"), res, data);
    if (error.code === "session_expired") {
      window.dispatchEvent(new Event("finpilot:session-expired"));
    }
    throw error;
  }
  return data;
}

export async function apiFetchRaw(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      credentials: "include",
      headers: { ...headers, ...(options.headers || {}) },
    });
  } catch (err) {
    throw toApiError(err);
  }
  if (!res.ok) {
    let data = null;
    try {
      data = await res.json();
    } catch {
      data = null;
    }
    throw toApiError(new Error("request failed"), res, data);
  }
  return res;
}

export { ApiError, toApiError };
