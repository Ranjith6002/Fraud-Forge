import React from 'react';

const TONES = {
  default: {
    val: "text-slate-100",
    border: "border-slate-800 hover:border-slate-700",
    accent: "bg-slate-700",
    iconBg: "bg-slate-800 text-slate-300",
  },
  danger: {
    val: "text-red-400",
    border: "border-red-900/40 hover:border-red-800/60",
    accent: "bg-red-500",
    iconBg: "bg-red-500/10 text-red-400 border border-red-500/20",
  },
  warn: {
    val: "text-amber-400",
    border: "border-amber-900/40 hover:border-amber-800/60",
    accent: "bg-amber-500",
    iconBg: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
  },
  good: {
    val: "text-emerald-400",
    border: "border-emerald-900/40 hover:border-emerald-800/60",
    accent: "bg-emerald-500",
    iconBg: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  },
  info: {
    val: "text-cyan-400",
    border: "border-cyan-900/40 hover:border-cyan-800/60",
    accent: "bg-cyan-500",
    iconBg: "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20",
  },
};

export default function StatCard({ label, value, tone = "default", hint, trend, icon: Icon }) {
  const t = TONES[tone] || TONES.default;

  return (
    <div className={`relative overflow-hidden rounded-xl bg-[#111726] p-4 border ${t.border} transition-all duration-200 shadow-lg`}>
      {/* Top accent bar */}
      <div className={`absolute top-0 left-0 right-0 h-0.5 ${t.accent} opacity-80`} />
      
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">{label}</p>
          <p className={`mt-2 text-2xl lg:text-3xl font-extrabold tracking-tight ${t.val}`}>
            {value != null ? (typeof value === 'number' ? value.toLocaleString() : value) : "—"}
          </p>
        </div>
        {Icon && (
          <div className={`p-2.5 rounded-lg ${t.iconBg}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="mt-2 flex items-center justify-between gap-2 text-xs">
        {trend && (
          <span className="inline-flex items-center font-medium text-emerald-400">
            ↑ {trend}
          </span>
        )}
        {hint && <span className="text-[11px] text-slate-400 truncate">{hint}</span>}
      </div>
    </div>
  );
}
