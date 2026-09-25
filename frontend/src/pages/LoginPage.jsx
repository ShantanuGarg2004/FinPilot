import { useState } from "react";
import Button from "../components/Button";
import { TextField } from "../components/Field";
import { apiFetch } from "../config/api";

export default function LoginPage({ onSignedIn }) {
  const [mode, setMode] = useState("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError("");
    if (mode === "signup" && password !== confirm) {
      setError("Confirm password must match password.");
      return;
    }
    setLoading(true);
    try {
      const path = mode === "signup" ? "/auth/signup" : "/auth/login";
      const body = mode === "signup"
        ? { email, password, confirm_password: confirm }
        : { email, password };
      const account = await apiFetch(path, { method: "POST", body: JSON.stringify(body) });
      onSignedIn(account);
    } catch (err) {
      setError(err.message || "Email or password is incorrect.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-background text-on-surface flex items-center justify-center px-4">
      <form onSubmit={submit} className="w-full max-w-md bg-surface border border-outline rounded-xl p-8 space-y-4">
        <div>
          <h1 className="text-[22px] font-bold">FinPilot <span className="text-primary">AI</span></h1>
          <p className="text-on-surface-variant text-[13px] mt-1">
            {mode === "signup" ? "Create an account" : "Sign in"}
          </p>
        </div>
        <TextField label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
        <TextField label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required autoComplete={mode === "signup" ? "new-password" : "current-password"} />
        {mode === "signup" && (
          <TextField label="Confirm password" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} required autoComplete="new-password" />
        )}
        {error && <p className="text-[13px] text-error">{error}</p>}
        <Button type="submit" loading={loading} className="w-full">
          {mode === "signup" ? "Create an account" : "Sign in"}
        </Button>
        <button
          type="button"
          className="text-[13px] text-primary"
          onClick={() => {
            setMode(mode === "signup" ? "signin" : "signup");
            setError("");
          }}
        >
          {mode === "signup" ? "Already have an account? Sign in" : "Create an account"}
        </button>
      </form>
    </div>
  );
}
