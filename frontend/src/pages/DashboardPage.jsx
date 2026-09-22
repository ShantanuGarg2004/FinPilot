import { useToast } from "../components/toast-context";
import useReport from "../hooks/useReport";
import { compactINR, formatINR, scoreStatus } from "../lib/format";
import Icon from "../components/Icon";
import Button from "../components/Button";
import Spinner from "../components/Spinner";
import GlassPanel from "../components/GlassPanel";
import GaugeRing from "../components/GaugeRing";
import StatCard from "../components/StatCard";
import LoadErrorBanner from "../components/LoadErrorBanner";
import PillarPerformance from "../sections/shared/PillarPerformance";

function InsightCard({ icon, tone, title, text }) {
  const border = { error: "border-error", primary: "border-primary", tertiary: "border-tertiary" }[tone];
  const color = { error: "text-error", primary: "text-primary", tertiary: "text-tertiary" }[tone];
  return (
    <div className={`bg-surface-container-low px-md py-md rounded-lg border-l-2 ${border} hover:bg-surface-container-high transition-all`}>
      <div className="flex gap-sm">
        <Icon name={icon} size={16} fill className={`${color} shrink-0 mt-0.5`} />
        <div className="min-w-0">
          <h4 className="text-[12px] font-semibold text-on-surface">{title}</h4>
          <p className="text-[12px] text-on-surface-variant mt-1 leading-relaxed">{text}</p>
        </div>
      </div>
    </div>
  );
}

export default function DashboardPage({ userId, user, onNavigate }) {
  const showToast = useToast();
  const { report, fetching, generating, generate, loadError, retryLoad } = useReport(userId, showToast);

  const health = report?.health || {};
  const status = scoreStatus(health.score || 0);

  const income = Number(user?.income) || 0;
  const expenses = Number(user?.expenses) || 0;
  const savings = Number(user?.savings) || 0;
  const annualSavings = savings * 12;
  const monthlySurplus = income - expenses;
  const savingsRate = health.savings_ratio ?? (income ? Math.round((savings / income) * 100) : 0);

  const warnings = health.warnings || [];
  const insights = health.insights || [];

  const missingReport = !report && (loadError?.code === "not_found" || loadError?.status === 404 || (!loadError && !fetching));
  const blockedLoad = !report && loadError && loadError.code !== "not_found" && loadError.status !== 404;

  return (
    <div className="grid grid-cols-12 gap-xl">
      <div className="col-span-12 lg:col-span-8 space-y-xl">
        <LoadErrorBanner error={loadError} onRetry={retryLoad} resource="health score" />

        {/* Health score + pillars — airy upper band */}
        <GlassPanel as="section" className="p-lg md:p-xl">
          {fetching ? (
            <div className="flex items-center gap-2 text-on-surface-variant text-[12px] py-lg">
              <Spinner size={14} /> Loading health score…
            </div>
          ) : blockedLoad ? (
            <div className="flex flex-col sm:flex-row items-center gap-xl py-md text-center sm:text-left">
              <GaugeRing
                value={0}
                size={128}
                stroke={8}
                color="#2A2A32"
                label={<Icon name="cloud_off" size={28} className="text-warning" />}
              />
              <div className="flex-1 space-y-md">
                <div>
                  <h3 className="font-headline-md text-headline-md text-on-surface">Couldn’t load health score</h3>
                  <p className="text-[13px] text-on-surface-variant mt-2 leading-relaxed max-w-md">
                    {loadError?.code === "rate_limit_exceeded"
                      ? "Rate limited while fetching your saved report. Retry shortly — regenerating is usually unnecessary."
                      : loadError?.message || "Something went wrong loading your saved report."}
                  </p>
                </div>
                <Button variant="subtle" size="sm" icon="refresh" onClick={retryLoad}>
                  Retry load
                </Button>
              </div>
            </div>
          ) : missingReport ? (
            <div className="flex flex-col sm:flex-row items-center gap-xl py-md text-center sm:text-left">
              <GaugeRing
                value={0}
                size={128}
                stroke={8}
                color="#2A2A32"
                label={<Icon name="query_stats" size={28} className="text-on-surface-variant" />}
              />
              <div className="flex-1 space-y-md">
                <div>
                  <h3 className="font-headline-md text-headline-md text-on-surface">No health score yet</h3>
                  <p className="text-[13px] text-on-surface-variant mt-2 leading-relaxed max-w-md">
                    Generate an AI advisory report to unlock your score and pillar breakdown.
                  </p>
                </div>
                <Button variant="primary" size="sm" icon="auto_awesome" loading={generating} loadingText="Generating…" onClick={generate}>
                  Generate Report
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col lg:flex-row lg:items-center gap-xl lg:gap-2xl">
              <div className="shrink-0 flex justify-center lg:justify-start lg:pr-md lg:border-r lg:border-outline/80">
                <GaugeRing value={health.score || 0} size={148} stroke={11} gradient sublabel="Health Score" />
              </div>

              <div className="flex-1 w-full min-w-0 space-y-md">
                <div className="flex items-end justify-between gap-md pb-sm">
                  <h3 className="font-headline-md text-headline-md text-on-surface">Pillar Performance</h3>
                  <span className="font-label-sm text-label-sm shrink-0 pb-0.5" style={{ color: status.color }}>
                    {status.label}
                  </span>
                </div>
                <PillarPerformance pillarScores={health.pillar_scores} variant="grid" />
              </div>
            </div>
          )}
        </GlassPanel>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-lg">
          <StatCard
            icon="account_balance_wallet"
            label="Annual Savings"
            value={compactINR(annualSavings)}
            sub={`₹${formatINR(savings)} / month`}
            subIcon="trending_up"
            subColor="text-tertiary"
          />
          <StatCard
            icon="savings"
            label="Monthly Surplus"
            value={`₹${formatINR(monthlySurplus)}`}
            sub={`${savingsRate}% savings rate`}
          />
        </div>
      </div>

      <div className="col-span-12 lg:col-span-4 space-y-xl">
        <section className="space-y-md">
          <div className="flex items-center justify-between">
            <h3 className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">Critical Insights</h3>
            {warnings.length > 0 && (
              <span className="px-1.5 py-0.5 bg-error-container text-on-error-container text-[10px] font-bold rounded uppercase">
                {warnings.length}
              </span>
            )}
          </div>
          <div className="space-y-sm">
            {warnings.length === 0 && insights.length === 0 ? (
              <GlassPanel className="p-md text-[12px] text-on-surface-variant leading-relaxed">
                {report ? "No critical insights — finances look balanced." : "Generate a report to surface AI insights."}
              </GlassPanel>
            ) : (
              <>
                {warnings.slice(0, 3).map((w, i) => (
                  <InsightCard key={`w${i}`} icon="warning" tone="error" title="Area to Improve" text={w} />
                ))}
                {insights.slice(0, 2).map((it, i) => (
                  <InsightCard key={`i${i}`} icon="new_releases" tone="tertiary" title="Strength" text={it} />
                ))}
              </>
            )}
          </div>
        </section>

        <GlassPanel as="section" className="p-lg space-y-md">
          <h3 className="font-headline-md text-headline-md text-on-surface">Quick Actions</h3>
          <div className="space-y-sm">
            {[
              { page: "advisory", icon: "analytics", label: "Detailed Report", primary: false },
              { page: "chat", icon: "smart_toy", label: "AI Chat", primary: true },
              { page: "goals", icon: "insights", label: "Goal Simulator", primary: false },
            ].map((a) => (
              <button
                key={a.page}
                onClick={() => onNavigate(a.page)}
                className={[
                  "w-full flex items-center justify-between px-md py-3 rounded-lg transition-all group",
                  a.primary
                    ? "bg-primary text-on-primary hover:bg-primary-container"
                    : "bg-surface-container text-on-surface hover:bg-primary hover:text-on-primary",
                ].join(" ")}
              >
                <div className="flex items-center gap-sm">
                  <Icon name={a.icon} size={18} fill={a.primary} />
                  <span className="text-[13px] font-semibold">{a.label}</span>
                </div>
                <Icon name="arrow_forward" size={16} className="group-hover:translate-x-0.5 transition-transform" />
              </button>
            ))}
          </div>
        </GlassPanel>
      </div>
    </div>
  );
}
