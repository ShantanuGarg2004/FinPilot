import { useState } from "react";
import { apiFetch } from "../../config/api";
import { useToast } from "../../components/toast-context";
import { formatApiErrorMessage, toastTypeForError } from "../../lib/apiErrors";
import { RISK_OPTIONS } from "../../lib/format";
import Icon from "../../components/Icon";
import Button from "../../components/Button";
import { TextField, TextArea } from "../../components/Field";

export default function ProfileForm({ onCreated }) {
  const showToast = useToast();
  const [form, setForm] = useState({
    age: "",
    income: "",
    expenses: "",
    savings: "",
    risk_appetite: "medium",
    financial_goals: "",
    debt_emi: "",
  });
  const [loading, setLoading] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e?.preventDefault?.();
    if (!form.age || !form.income || !form.expenses || !form.savings) {
      showToast("Please fill in all required fields", "error");
      return;
    }
    if (!form.financial_goals.trim()) {
      showToast("Please enter your financial goals", "error");
      return;
    }
    setLoading(true);
    try {
      const body = {
        age: parseInt(form.age, 10),
        income: parseFloat(form.income),
        expenses: parseFloat(form.expenses),
        savings: parseFloat(form.savings),
        risk_appetite: form.risk_appetite,
        financial_goals: form.financial_goals.trim(),
      };
      const parsedDebt = parseFloat(form.debt_emi);
      if (form.debt_emi.trim() !== "" && !isNaN(parsedDebt) && parsedDebt >= 0) {
        body.debt_emi = parsedDebt;
      }
      const data = await apiFetch("/profile", { method: "POST", body: JSON.stringify(body) });
      showToast("Profile created successfully", "success");
      onCreated(data.user_id, body.financial_goals);
    } catch (err) {
      const type = toastTypeForError(err) || "error";
      showToast(formatApiErrorMessage(err, "Could not create profile"), type);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={submit} className="flex flex-col h-full gap-gutter">
      <header className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <h2 className="font-headline-lg text-headline-lg text-on-surface">Create profile</h2>
          <p className="text-body-md text-on-surface-variant max-w-md">
            Enter your monthly financials to unlock AI advisory, chat, and goal simulation.
          </p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0 text-info bg-info/10 border border-info/25 rounded-full px-3 py-1">
          <Icon name="verified_user" size={14} />
          <span className="font-label-sm text-label-sm">ENCRYPTED</span>
        </div>
      </header>

      <section className="bg-surface-container border border-outline rounded-xl p-gutter space-y-md">
        <div className="flex items-center gap-2">
          <Icon name="account_balance_wallet" size={18} className="text-primary" />
          <h3 className="font-headline-md text-headline-md text-on-surface">Financial snapshot</h3>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-md">
          <TextField label="Age" type="number" value={form.age} onChange={(e) => set("age", e.target.value)} placeholder="28" />
          <TextField label="Monthly income" type="number" prefix="₹" value={form.income} onChange={(e) => set("income", e.target.value)} placeholder="150000" />
          <TextField label="Monthly expenses" type="number" prefix="₹" value={form.expenses} onChange={(e) => set("expenses", e.target.value)} placeholder="80000" />
          <TextField label="Monthly savings" type="number" prefix="₹" value={form.savings} onChange={(e) => set("savings", e.target.value)} placeholder="40000" />
          <TextField
            className="col-span-2"
            label="Debt / EMI (optional)"
            type="number"
            prefix="₹"
            value={form.debt_emi}
            onChange={(e) => set("debt_emi", e.target.value)}
            placeholder="0"
          />
        </div>
      </section>

      <section className="bg-surface-container border border-outline rounded-xl p-gutter space-y-md">
        <div className="flex items-center gap-2">
          <Icon name="monitor_heart" size={18} className="text-primary" />
          <h3 className="font-headline-md text-headline-md text-on-surface">Risk appetite</h3>
        </div>
        <div className="grid grid-cols-3 gap-sm">
          {RISK_OPTIONS.map((opt) => {
            const active = form.risk_appetite === opt.value;
            return (
              <button
                type="button"
                key={opt.value}
                onClick={() => set("risk_appetite", opt.value)}
                className={[
                  "px-2 py-3 border rounded-lg transition-all text-center",
                  active ? "border-primary bg-primary/10" : "border-outline bg-surface hover:border-primary/40",
                ].join(" ")}
              >
                <Icon name={opt.icon} size={18} className={active ? "text-primary" : "text-on-surface-variant"} />
                <p className="font-label-sm text-label-sm uppercase text-on-surface mt-1.5 font-semibold">{opt.label}</p>
                <p className="text-[11px] text-on-surface-variant leading-tight mt-0.5">{opt.hint}</p>
              </button>
            );
          })}
        </div>
      </section>

      <section className="bg-surface-container border border-outline rounded-xl p-gutter space-y-md">
        <div className="flex items-center gap-2">
          <Icon name="flag" size={18} className="text-primary" />
          <h3 className="font-headline-md text-headline-md text-on-surface">Financial goals</h3>
        </div>
        <TextArea
          value={form.financial_goals}
          onChange={(e) => set("financial_goals", e.target.value)}
          rows={3}
          placeholder="e.g. Buy a house in 5 years, retire at 55…"
        />
      </section>

      <div className="pt-md border-t border-outline flex justify-end">
        <Button type="submit" variant="primary" size="lg" loading={loading} loadingText="Creating…" trailingIcon="arrow_forward">
          Continue to Dashboard
        </Button>
      </div>
    </form>
  );
}
