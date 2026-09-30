import React, { useState } from "react";
import { Link } from "react-router-dom";
import StatCard from "../components/StatCard.jsx";
import TransactionTable from "../components/TransactionTable.jsx";
import { EmptyState, ErrorState, Loading } from "../components/States.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { api } from "../services/api.js";
import {
  ActivityIcon,
  AlertTriangleIcon,
  ArrowUpRightIcon,
  CheckCircleIcon,
  CreditCardIcon,
  RefreshCwIcon,
  RulesIcon,
  ShieldLogoIcon,
} from "../components/Icons.jsx";
import { RuleChip } from "../components/Badges.jsx";

export default function Dashboard() {
  const stats = useAsync(() => api.stats(), []);
  const rules = useAsync(() => api.rules(), []);
  const [seeding, setSeeding] = useState(false);
  const [seedMsg, setSeedMsg] = useState(null);
  const [seedErr, setSeedErr] = useState(null);

  async function seed() {
    setSeeding(true);
    setSeedErr(null);
    setSeedMsg(null);
    try {
      const res = await api.seed();
      setSeedMsg(res.message);
      stats.reload();
    } catch (e) {
      setSeedErr(e.message);
    } finally {
      setSeeding(false);
    }
  }

  const s = stats.data;

  // Calculate live breakdown percentages for risk distribution
  const total = s?.total_transactions || 0;
  const highCount = s?.high_risk_transactions || 0;
  const medCount = s?.medium_risk_transactions || 0;
  const lowCount = Math.max(0, total - (highCount + medCount));

  const highPct = total > 0 ? Math.round((highCount / total) * 100) : 0;
  const medPct = total > 0 ? Math.round((medCount / total) * 100) : 0;
  const lowPct = total > 0 ? Math.round((lowCount / total) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Header Section */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-slate-800/80 pb-5">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-extrabold tracking-tight text-slate-100 font-sans">
              Fraud Monitoring Center
            </h1>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-cyan-400">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
              LIVE SOC
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400 font-medium">
            Real-time transaction risk intelligence & automated threat evaluation console
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={seed}
            disabled={seeding}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 hover:border-slate-600 px-4 py-2 text-xs font-semibold text-slate-200 transition-all shadow-md disabled:opacity-50"
          >
            <RefreshCwIcon className={`w-3.5 h-3.5 text-cyan-400 ${seeding ? "animate-spin" : ""}`} />
            <span>{seeding ? "Seeding Engine..." : "Seed Demo Data"}</span>
          </button>
        </div>
      </div>

      {seedMsg && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-xs text-emerald-300 flex items-center gap-2" role="status">
          <CheckCircleIcon className="w-4 h-4 text-emerald-400 flex-shrink-0" />
          <span>{seedMsg}</span>
        </div>
      )}

      {seedErr && <ErrorState message={seedErr} />}
      {stats.loading && !s && <Loading label="Fetching enterprise risk telemetry..." />}
      {stats.error && <ErrorState message={stats.error} onRetry={stats.reload} />}

      {s && (
        <>
          {/* Top Metric Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              label="TOTAL TRANSACTIONS"
              value={s.total_transactions}
              tone="default"
              icon={CreditCardIcon}
              hint="Monitored by rule engine"
            />
            <StatCard
              label="FLAGGED TRANSACTIONS"
              value={s.flagged_transactions}
              tone="warn"
              icon={AlertTriangleIcon}
              hint="Triggered risk rules"
            />
            <StatCard
              label="HIGH RISK ALERTS"
              value={s.high_risk_transactions}
              tone="danger"
              icon={ActivityIcon}
              hint="Requires urgent investigation"
            />
            <StatCard
              label="PENDING REVIEWS"
              value={s.pending_reviews}
              tone="warn"
              icon={ShieldLogoIcon}
              hint="Awaiting reviewer decision"
            />
          </div>

          {/* Live Risk Overview Section */}
          <div className="rounded-xl border border-slate-800 bg-[#111726] p-5 shadow-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
              <div>
                <h2 className="text-sm font-bold tracking-wide text-slate-200 uppercase font-mono">
                  LIVE RISK OVERVIEW
                </h2>
                <p className="text-xs text-slate-400">Distribution of evaluated transactions by risk level</p>
              </div>
              <span className="text-xs text-slate-400 font-mono">Total Evaluated: {total.toLocaleString()}</span>
            </div>

            {/* Counts Grid */}
            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg border border-emerald-900/40 bg-emerald-950/20 p-3.5 text-center">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-emerald-400">LOW RISK</p>
                <p className="mt-1 text-2xl font-extrabold text-emerald-300 font-mono">{lowCount.toLocaleString()}</p>
                <p className="mt-0.5 text-[11px] text-emerald-500 font-mono">{lowPct}% of total</p>
              </div>

              <div className="rounded-lg border border-amber-900/40 bg-amber-950/20 p-3.5 text-center">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-amber-400">MEDIUM RISK</p>
                <p className="mt-1 text-2xl font-extrabold text-amber-300 font-mono">{medCount.toLocaleString()}</p>
                <p className="mt-0.5 text-[11px] text-amber-500 font-mono">{medPct}% of total</p>
              </div>

              <div className="rounded-lg border border-red-900/40 bg-red-950/20 p-3.5 text-center relative overflow-hidden">
                <div className="absolute top-0 right-0 w-2 h-2 rounded-full bg-red-500 animate-ping m-2" />
                <p className="text-[11px] font-semibold uppercase tracking-wider text-red-400">HIGH RISK</p>
                <p className="mt-1 text-2xl font-extrabold text-red-400 font-mono">{highCount.toLocaleString()}</p>
                <p className="mt-0.5 text-[11px] text-red-400/80 font-mono">{highPct}% of total</p>
              </div>
            </div>

            {/* Distribution Bar */}
            <div className="space-y-1.5 pt-1">
              <div className="h-3 w-full overflow-hidden rounded-full bg-slate-900 flex border border-slate-800">
                <div style={{ width: `${lowPct}%` }} className="bg-emerald-500 transition-all duration-500" title={`Low Risk: ${lowPct}%`} />
                <div style={{ width: `${medPct}%` }} className="bg-amber-500 transition-all duration-500" title={`Medium Risk: ${medPct}%`} />
                <div style={{ width: `${highPct}%` }} className="bg-red-500 transition-all duration-500" title={`High Risk: ${highPct}%`} />
              </div>
              <div className="flex justify-between text-[10px] text-slate-400 font-mono px-0.5">
                <span className="text-emerald-400">● Low ({lowPct}%)</span>
                <span className="text-amber-400">● Medium ({medPct}%)</span>
                <span className="text-red-400">● High ({highPct}%)</span>
              </div>
            </div>
          </div>

          {/* Recent Suspicious Transactions Table */}
          <section className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-100">Recent High-Risk & Flagged Transactions</h2>
                <p className="text-xs text-slate-400">Latest transactions requiring analyst review</p>
              </div>
              <Link
                to="/flagged"
                className="inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300 hover:underline"
              >
                <span>View All Flagged Alerts</span>
                <ArrowUpRightIcon className="w-3.5 h-3.5" />
              </Link>
            </div>

            {s.total_transactions === 0 ? (
              <EmptyState title="No transactions detected in database">
                Click “Seed Demo Data” above to populate realistic fraud scenarios and live transactions.
              </EmptyState>
            ) : s.recent_suspicious.length === 0 ? (
              <EmptyState title="No suspicious transactions flagged right now">
                All monitored transactions are currently within configured risk thresholds.
              </EmptyState>
            ) : (
              <TransactionTable items={s.recent_suspicious} />
            )}
          </section>
        </>
      )}

      {/* Active Fraud Rules Catalog */}
      <section className="space-y-3 border-t border-slate-800/80 pt-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2">
              <RulesIcon className="w-4 h-4 text-cyan-400" />
              <span>Active Fraud Detection Rules</span>
            </h2>
            <p className="text-xs text-slate-400">Configured engine heuristics & point weights</p>
          </div>
          <Link to="/rules" className="text-xs font-semibold text-cyan-400 hover:underline">
            View Rule Specs →
          </Link>
        </div>

        {rules.error && <ErrorState message={rules.error} onRetry={rules.reload} />}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {(rules.data || []).map((r) => (
            <div
              key={r.name}
              className="rounded-xl border border-slate-800 bg-[#111726] p-4 shadow-lg flex flex-col justify-between hover:border-slate-700 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-2 mb-2">
                  <span className="font-mono text-xs font-bold text-cyan-400 tracking-wide">
                    {r.name}
                  </span>
                  <span className="rounded bg-red-950/80 border border-red-800/60 px-2 py-0.5 text-[11px] font-mono font-bold text-red-400">
                    +{r.score} PTS
                  </span>
                </div>
                <p className="text-xs text-slate-300 leading-relaxed">{r.description}</p>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-800/60 flex flex-wrap gap-1 text-[10px] font-mono text-slate-400">
                {Object.entries(r.parameters || {}).map(([k, v]) => (
                  <span key={k} className="rounded bg-slate-900 px-1.5 py-0.5 border border-slate-800">
                    {k}: <strong className="text-slate-200">{v}</strong>
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
