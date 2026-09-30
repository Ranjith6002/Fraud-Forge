import React, { useState } from "react";
import { Link, useParams } from "react-router-dom";
import ConfirmDialog from "../components/ConfirmDialog.jsx";
import { RiskBadge, StatusBadge } from "../components/Badges.jsx";
import { ErrorState, Loading } from "../components/States.jsx";
import RiskScoreGauge from "../components/RiskScoreGauge.jsx";
import { useAsync } from "../hooks/useAsync.js";
import { api } from "../services/api.js";
import { formatDate, formatMoney, ruleLabel } from "../utils/format.js";
import {
  ActivityIcon,
  AlertTriangleIcon,
  AuditIcon,
  CheckCircleIcon,
  ClockIcon,
  CreditCardIcon,
  MapPinIcon,
  UserIcon,
} from "../components/Icons.jsx";

function MetadataItem({ label, icon: Icon, children }) {
  return (
    <div className="rounded-lg bg-slate-900/60 p-3 border border-slate-800/80">
      <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-slate-400">
        {Icon && <Icon className="w-3.5 h-3.5 text-cyan-400" />}
        <span>{label}</span>
      </div>
      <div className="mt-1 text-sm font-semibold text-slate-100 font-mono">
        {children ?? <span className="text-slate-600 font-normal">—</span>}
      </div>
    </div>
  );
}

const NOTIFICATION_MAP = {
  SENT: { text: "AWS SNS / Alert sent successfully", cls: "text-emerald-400 border-emerald-900/50 bg-emerald-950/20" },
  FAILED: { text: "Alert notification attempt failed", cls: "text-red-400 border-red-900/50 bg-red-950/20" },
  SKIPPED: { text: "Alert logged locally (AWS credentials not active)", cls: "text-amber-400 border-amber-900/50 bg-amber-950/20" },
  NOT_REQUIRED: { text: "No alert triggered (risk score below high threshold)", cls: "text-slate-400 border-slate-800 bg-slate-900/40" },
};

export default function TransactionDetails() {
  const { id } = useParams();
  const { data: t, loading, error, reload } = useAsync(() => api.getTransaction(id), [id]);
  const [reviewer, setReviewer] = useState("admin");
  const [comment, setComment] = useState("");
  const [pending, setPending] = useState(null); // "review" | "clear"
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  if (loading && !t) return <Loading label="Retrieving transaction investigation files..." />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  if (!t) return null;

  const notif = NOTIFICATION_MAP[t.notification_status] || NOTIFICATION_MAP.NOT_REQUIRED;
  const canAct = reviewer.trim().length > 0;

  async function handleConfirmAction() {
    setBusy(true);
    setActionError(null);
    try {
      const body = { reviewer: reviewer.trim(), comment: comment.trim() || null };
      if (pending === "review") {
        await api.review(t.transaction_id, body);
        setToastMsg("Transaction successfully marked as REVIEWED.");
      } else {
        await api.clear(t.transaction_id, body);
        setToastMsg("Transaction CLEARED (Marked as legitimate).");
      }
      setComment("");
      setPending(null);
      reload();
    } catch (e) {
      setActionError(e.message);
      setPending(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Navigation Back Link */}
      <div className="flex items-center justify-between">
        <Link
          to="/flagged"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-cyan-400 hover:text-cyan-300 transition-colors"
        >
          <span>← Back to Fraud Alerts Console</span>
        </Link>
        <span className="text-xs text-slate-400 font-mono">Investigation ID: {t.transaction_id}</span>
      </div>

      {/* Main Header Banner */}
      <div className="rounded-xl border border-slate-800 bg-[#111726] p-6 shadow-xl flex flex-col md:flex-row md:items-center md:justify-between gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold uppercase tracking-widest text-cyan-400">
              TRANSACTION INVESTIGATION
            </span>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="font-mono text-3xl font-extrabold tracking-tight text-slate-100">
              {t.transaction_id}
            </h1>
            <RiskBadge level={t.risk_level} size="lg" />
            <StatusBadge status={t.review_status} />
          </div>
          <p className="text-xs text-slate-400 font-mono">
            Recorded at {formatDate(t.timestamp)} • User ID: <strong className="text-slate-200">{t.user_id}</strong>
          </p>
        </div>

        {/* Circular Risk Meter */}
        <div className="flex items-center justify-center md:justify-end flex-shrink-0">
          <RiskScoreGauge score={t.risk_score} level={t.risk_level} size={150} />
        </div>
      </div>

      {/* Action Toast Feedback */}
      {toastMsg && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-xs font-medium text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircleIcon className="w-4 h-4 text-emerald-400" />
            <span>{toastMsg}</span>
          </div>
          <button onClick={() => setToastMsg(null)} className="text-slate-400 hover:text-white font-bold">×</button>
        </div>
      )}

      {/* Grid: Transaction Details + Reviewer Decision */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left 2 Cols: Transaction Metadata */}
        <section className="rounded-xl border border-slate-800 bg-[#111726] p-5 shadow-xl space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-sm font-bold tracking-wide text-slate-200 uppercase font-mono flex items-center gap-2">
              <CreditCardIcon className="w-4 h-4 text-cyan-400" />
              <span>Transaction Telemetry Data</span>
            </h2>
            <span className="text-xs font-mono text-slate-400">{t.currency} Currency</span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <MetadataItem label="Transaction ID">{t.transaction_id}</MetadataItem>
            <MetadataItem label="User ID" icon={UserIcon}>{t.user_id}</MetadataItem>
            <MetadataItem label="Amount" icon={ActivityIcon}>
              <span className="text-base text-cyan-300 font-bold">{formatMoney(t.amount, t.currency)}</span>
            </MetadataItem>
            <MetadataItem label="Merchant">{t.merchant || "N/A"}</MetadataItem>
            <MetadataItem label="Location" icon={MapPinIcon}>{t.location || "N/A"}</MetadataItem>
            <MetadataItem label="Coordinates">
              {t.latitude != null && t.longitude != null ? (
                <span>{t.latitude.toFixed(4)}, {t.longitude.toFixed(4)}</span>
              ) : "N/A"}
            </MetadataItem>
            <MetadataItem label="Timestamp" icon={ClockIcon}>{formatDate(t.timestamp)}</MetadataItem>
            <MetadataItem label="Device ID">{t.device_id || "N/A"}</MetadataItem>
            <MetadataItem label="Notification Status">
              <span className="text-xs">{t.notification_status}</span>
            </MetadataItem>
          </div>

          {/* Notification telemetry status box */}
          <div className={`rounded-lg border p-3 text-xs leading-relaxed ${notif.cls}`}>
            <strong className="font-semibold block mb-0.5">Automated Alert Dispatch: {notif.text}</strong>
            {t.notification_detail && (
              <span className="text-[11px] opacity-80 font-mono block mt-1">{t.notification_detail}</span>
            )}
          </div>
        </section>

        {/* Right Col: Reviewer Decision Panel */}
        <section className="rounded-xl border border-slate-800 bg-[#111726] p-5 shadow-xl space-y-4 flex flex-col justify-between">
          <div className="space-y-3">
            <div className="border-b border-slate-800 pb-3">
              <h2 className="text-sm font-bold tracking-wide text-slate-200 uppercase font-mono flex items-center gap-2">
                <AuditIcon className="w-4 h-4 text-cyan-400" />
                <span>Reviewer Decision Workspace</span>
              </h2>
              <p className="text-[11px] text-slate-400 mt-0.5">Submit official audit action for this record</p>
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1" htmlFor="reviewer">
                Reviewer Username
              </label>
              <input
                id="reviewer"
                value={reviewer}
                onChange={(e) => setReviewer(e.target.value)}
                maxLength={64}
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-mono text-slate-200 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1" htmlFor="comment">
                Investigation Notes / Audit Comment
              </label>
              <textarea
                id="comment"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={4}
                maxLength={2000}
                placeholder="e.g. Spoke with customer via phone verification. Confirmed legitimate travel."
                className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-200 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 leading-relaxed"
              />
            </div>

            {actionError && (
              <p className="rounded-md border border-red-800 bg-red-950/40 p-2.5 text-xs text-red-300" role="alert">
                {actionError}
              </p>
            )}
          </div>

          <div className="space-y-2 pt-2 border-t border-slate-800">
            <button
              onClick={() => {
                setToastMsg(null);
                setPending("review");
              }}
              disabled={!canAct || t.review_status === "REVIEWED"}
              className="w-full rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold py-2.5 text-xs tracking-wider uppercase shadow-lg shadow-cyan-950 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <span>Mark as Reviewed</span>
            </button>

            <button
              onClick={() => {
                setToastMsg(null);
                setPending("clear");
              }}
              disabled={!canAct || t.review_status === "CLEARED"}
              className="w-full rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold py-2.5 text-xs tracking-wider uppercase shadow-lg shadow-emerald-950 transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              <span>Clear Transaction (Legitimate)</span>
            </button>

            <p className="text-[10px] text-slate-500 text-center pt-1 font-mono">
              Audit immutable log: Fraud flags remain saved for compliance.
            </p>
          </div>
        </section>
      </div>

      {/* WHY WAS THIS TRANSACTION FLAGGED? Section */}
      <section className="rounded-xl border border-slate-800 bg-[#111726] p-5 shadow-xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 font-mono">
              <AlertTriangleIcon className="w-5 h-5 text-amber-400" />
              <span>WHY WAS THIS TRANSACTION FLAGGED?</span>
            </h2>
            <p className="text-xs text-slate-400">Detailed rule breakdown evaluated by rule engine</p>
          </div>
          <span className="text-xs font-mono text-red-400 font-bold">{t.flags.length} Triggered Flag(s)</span>
        </div>

        {t.flags.length === 0 && (
          <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-6 text-center text-xs text-slate-400">
            No fraud rules were triggered for this transaction. Overall risk score is 0.
          </div>
        )}

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {t.rule_results.map((r) => {
            const isTriggered = r.triggered;
            return (
              <div
                key={r.rule}
                className={`rounded-xl border p-4 transition-all ${
                  isTriggered
                    ? "border-red-500/40 bg-red-950/20 shadow-lg shadow-red-950/30"
                    : "border-slate-800 bg-slate-900/30 opacity-70"
                }`}
              >
                <div className="flex items-start justify-between gap-2 border-b border-slate-800/80 pb-2 mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-base">
                      {isTriggered ? "⚡" : "◉"}
                    </span>
                    <span className="font-mono text-xs font-bold tracking-wide text-slate-100">
                      {ruleLabel(r.rule)}
                    </span>
                  </div>
                  <span
                    className={`font-mono text-xs font-extrabold ${
                      isTriggered ? "text-red-400" : "text-slate-500"
                    }`}
                  >
                    +{r.score} PTS
                  </span>
                </div>

                <div className="mt-2 space-y-1.5">
                  <span
                    className={`inline-block rounded px-2 py-0.5 text-[10px] font-mono font-bold tracking-wider uppercase ${
                      isTriggered
                        ? "bg-red-500/20 text-red-400 border border-red-500/30"
                        : "bg-slate-800 text-slate-400"
                    }`}
                  >
                    {isTriggered ? "TRIGGERED" : "NOT TRIGGERED"}
                  </span>
                  <p className="text-xs leading-relaxed text-slate-300 font-sans">
                    {isTriggered ? r.reason : r.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Audit Trail Section */}
      <section className="rounded-xl border border-slate-800 bg-[#111726] p-5 shadow-xl space-y-4">
        <div className="border-b border-slate-800 pb-3">
          <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 font-mono">
            <AuditIcon className="w-5 h-5 text-cyan-400" />
            <span>Audit Trail & Review History</span>
          </h2>
          <p className="text-xs text-slate-400">Historical reviewer decisions for regulatory compliance</p>
        </div>

        {t.reviews.length === 0 ? (
          <p className="text-xs text-slate-400 font-mono py-4 text-center">No reviewer actions recorded yet.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="min-w-full text-xs text-left">
              <thead className="bg-[#0F1420] text-slate-400 font-mono uppercase text-[11px] border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-4">Timestamp</th>
                  <th className="py-2.5 px-4">Reviewer</th>
                  <th className="py-2.5 px-4">Status Change</th>
                  <th className="py-2.5 px-4">Comments</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {[...t.reviews].reverse().map((r) => (
                  <tr key={r.id} className="hover:bg-slate-800/40">
                    <td className="py-3 px-4 text-slate-400 whitespace-nowrap">{formatDate(r.reviewed_at)}</td>
                    <td className="py-3 px-4 text-slate-200 font-bold">{r.reviewer}</td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <StatusBadge status={r.previous_status} />
                      <span className="mx-2 text-slate-500">→</span>
                      <StatusBadge status={r.status} />
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-sans">{r.comment || <span className="text-slate-600">—</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Confirmation Modal Dialog */}
      <ConfirmDialog
        open={pending !== null}
        title={pending === "review" ? "Mark Transaction as Reviewed?" : "Clear Transaction as Legitimate?"}
        message={
          pending === "review"
            ? `${t.transaction_id} will be updated to REVIEWED by analyst "${reviewer.trim()}".`
            : `${t.transaction_id} will be updated to CLEARED (Legitimate transaction). Original fraud flags remain in compliance audit history.`
        }
        confirmLabel={pending === "review" ? "Confirm Reviewed" : "Confirm Clear Transaction"}
        confirmVariant={pending === "review" ? "primary" : "emerald"}
        busy={busy}
        onConfirm={handleConfirmAction}
        onCancel={() => setPending(null)}
      />
    </div>
  );
}
