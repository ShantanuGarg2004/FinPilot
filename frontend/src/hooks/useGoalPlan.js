import { useState } from "react";
import { apiFetch } from "../config/api";
import { formatApiErrorMessage, toastTypeForError } from "../lib/apiErrors";

export default function useGoalPlan(userId, showToast) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const simulate = async ({ goal_name, target_amount, time_years }) => {
    const amount = parseFloat(target_amount);
    const years = parseFloat(time_years);
    if (!target_amount || isNaN(amount) || amount <= 0) {
      showToast?.("Please enter a valid goal amount", "error");
      return;
    }
    if (!time_years || isNaN(years) || years < 0.5) {
      showToast?.("Target horizon must be at least 0.5 years", "error");
      return;
    }
    setLoading(true);
    try {
      const data = await apiFetch("/goal-plan", {
        method: "POST",
        body: JSON.stringify({
          user_id: userId,
          goal_name: (goal_name || "").trim() || "My Goal",
          target_amount: amount,
          time_years: years,
        }),
      });
      setResult(data);
    } catch (e) {
      const type = toastTypeForError(e) || "error";
      showToast?.(formatApiErrorMessage(e, "Could not run simulation"), type);
    } finally {
      setLoading(false);
    }
  };

  return { result, loading, simulate };
}
