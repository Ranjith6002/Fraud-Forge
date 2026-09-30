import React, { useState } from "react";
import { useAsync } from "../hooks/useAsync";
import { api } from "../services/api";
import { EmptyState, ErrorState, Loading } from "../components/States";
import { AlertTriangleIcon, CheckCircleIcon, RefreshCwIcon, RulesIcon } from "../components/Icons";

export default function RulesPage() {
  const { data: rules, loading, error, reload } = useAsync(() => api.rules(), []);

  // Modal State
  const [modalOpen, setModalOpen] = useState(false);
  const [editingRule, setEditingRule] = useState(null); // null for Add, rule object for Edit
  const [busy, setBusy] = useState(false);
  const [modalErr, setModalErr] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  // Form State
  const [name, setName] = useState("");
  const [ruleType, setRuleType] = useState("VELOCITY");
  const [description, setDescription] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [riskScore, setRiskScore] = useState(30);

  // Parameter states
  const [maxTransactions, setMaxTransactions] = useState(5);
  const [windowMinutes, setWindowMinutes] = useState(10);
  const [multiplier, setMultiplier] = useState(5.0);
  const [minHistory, setMinHistory] = useState(3);
  const [maxSpeedKmh, setMaxSpeedKmh] = useState(900.0);

  function openAddModal() {
    setEditingRule(null);
    setName("");
    setRuleType("VELOCITY");
    setDescription("");
    setEnabled(true);
    setRiskScore(30);
    setMaxTransactions(5);
    setWindowMinutes(10);
    setMultiplier(5.0);
    setMinHistory(3);
    setMaxSpeedKmh(900.0);
    setModalErr(null);
    setModalOpen(true);
  }

  function openEditModal(r) {
    setEditingRule(r);
    setName(r.name);
    setRuleType(r.rule_type || "VELOCITY");
    setDescription(r.description);
    setEnabled(r.enabled !== false);
    setRiskScore(r.risk_score || r.score || 30);

    const p = r.parameters || {};
    setMaxTransactions(p.max_transactions || p.threshold || 5);
    setWindowMinutes(p.window_minutes || 10);
    setMultiplier(p.multiplier || 5.0);
    setMinHistory(p.min_history || 3);
    setMaxSpeedKmh(p.max_speed_kmh || 900.0);

    setModalErr(null);
    setModalOpen(true);
  }

  async function handleSaveRule(e) {
    e.preventDefault();
    if (!name.trim()) {
      setModalErr("Rule Name is required.");
      return;
    }

    setBusy(true);
    setModalErr(null);

    // Build parameters based on ruleType
    const parameters = {};
    if (ruleType === "VELOCITY") {
      parameters.max_transactions = Number(maxTransactions);
      parameters.window_minutes = Number(windowMinutes);
    } else if (ruleType === "AMOUNT" || ruleType === "UNUSUAL_AMOUNT") {
      parameters.multiplier = Number(multiplier);
      parameters.min_history = Number(minHistory);
    } else if (ruleType === "GEO" || ruleType === "IMPOSSIBLE_GEO") {
      parameters.max_speed_kmh = Number(maxSpeedKmh);
      parameters.min_distance_km = 50.0;
    }

    const payload = {
      name: name.trim(),
      rule_type: ruleType,
      description: description.trim() || `Configured ${ruleType} fraud rule`,
      enabled,
      risk_score: Number(riskScore),
      parameters,
    };

    try {
      if (editingRule && editingRule.id) {
        await api.updateRule(editingRule.id, payload);
        setToastMsg(`Rule '${name}' updated successfully.`);
      } else {
        await api.createRule(payload);
        setToastMsg(`Rule '${name}' created and added to live rule engine.`);
      }
      setModalOpen(false);
      reload();
    } catch (err) {
      setModalErr(err.message);
    } finally {
      setBusy(false);
    }
  }

  async function toggleRuleEnabled(r) {
    try {
      if (r.id) {
        await api.updateRule(r.id, { enabled: !r.enabled });
        setToastMsg(`Rule '${r.name}' is now ${!r.enabled ? "ENABLED" : "DISABLED"}.`);
        reload();
      }
    } catch (err) {
      alert(`Error toggling rule: ${err.message}`);
    }
  }

  async function handleDeleteRule(r) {
    if (!window.confirm(`Are you sure you want to delete rule '${r.name}'?`)) return;
    try {
      if (r.id) {
        await api.deleteRule(r.id);
        setToastMsg(`Rule '${r.name}' deleted.`);
        reload();
      }
    } catch (err) {
      alert(`Error deleting rule: ${err.message}`);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-extrabold tracking-tight text-slate-100 flex items-center gap-2 font-sans">
              <RulesIcon className="w-6 h-6 text-cyan-400" />
              <span>Fraud Engine Rules & Policy Management</span>
            </h1>
            <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-400">
              CONFIGURABLE ENGINE
            </span>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Define, configure, enable/disable, and add new fraud detection rules that flow into live transaction risk scoring
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={openAddModal}
            className="inline-flex items-center gap-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-cyan-950 transition-all"
          >
            <span>+ Add New Rule</span>
          </button>
        </div>
      </div>

      {/* Toast Message */}
      {toastMsg && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3.5 text-xs text-emerald-300 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircleIcon className="w-4 h-4 text-emerald-400" />
            <span>{toastMsg}</span>
          </div>
          <button onClick={() => setToastMsg(null)} className="text-slate-400 hover:text-white font-bold">
            ✕
          </button>
        </div>
      )}

      {loading && !rules && <Loading label="Fetching dynamic fraud rules from engine DB..." />}
      {error && <ErrorState message={error} onRetry={reload} />}

      {rules && rules.length === 0 && (
        <EmptyState title="No fraud rules configured">
          Click "+ Add New Rule" to create a custom rule for the engine.
        </EmptyState>
      )}

      {/* Rules Grid */}
      {rules && rules.length > 0 && (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {rules.map((r, idx) => {
            const isEnabled = r.enabled !== false;
            return (
              <div
                key={r.name}
                className={`rounded-xl border bg-[#111726] p-6 shadow-xl space-y-4 flex flex-col justify-between transition-all ${
                  isEnabled ? "border-slate-800 hover:border-slate-700" : "border-slate-900 opacity-60 bg-slate-950/40"
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-slate-500">0{idx + 1}</span>
                      <span className="font-mono text-sm font-extrabold tracking-wide text-cyan-400">{r.name}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`rounded px-2 py-0.5 text-[10px] font-mono font-bold uppercase ${
                          isEnabled
                            ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                            : "bg-slate-800 text-slate-400 border border-slate-700"
                        }`}
                      >
                        {isEnabled ? "ENABLED" : "DISABLED"}
                      </span>
                      <span className="rounded-md border border-red-800/60 bg-red-950/80 px-2 py-0.5 font-mono text-xs font-extrabold text-red-400">
                        +{r.risk_score || r.score} PTS
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 font-mono text-[11px] text-slate-400">
                    <span>Type: <strong className="text-cyan-300">{r.rule_type || "CUSTOM"}</strong></span>
                  </div>

                  <p className="text-xs leading-relaxed text-slate-300">{r.description}</p>
                </div>

                <div className="space-y-3 pt-3 border-t border-slate-800/80">
                  <span className="block text-[10px] font-mono uppercase tracking-wider text-slate-500">
                    Engine Threshold Parameters:
                  </span>
                  <div className="space-y-1 font-mono text-xs">
                    {Object.entries(r.parameters || {}).map(([k, v]) => (
                      <div key={k} className="flex items-center justify-between rounded bg-slate-900 px-2.5 py-1.5 border border-slate-800">
                        <span className="text-slate-400 text-[11px]">{k}</span>
                        <span className="font-bold text-slate-200">{String(v)}</span>
                      </div>
                    ))}
                  </div>

                  {/* Actions Toolbar */}
                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                    <button
                      onClick={() => toggleRuleEnabled(r)}
                      className={`px-3 py-1 rounded text-xs font-semibold font-mono transition-colors ${
                        isEnabled
                          ? "bg-amber-950/60 text-amber-400 border border-amber-800/60 hover:bg-amber-900"
                          : "bg-emerald-950/60 text-emerald-400 border border-emerald-800/60 hover:bg-emerald-900"
                      }`}
                    >
                      {isEnabled ? "Disable" : "Enable"}
                    </button>

                    <div className="flex items-center gap-2">
                      {r.id && (
                        <button
                          onClick={() => openEditModal(r)}
                          className="px-2.5 py-1 rounded border border-slate-700 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
                        >
                          Edit
                        </button>
                      )}
                      {r.id && (
                        <button
                          onClick={() => handleDeleteRule(r)}
                          className="px-2.5 py-1 rounded border border-red-900/60 bg-red-950/40 hover:bg-red-900 text-xs font-semibold text-red-400"
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add / Edit Rule Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-slate-800 bg-[#111726] p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                <RulesIcon className="w-5 h-5 text-cyan-400" />
                <span>{editingRule ? "Edit Fraud Rule" : "Add New Fraud Rule"}</span>
              </h2>
              <button onClick={() => setModalOpen(false)} className="text-slate-400 hover:text-white font-bold">
                ✕
              </button>
            </div>

            {modalErr && (
              <div className="rounded-lg border border-red-800 bg-red-950/40 p-3 text-xs text-red-300">
                {modalErr}
              </div>
            )}

            <form onSubmit={handleSaveRule} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold uppercase text-slate-400 mb-1" htmlFor="rname">
                  Rule Name <span className="text-red-400">*</span>
                </label>
                <input
                  id="rname"
                  required
                  placeholder="e.g. Extreme Velocity Alert"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-mono text-slate-100 focus:border-cyan-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold uppercase text-slate-400 mb-1" htmlFor="rtype">
                    Rule Type <span className="text-red-400">*</span>
                  </label>
                  <select
                    id="rtype"
                    value={ruleType}
                    onChange={(e) => setRuleType(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-mono text-slate-100 focus:border-cyan-500 focus:outline-none"
                  >
                    <option value="VELOCITY">VELOCITY (Frequency)</option>
                    <option value="AMOUNT">AMOUNT (Unusual Amount)</option>
                    <option value="GEO">GEO (Impossible Travel)</option>
                    <option value="DEVICE_MISMATCH">DEVICE_MISMATCH (New Device)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold uppercase text-slate-400 mb-1" htmlFor="rscore">
                    Risk Score Weight (1-100) <span className="text-red-400">*</span>
                  </label>
                  <input
                    id="rscore"
                    type="number"
                    min="1"
                    max="100"
                    required
                    value={riskScore}
                    onChange={(e) => setRiskScore(e.target.value)}
                    className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs font-mono text-slate-100 focus:border-cyan-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block font-semibold uppercase text-slate-400 mb-1" htmlFor="rdesc">
                  Description
                </label>
                <textarea
                  id="rdesc"
                  rows={2}
                  placeholder="Explain what suspicious pattern this rule detects..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-100 focus:border-cyan-500 focus:outline-none"
                />
              </div>

              {/* Dynamic Threshold Fields */}
              <div className="rounded-lg border border-slate-800 bg-slate-900/60 p-3.5 space-y-3">
                <span className="block font-mono text-[11px] uppercase tracking-wider text-cyan-400 font-bold">
                  Rule Threshold Configuration
                </span>

                {ruleType === "VELOCITY" && (
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[10px] text-slate-400 font-mono mb-1">Max Transactions</label>
                      <input
                        type="number"
                        min="1"
                        value={maxTransactions}
                        onChange={(e) => setMaxTransactions(e.target.value)}
                        className="w-full rounded border border-slate-700 bg-slate-900 px-2.5 py-1.5 font-mono text-slate-200"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] text-slate-400 font-mono mb-1">Window Minutes</label>
                      <input
                        type="number"
                        min="0.1"
                        step="0.1"
                        value={windowMinutes}
                        onChange={(e) => setWindowMinutes(e.target.value)}
                        className="w-full rounded border border-slate-700 bg-slate-900 px-2.5 py-1.5 font-mono text-slate-200"
                      />
                    </div>
                  </div>
                )}

                {(ruleType === "AMOUNT" || ruleType === "UNUSUAL_AMOUNT") && (
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-[10px] text-slate-400 font-mono mb-1">Amount Multiplier (e.g. 5.0x)</label>
                      <input
                        type="number"
                        min="1.1"
                        step="0.1"
                        value={multiplier}
                        onChange={(e) => setMultiplier(e.target.value)}
                        className="w-full rounded border border-slate-700 bg-slate-900 px-2.5 py-1.5 font-mono text-slate-200"
                      />
                    </div>
                    <div>
                      <label className="block text-[10px] text-slate-400 font-mono mb-1">Min History Count</label>
                      <input
                        type="number"
                        min="1"
                        value={minHistory}
                        onChange={(e) => setMinHistory(e.target.value)}
                        className="w-full rounded border border-slate-700 bg-slate-900 px-2.5 py-1.5 font-mono text-slate-200"
                      />
                    </div>
                  </div>
                )}

                {(ruleType === "GEO" || ruleType === "IMPOSSIBLE_GEO") && (
                  <div>
                    <label className="block text-[10px] text-slate-400 font-mono mb-1">Max Speed (km/h threshold)</label>
                    <input
                      type="number"
                      min="10"
                      value={maxSpeedKmh}
                      onChange={(e) => setMaxSpeedKmh(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-900 px-2.5 py-1.5 font-mono text-slate-200"
                    />
                  </div>
                )}

                {ruleType === "DEVICE_MISMATCH" && (
                  <p className="text-[11px] text-slate-400 font-mono">
                    Flags transactions when a user uses a device ID never used in prior history.
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2 pt-1">
                <input
                  type="checkbox"
                  id="renabled"
                  checked={enabled}
                  onChange={(e) => setEnabled(e.target.checked)}
                  className="h-4 w-4 rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-cyan-500"
                />
                <label htmlFor="renabled" className="text-xs font-semibold text-slate-300">
                  Enable Rule Immediately for Transaction Evaluations
                </label>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  disabled={busy}
                  className="rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={busy}
                  className="rounded-lg bg-cyan-600 hover:bg-cyan-500 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-cyan-950 flex items-center gap-2"
                >
                  {busy ? "Saving Rule..." : editingRule ? "Update Rule" : "Create & Deploy Rule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
