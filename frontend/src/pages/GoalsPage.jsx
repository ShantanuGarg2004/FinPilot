import { useState } from "react";
import { useToast } from "../components/toast-context";
import useGoalPlan from "../hooks/useGoalPlan";
import { compactINR, formatINR } from "../lib/format";
import Icon from "../components/Icon";
import Button from "../components/Button";
import GlassPanel from "../components/GlassPanel";
import ProgressBar from "../components/ProgressBar";
import StatCard from "../components/StatCard";
import { TextField, RangeField } from "../components/Field";

const SCENARIO_META = {
  Conservative: { icon: "shield", tag: "Low Risk", color: "#6B9BCF", recommended: false },
  Balanced: { icon: "balance", tag: "Optimum", color: "#18B981", recommended: true },
  Aggressive: { icon: "rocket_launch", tag: "High Risk", color: "#F4B740", recommended: false },
};

function ScenarioCard({ sc }) {
  const meta = SCENARIO_META[sc.scenario] || { icon: "insights", tag: "", color: "#18B981" };
  const coverage = sc.feasible ? 100 : null;
  return (
    <div
      className={[
        "rounded-lg p-md transition-all border relative",
        meta.recommended
          ? "bg-surface-container-high border-primary/30"
          : "bg-surface-container-low border-outline hover:border-primary/40",
      ].join(" ")}
    >
      {meta.recommended && (
        <div className="absolute -top-2 left-1/2 -translate-x-1/2 bg-primary text-on-primary text-[9px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
          Recommended
        </div>
      )}
      <div className="flex justify-between items-start mb-sm">
        <div className={`p-1.5 rounded-md ${meta.recommended ? "bg-primary/20" : "bg-surface-container-highest"}`}>
          <Icon name={meta.icon} size={18} style={{ color: meta.color }} />
        </div>
        <span
          className={`text-[10px] px-2 py-0.5 rounded-full ${
            meta.recommended ? "bg-primary/10 text-primary" : "bg-surface-container-highest text-on-surface-variant"
          }`}
        >
          {meta.tag}
        </span>
      </div>
      <h4 className="font-headline-md text-headline-md mb-sm text-on-surface">{sc.scenario}</h4>
      <div className="space-y-1.5">
        <div className="flex justify-between border-b border-outline/60 pb-1.5">
          <span className="text-on-surface-variant text-[12px]">Monthly SIP</span>
          <span className="text-[13px] font-semibold" style={{ color: meta.color }}>
            ₹{formatINR(Math.round(sc.monthly_needed || 0))}
          </span>
        </div>
        <div className="flex justify-between border-b border-outline/60 pb-1.5">
          <span className="text-on-surface-variant text-[12px]">Assumed CAGR</span>
          <span className="text-[13px] font-semibold text-on-surface">{sc.cagr}</span>
        </div>
        <div className="pt-1">
          <ProgressBar pct={coverage ?? 60} color={meta.color} height={4} />
          <p className="text-[10px] mt-1 text-right" style={{ color: sc.feasible ? meta.color : "#9AA8BC" }}>
            {sc.feasible ? "✓ Feasible now" : `Reach in ${sc.recommended_timeline}`}
          </p>
        </div>
      </div>
    </div>
  );
}

export default function GoalsPage({ userId, userGoal }) {
  const showToast = useToast();
  const { result, loading, simulate } = useGoalPlan(userId, showToast);
  const [form, setForm] = useState({ goal_name: "", target_amount: "", time_years: 5 });
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const fScore = result?.feasibility_score ?? 0;
  const fColor = fScore >= 75 ? "#18B981" : fScore >= 50 ? "#F4B740" : "#F06A6A";

  return (
    <div className="space-y-gutter">
      {/* Definition + Confidence */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-gutter items-stretch">
        <div className="lg:col-span-4 bg-surface-container-low border border-outline rounded-lg p-md space-y-sm">
          <div className="flex items-center gap-1.5">
            <Icon name="track_changes" size={16} className="text-primary" />
            <h3 className="font-headline-md text-headline-md text-on-surface">Goal Definition</h3>
          </div>
          <p className="text-[11px] text-on-surface-variant truncate">{userGoal || `Profile #${userId}`}</p>

          <TextField
            label="Goal Name"
            value={form.goal_name}
            onChange={(e) => set("goal_name", e.target.value)}
            placeholder="e.g. Retirement Home"
          />
          <TextField
            label="Target Amount (₹)"
            type="number"
            prefix="₹"
            value={form.target_amount}
            onChange={(e) => set("target_amount", e.target.value)}
            placeholder="75,00,000"
          />
          <RangeField
            label="Horizon (Years)"
            min={1}
            max={40}
            step={1}
            value={form.time_years}
            displayValue={form.time_years}
            onChange={(e) => set("time_years", Number(e.target.value))}
          />
          <Button
            variant="primary"
            className="w-full"
            icon="auto_awesome"
            iconFill
            loading={loading}
            loadingText="Running Simulation…"
            onClick={() => simulate(form)}
          >
            Calculate Pilot Path
          </Button>
        </div>

        <div className="lg:col-span-8 bg-surface-container-low border border-outline rounded-lg p-md relative overflow-hidden flex flex-col justify-center items-center text-center min-h-[180px]">
          <div
            className="absolute inset-0 opacity-40"
            style={{
              backgroundImage:
                "radial-gradient(ellipse 60% 60% at 50% 40%, rgba(229,196,135,0.10) 0%, transparent 60%)",
            }}
          />
          {result ? (
            <div className="relative z-10 space-y-2">
              <p className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
                Pilot AI Confidence Score
              </p>
              <div className="text-[48px] font-bold leading-none tracking-tighter" style={{ color: fColor }}>
                {fScore}
                <span className="text-headline-md">%</span>
              </div>
              <p className="text-[13px] text-on-surface-variant max-w-md mx-auto">
                {result.feasible ? "Your goal is " : "There's a gap — your goal is "}
                <span className="font-semibold" style={{ color: fColor }}>
                  {result.feasibility_label}
                </span>
                . {result.scenario_message}
              </p>
              {result.recommended_timeline && !result.feasible && (
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full border border-primary/20 bg-primary/10">
                  <span className="text-[11px] text-primary font-semibold">Achievable in</span>
                  <span className="text-[12px] text-primary-fixed font-bold">{result.recommended_timeline}</span>
                </div>
              )}
            </div>
          ) : (
            <div className="relative z-10 space-y-1.5">
              <Icon name="insights" size={32} className="text-on-surface-variant" />
              <p className="text-[13px] text-on-surface-variant max-w-sm mx-auto">
                Define a goal and run the simulation to see your confidence score.
              </p>
            </div>
          )}
        </div>
      </section>

      {result && (
        <>
          {/* Scenarios */}
          {result.scenarios?.length > 0 && (
            <section className="grid grid-cols-1 md:grid-cols-3 gap-gutter">
              {result.scenarios.map((sc) => (
                <ScenarioCard key={sc.scenario} sc={sc} />
              ))}
            </section>
          )}

          {/* Gap analysis */}
          <section className="grid grid-cols-1 md:grid-cols-3 gap-md">
            <StatCard
              icon="savings"
              label="Current Saving"
              value={`₹${formatINR(Math.round(result.current_monthly_saving || 0))}`}
              sub="/month"
            />
            <StatCard
              icon="payments"
              label="Required SIP"
              value={`₹${formatINR(Math.round(result.required_monthly_saving || 0))}`}
              sub={`@ ${result.cagr_moderate} CAGR`}
              accent
            />
            <StatCard
              icon={result.feasible ? "trending_up" : "warning"}
              label={result.feasible ? "Monthly Surplus" : "Monthly Gap"}
              value={`₹${formatINR(Math.round((result.feasible ? result.monthly_surplus : result.monthly_gap) || 0))}`}
              sub="/month"
              subColor={result.feasible ? "text-tertiary" : "text-error"}
            />
          </section>

          {/* Projection */}
          <section className="grid grid-cols-1 md:grid-cols-2 gap-md">
            <StatCard
              icon="account_balance"
              label="Projected Corpus"
              value={compactINR(result.projected_value || 0)}
              sub="at current savings + moderate CAGR"
            />
            <StatCard
              icon="target"
              label="Goal Coverage"
              value={`${result.coverage_pct}%`}
              sub="of target amount covered"
              accent={result.coverage_pct >= 80}
            />
          </section>

          {/* Strategy */}
          <GlassPanel className="p-md bg-primary/[0.04] border-primary/15">
            <div className="font-label-sm text-label-sm uppercase text-primary mb-sm flex items-center gap-1.5">
              <Icon name="lightbulb" size={14} fill /> Recommended Investment Strategy
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-sm mb-sm">
              <div className="p-sm bg-surface-container-low rounded-md border border-outline/60">
                <div className="font-label-sm text-label-sm uppercase text-on-surface-variant mb-0.5">Primary</div>
                <div className="text-[12px] text-on-surface font-medium">
                  {result.investment_strategy || result.investment_suggestion}
                </div>
              </div>
              <div className="p-sm bg-surface-container-low rounded-md border border-outline/60">
                <div className="font-label-sm text-label-sm uppercase text-on-surface-variant mb-0.5">Secondary</div>
                <div className="text-[12px] text-on-surface font-medium">{result.secondary_suggestion}</div>
              </div>
            </div>
            {result.rationale && (
              <div className="text-[12px] text-on-surface-variant leading-relaxed p-sm bg-surface-container-low rounded-md border-l-2 border-primary/40">
                {result.rationale}
              </div>
            )}
          </GlassPanel>
        </>
      )}
    </div>
  );
}
