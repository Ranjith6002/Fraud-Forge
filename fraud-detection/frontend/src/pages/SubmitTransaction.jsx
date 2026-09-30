import React, { useState } from "react";
import { Link } from "react-router-dom";
import { RiskBadge } from "../components/Badges.jsx";
import { api } from "../services/api.js";
import { ArrowUpRightIcon, CreditCardIcon, SendIcon, ShieldLogoIcon } from "../components/Icons.jsx";
import RiskScoreGauge from "../components/RiskScoreGauge.jsx";

const CITIES = {
  "": null,
  Chennai: [13.0827, 80.2707],
  Mumbai: [19.076, 72.8777],
  Delhi: [28.6139, 77.209],
  London: [51.5074, -0.1278],
  "New York": [40.7128, -74.006],
  Dubai: [25.2048, 55.2708],
};

const field =
  "mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3.5 py-2 text-xs font-mono text-slate-200 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500";
const label = "block text-[11px] font-semibold uppercase tracking-wider text-slate-400";

export default function SubmitTransaction() {
  const [form, setForm] = useState({
    transaction_id: `TX-${Date.now().toString().slice(-7)}`,
    user_id: "U999",
    amount: "1500",
    merchant: "Electronics MegaStore",
    city: "Chennai",
    device_id: "DEV-MOBILE-9021",
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    if (!form.city || !form.city.trim()) {
      setError("Location is required.");
      return;
    }

    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const coords = CITIES[form.city];
      const res = await api.createTransaction({
        transaction_id: form.transaction_id.trim(),
        user_id: form.user_id.trim(),
        amount: Number(form.amount),
        currency: "INR",
        merchant: form.merchant || null,
        location: form.city.trim(),
        latitude: coords ? coords[0] : null,
        longitude: coords ? coords[1] : null,
        device_id: form.device_id || null,
        timestamp: new Date().toISOString(),
      });
      setResult(res);
      setForm((f) => ({ ...f, transaction_id: `TX-${Date.now().toString().slice(-7)}` }));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* Header */}
      <div className="border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2.5">
          <h1 className="text-2xl font-extrabold tracking-tight text-slate-100 flex items-center gap-2 font-sans">
            <SendIcon className="w-6 h-6 text-cyan-400" />
            <span>Live Transaction Evaluation Sandbox</span>
          </h1>
          <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-cyan-400">
            REALTIME EVALUATOR
          </span>
        </div>
        <p className="mt-1 text-xs text-slate-400">
          Inject test transactions directly into the live rule engine. Tip: submit a small transaction in Chennai, then a large London transaction seconds later to trigger Geo Travel & Velocity rules.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-12">
        {/* Form Container */}
        <form
          onSubmit={submit}
          className="md:col-span-7 grid gap-4 rounded-xl border border-slate-800 bg-[#111726] p-5 shadow-xl sm:grid-cols-2"
        >
          <div>
            <label className={label} htmlFor="tid">
              Transaction ID
            </label>
            <input id="tid" required className={field} value={form.transaction_id} onChange={set("transaction_id")} />
          </div>

          <div>
            <label className={label} htmlFor="uid">
              User ID
            </label>
            <input id="uid" required className={field} value={form.user_id} onChange={set("user_id")} />
          </div>

          <div>
            <label className={label} htmlFor="amt">
              Amount (INR)
            </label>
            <input
              id="amt"
              required
              type="number"
              min="0.01"
              step="0.01"
              className={field}
              value={form.amount}
              onChange={set("amount")}
            />
          </div>

          <div>
            <label className={label} htmlFor="mer">
              Merchant Name
            </label>
            <input id="mer" className={field} value={form.merchant} onChange={set("merchant")} />
          </div>

          <div>
            <label className={label} htmlFor="city">
              Location Preset <span className="text-red-400 font-bold">*</span>
            </label>
            <select id="city" required className={field} value={form.city} onChange={set("city")}>
              {Object.keys(CITIES)
                .filter((c) => c !== "")
                .map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
            </select>
          </div>

          <div>
            <label className={label} htmlFor="dev">
              Device ID (Optional)
            </label>
            <input id="dev" className={field} value={form.device_id} onChange={set("device_id")} />
          </div>

          <div className="sm:col-span-2 pt-2 border-t border-slate-800">
            <button
              disabled={busy}
              className="w-full rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold py-2.5 text-xs tracking-wider uppercase shadow-lg shadow-cyan-950 transition-all disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {busy ? (
                <>
                  <span className="w-3.5 h-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  <span>Evaluating Risk Heuristics...</span>
                </>
              ) : (
                <>
                  <SendIcon className="w-4 h-4" />
                  <span>Submit Transaction & Evaluate</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Evaluation Output Preview */}
        <div className="md:col-span-5 space-y-4">
          {error && (
            <div className="rounded-xl border border-red-800 bg-red-950/30 p-4 text-xs text-red-300" role="alert">
              <strong className="font-semibold block text-red-200">Evaluation Failed</strong>
              <span className="mt-1 block leading-relaxed">{error}</span>
            </div>
          )}

          {result ? (
            <div className="rounded-xl border border-slate-800 bg-[#111726] p-5 shadow-xl space-y-4 animate-fade-in" role="status">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-xs font-mono font-bold text-cyan-400 uppercase">Evaluation Result</span>
                <RiskBadge level={result.risk_level} />
              </div>

              <div className="flex justify-center py-2">
                <RiskScoreGauge score={result.risk_score} level={result.risk_level} size={140} />
              </div>

              <div className="space-y-2">
                <p className="text-xs font-mono font-semibold text-slate-300">
                  Transaction: <span className="text-cyan-400">{result.transaction_id}</span>
                </p>
                {result.flags.length === 0 ? (
                  <p className="text-xs text-slate-400 bg-slate-900/60 p-3 rounded border border-slate-800">
                    No fraud rules triggered. Low risk score.
                  </p>
                ) : (
                  <div className="space-y-2">
                    <span className="text-[11px] font-mono uppercase text-red-400 font-semibold block">
                      Triggered Risk Rules ({result.flags.length}):
                    </span>
                    <ul className="space-y-1.5">
                      {result.flags.map((f) => (
                        <li key={f.rule} className="rounded border border-red-900/40 bg-red-950/20 p-2.5 text-xs text-red-300">
                          <div className="flex justify-between font-mono font-bold text-red-400">
                            <span>⚡ {f.rule.replace(/_/g, " ")}</span>
                            <span>+{f.score} PTS</span>
                          </div>
                          <p className="mt-1 text-[11px] text-slate-300 leading-relaxed">{f.reason}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-slate-800">
                <Link
                  to={`/transactions/${encodeURIComponent(result.transaction_id)}`}
                  className="w-full rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold py-2 px-3 transition-colors flex items-center justify-center gap-1.5"
                >
                  <span>Open Full Investigation Case</span>
                  <ArrowUpRightIcon className="w-3.5 h-3.5 text-cyan-400" />
                </Link>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-800 bg-[#111726]/40 p-8 text-center text-xs text-slate-500">
              <ShieldLogoIcon className="w-8 h-8 text-slate-700 mx-auto mb-2" />
              <p className="font-semibold text-slate-400">Awaiting Evaluation Input</p>
              <p className="mt-1">Fill in the fields on the left and click submit to trigger live risk score calculation.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
