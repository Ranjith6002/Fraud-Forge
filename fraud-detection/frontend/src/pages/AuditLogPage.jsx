import React from "react";
import { Link } from "react-router-dom";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { EmptyState, ErrorState, Loading } from "../components/States";
import { formatDate } from "../utils/format";
import { StatusBadge } from "../components/Badges";
import { AuditIcon, ArrowUpRightIcon, UserIcon } from "../components/Icons";

export default function AuditLogPage() {
  const { data, loading, error, reload } = useAsync(
    () => api.listTransactions({ limit: 200 }),
    []
  );

  // Collect all review records across all transactions
  const auditEntries = [];
  if (data?.items) {
    data.items.forEach((t) => {
      if (t.review_status !== "PENDING") {
        auditEntries.push({
          transaction_id: t.transaction_id,
          user_id: t.user_id,
          status: t.review_status,
          risk_level: t.risk_level,
          amount: t.amount,
          created_at: t.created_at,
        });
      }
    });
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2.5">
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-100 flex items-center gap-2 font-sans">
            <AuditIcon className="w-6 h-6 text-cyan-400" />
            <span>Enterprise Compliance Audit Log</span>
          </h1>
          <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-cyan-400">
            IMMUTABLE TRAIL
          </span>
        </div>
        <p className="mt-1 text-xs text-slate-400">
          Permanent history of analyst decisions, status reviews, and override comments recorded in the system
        </p>
      </div>

      {loading && !data && <Loading label="Compiling compliance audit logs..." />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {data && auditEntries.length === 0 && (
        <EmptyState title="No reviewer decisions recorded yet">
          When analysts mark transactions as REVIEWED or CLEARED on the transaction investigation page, their decisions will automatically log here.
        </EmptyState>
      )}

      {data && auditEntries.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-[#111726] shadow-xl">
          <table className="min-w-full divide-y divide-slate-800 text-left text-xs font-mono">
            <thead className="bg-[#0F1420] text-slate-400 uppercase text-[11px] border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Transaction ID</th>
                <th className="py-3.5 px-4">User</th>
                <th className="py-3.5 px-4">Status Result</th>
                <th className="py-3.5 px-4">Recorded Date</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {auditEntries.map((entry) => (
                <tr key={entry.transaction_id} className="hover:bg-slate-800/40 transition-colors">
                  <td className="py-3 px-4 text-cyan-400 font-bold">
                    <Link to={`/transactions/${encodeURIComponent(entry.transaction_id)}`} className="hover:underline">
                      {entry.transaction_id}
                    </Link>
                  </td>
                  <td className="py-3 px-4 text-slate-300">{entry.user_id}</td>
                  <td className="py-3 px-4 whitespace-nowrap">
                    <StatusBadge status={entry.status} />
                  </td>
                  <td className="py-3 px-4 text-slate-400">{formatDate(entry.created_at)}</td>
                  <td className="py-3 px-4 text-right">
                    <Link
                      to={`/transactions/${encodeURIComponent(entry.transaction_id)}`}
                      className="inline-flex items-center gap-1 rounded bg-slate-800 px-2.5 py-1 text-[11px] font-sans font-semibold text-slate-200 hover:bg-slate-700 hover:text-white"
                    >
                      <span>View Record</span>
                      <ArrowUpRightIcon className="w-3 h-3 text-cyan-400" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
