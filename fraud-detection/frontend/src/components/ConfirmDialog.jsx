import React, { useEffect } from "react";
import { AlertTriangleIcon, CheckCircleIcon } from "./Icons";

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel,
  confirmVariant = "primary", // "primary" | "emerald" | "danger"
  busy,
  onConfirm,
  onCancel,
}) {
  useEffect(() => {
    if (!open) return undefined;
    const onKey = (e) => e.key === "Escape" && !busy && onCancel();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, busy, onCancel]);

  if (!open) return null;

  let btnCls = "bg-cyan-600 hover:bg-cyan-500 text-white shadow-cyan-900/30";
  if (confirmVariant === "emerald") {
    btnCls = "bg-emerald-600 hover:bg-emerald-500 text-white shadow-emerald-900/30";
  } else if (confirmVariant === "danger") {
    btnCls = "bg-red-600 hover:bg-red-500 text-white shadow-red-900/30";
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-fade-in">
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        className="w-full max-w-md rounded-xl border border-slate-800 bg-[#111726] p-6 shadow-2xl space-y-4"
      >
        <div className="flex items-start gap-3">
          <div className="p-2 rounded-lg bg-slate-800 text-cyan-400 border border-slate-700">
            {confirmVariant === "emerald" ? (
              <CheckCircleIcon className="w-6 h-6 text-emerald-400" />
            ) : (
              <AlertTriangleIcon className="w-6 h-6 text-amber-400" />
            )}
          </div>
          <div>
            <h2 id="confirm-title" className="text-lg font-bold text-slate-100">
              {title}
            </h2>
            <p className="mt-1 text-xs leading-relaxed text-slate-400">{message}</p>
          </div>
        </div>

        <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
          <button
            onClick={onCancel}
            disabled={busy}
            className="rounded-lg border border-slate-700 bg-slate-800/80 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-700 hover:text-white transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={busy}
            className={`rounded-lg px-4 py-2 text-xs font-semibold shadow-lg transition-all disabled:opacity-50 flex items-center gap-2 ${btnCls}`}
          >
            {busy ? (
              <>
                <span className="w-3.5 h-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                <span>Processing...</span>
              </>
            ) : (
              confirmLabel
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
