import React from 'react';
import { Link } from "react-router-dom";
import { formatDate, formatMoney } from "../utils/format";
import { RiskBadge, RuleChip, StatusBadge } from "./Badges";
import { ArrowUpRightIcon, MapPinIcon } from "./Icons";

function SortHeader({ label, field, sort, onSort }) {
  if (!onSort) return <span>{label}</span>;
  const active = sort?.by === field;
  return (
    <button
      type="button"
      onClick={() => onSort(field)}
      className="inline-flex items-center gap-1 font-semibold text-slate-400 hover:text-cyan-400 transition-colors uppercase tracking-wider text-[11px]"
    >
      <span>{label}</span>
      <span aria-hidden="true" className="text-[10px] text-cyan-500 font-bold">
        {active ? (sort.order === "asc" ? "▲" : "▼") : "↕"}
      </span>
    </button>
  );
}

export default function TransactionTable({ items, sort, onSort }) {
  const th = "whitespace-nowrap px-4 py-3.5 text-left text-[11px] font-semibold uppercase tracking-wider text-slate-400 border-b border-slate-800 bg-[#0F1420]";

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-800/80 bg-[#111726] shadow-xl">
      <table className="min-w-full divide-y divide-slate-800/60 text-sm text-left">
        <thead>
          <tr>
            <th className={th}>Transaction</th>
            <th className={th}>User</th>
            <th className={th}>
              <SortHeader label="Amount" field="amount" sort={sort} onSort={onSort} />
            </th>
            <th className={th}>Location</th>
            <th className={th}>
              <SortHeader label="Risk Score" field="risk_score" sort={sort} onSort={onSort} />
            </th>
            <th className={th}>Triggered Rules</th>
            <th className={th}>Status</th>
            <th className={th}>
              <SortHeader label="Time" field="created_at" sort={sort} onSort={onSort} />
            </th>
            <th className={`${th} text-right`}>Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/50">
          {items.map((t) => {
            const isHigh = t.risk_level === "HIGH" || t.risk_score >= 70;
            return (
              <tr
                key={t.transaction_id}
                className={`transition-colors hover:bg-slate-800/50 ${isHigh ? "bg-red-950/10 hover:bg-red-950/20" : ""}`}
              >
                {/* Transaction ID */}
                <td className="whitespace-nowrap px-4 py-3.5">
                  <Link
                    to={`/transactions/${encodeURIComponent(t.transaction_id)}`}
                    className="font-mono text-xs font-semibold text-cyan-400 hover:text-cyan-300 hover:underline flex items-center gap-1.5"
                  >
                    <span>{t.transaction_id}</span>
                  </Link>
                </td>

                {/* User ID */}
                <td className="whitespace-nowrap px-4 py-3.5 font-mono text-xs text-slate-300">
                  {t.user_id}
                </td>

                {/* Amount */}
                <td className="whitespace-nowrap px-4 py-3.5 font-semibold text-slate-100 tabular-nums">
                  {formatMoney(t.amount, t.currency)}
                </td>

                {/* Location */}
                <td className="whitespace-nowrap px-4 py-3.5 text-xs text-slate-400">
                  {t.location ? (
                    <span className="inline-flex items-center gap-1">
                      <MapPinIcon className="w-3.5 h-3.5 text-slate-500" />
                      {t.location}
                    </span>
                  ) : (
                    <span className="text-slate-600">—</span>
                  )}
                </td>

                {/* Risk Score & Badge */}
                <td className="whitespace-nowrap px-4 py-3.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={`font-mono text-sm font-bold tabular-nums ${
                        isHigh
                          ? "text-red-400"
                          : t.risk_level === "MEDIUM"
                          ? "text-amber-400"
                          : "text-emerald-400"
                      }`}
                    >
                      {t.risk_score}
                    </span>
                    <RiskBadge level={t.risk_level} size="sm" showDot={false} />
                  </div>
                </td>

                {/* Triggered Rules */}
                <td className="px-4 py-3.5">
                  <div className="flex flex-wrap gap-1 max-w-xs">
                    {t.triggered_rules && t.triggered_rules.length > 0 ? (
                      t.triggered_rules.map((r) => <RuleChip key={r} name={r} />)
                    ) : (
                      <span className="text-xs text-slate-500 font-mono">None</span>
                    )}
                  </div>
                </td>

                {/* Review Status */}
                <td className="whitespace-nowrap px-4 py-3.5">
                  <StatusBadge status={t.review_status} />
                </td>

                {/* Created At */}
                <td className="whitespace-nowrap px-4 py-3.5 text-xs text-slate-400 font-mono">
                  {formatDate(t.created_at)}
                </td>

                {/* Action */}
                <td className="whitespace-nowrap px-4 py-3.5 text-right">
                  <Link
                    to={`/transactions/${encodeURIComponent(t.transaction_id)}`}
                    className="inline-flex items-center gap-1 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1 text-xs font-medium text-slate-200 hover:bg-slate-700 hover:border-slate-600 hover:text-white transition-all shadow-sm"
                  >
                    <span>View</span>
                    <ArrowUpRightIcon className="w-3.5 h-3.5 text-cyan-400" />
                  </Link>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
