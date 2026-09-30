import React, { useState } from "react";
import TransactionTable from "../components/TransactionTable.jsx";
import { EmptyState, ErrorState, Loading } from "../components/States.jsx";
import { useAsync, useDebounced } from "../hooks/useAsync.js";
import { api } from "../services/api.js";
import { AlertTriangleIcon, CreditCardIcon, FilterIcon, RefreshCwIcon, SearchIcon } from "../components/Icons.jsx";

const inputClass =
  "rounded-lg border border-slate-700 bg-slate-900 px-3.5 py-2 text-xs font-mono text-slate-200 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 placeholder:text-slate-500";

export default function TransactionsPage({ flaggedOnly = false }) {
  const [search, setSearch] = useState("");
  const [risk, setRisk] = useState("");
  const [status, setStatus] = useState("");
  const [sort, setSort] = useState(
    flaggedOnly ? { by: "risk_score", order: "desc" } : { by: "created_at", order: "desc" }
  );
  const q = useDebounced(search, 300);

  const { data, loading, error, reload } = useAsync(
    () =>
      (flaggedOnly ? api.listFlagged : api.listTransactions)({
        q,
        risk_level: risk,
        status,
        sort_by: sort.by,
        order: sort.order,
        limit: 200,
      }),
    [q, risk, status, sort.by, sort.order, flaggedOnly]
  );

  const toggleSort = (field) =>
    setSort((s) => (s.by === field ? { by: field, order: s.order === "asc" ? "desc" : "asc" } : { by: field, order: "desc" }));

  const filtersActive = q || risk || status;
  const title = flaggedOnly ? "Fraud Alerts Center" : "All Monitored Transactions";
  const subtitle = flaggedOnly
    ? "Real-time stream of transactions that triggered engine fraud rules"
    : "Comprehensive audit explorer of all transactions evaluated by Sentinel Fraud";

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-100 flex items-center gap-2.5">
            {flaggedOnly ? (
              <AlertTriangleIcon className="w-6 h-6 text-amber-400" />
            ) : (
              <CreditCardIcon className="w-6 h-6 text-cyan-400" />
            )}
            <span>{title}</span>
          </h1>
          <p className="mt-1 text-xs text-slate-400">
            {subtitle}
            {data ? ` • Showing ${data.items.length} of ${data.total} records` : ""}
          </p>
        </div>

        <button
          onClick={reload}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
        >
          <RefreshCwIcon className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter Toolbar */}
      <div className="rounded-xl border border-slate-800 bg-[#111726] p-4 shadow-lg flex flex-col md:flex-row gap-3 md:items-center justify-between">
        <div className="flex flex-col sm:flex-row gap-3 flex-1">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <SearchIcon className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
            <input
              className={`${inputClass} pl-9 w-full`}
              placeholder="Search Transaction ID, User, Merchant, Location..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              aria-label="Search transactions"
            />
          </div>

          {/* Risk Level Filter */}
          <div className="flex items-center gap-2">
            <select
              className={inputClass}
              value={risk}
              onChange={(e) => setRisk(e.target.value)}
              aria-label="Filter by risk level"
            >
              <option value="">All Risk Levels</option>
              <option value="HIGH">High Risk (70+)</option>
              <option value="MEDIUM">Medium Risk (30-69)</option>
              <option value="LOW">Low Risk (&lt; 30)</option>
            </select>
          </div>

          {/* Review Status Filter */}
          <div className="flex items-center gap-2">
            <select
              className={inputClass}
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              aria-label="Filter by review status"
            >
              <option value="">All Review Statuses</option>
              <option value="PENDING">Pending Review</option>
              <option value="REVIEWED">Reviewed</option>
              <option value="CLEARED">Cleared</option>
            </select>
          </div>
        </div>

        {filtersActive && (
          <button
            className="inline-flex items-center gap-1 text-xs font-semibold text-cyan-400 hover:text-cyan-300 hover:underline self-start md:self-center"
            onClick={() => {
              setSearch("");
              setRisk("");
              setStatus("");
            }}
          >
            <span>Clear Filters</span>
          </button>
        )}
      </div>

      {/* Main Content State */}
      {loading && !data && <Loading label="Querying transaction audit database..." />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {data && data.items.length === 0 && (
        <EmptyState
          title={filtersActive ? "No transactions match your current search criteria" : "No transactions found"}
        >
          {filtersActive
            ? "Try resetting your search term or adjusting risk level and status filters."
            : "Use the “Seed Demo Data” button on the Dashboard to populate test data."}
        </EmptyState>
      )}

      {data && data.items.length > 0 && (
        <div className={loading ? "opacity-60 transition-opacity" : ""}>
          <TransactionTable items={data.items} sort={sort} onSort={toggleSort} />
        </div>
      )}
    </div>
  );
}
