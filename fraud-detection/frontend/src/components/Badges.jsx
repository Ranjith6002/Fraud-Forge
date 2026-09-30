import React from 'react';

const RISK_MAP = {
  HIGH: {
    cls: "bg-red-500/10 text-red-400 border-red-500/30 ring-red-500/20",
    dotCls: "bg-red-500 animate-pulse",
    icon: "▲",
    label: "HIGH RISK",
  },
  MEDIUM: {
    cls: "bg-amber-500/10 text-amber-400 border-amber-500/30 ring-amber-500/20",
    dotCls: "bg-amber-500",
    icon: "◆",
    label: "MEDIUM RISK",
  },
  LOW: {
    cls: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30 ring-emerald-500/20",
    dotCls: "bg-emerald-500",
    icon: "●",
    label: "LOW RISK",
  },
};

const STATUS_MAP = {
  PENDING: {
    cls: "bg-amber-500/10 text-amber-300 border-amber-500/30",
    icon: "⏳",
    label: "PENDING REVIEW",
  },
  REVIEWED: {
    cls: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
    icon: "👁️",
    label: "REVIEWED",
  },
  CLEARED: {
    cls: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
    icon: "✓",
    label: "CLEARED",
  },
};

export function RiskBadge({ level, showDot = true, size = "md" }) {
  const r = RISK_MAP[level] || RISK_MAP.LOW;
  const padding = size === "sm" ? "px-2 py-0.5 text-[11px]" : size === "lg" ? "px-3 py-1 text-xs" : "px-2.5 py-1 text-xs";
  
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-semibold tracking-wide uppercase transition-colors ${padding} ${r.cls}`}>
      {showDot && <span className={`w-1.5 h-1.5 rounded-full ${r.dotCls}`} aria-hidden="true" />}
      <span>{level || "LOW"}</span>
    </span>
  );
}

export function StatusBadge({ status }) {
  const s = STATUS_MAP[status] || STATUS_MAP.PENDING;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider ${s.cls}`}>
      <span className="text-[10px]">{s.icon}</span>
      <span>{status || "PENDING"}</span>
    </span>
  );
}

export function RuleChip({ name, score }) {
  return (
    <span className="inline-flex items-center gap-1.5 rounded border border-slate-800 bg-slate-900/80 px-2 py-0.5 text-[11px] font-mono text-slate-300">
      <span>{name.replace(/_/g, " ")}</span>
      {score !== undefined && (
        <span className="text-[10px] font-bold text-red-400">+{score}</span>
      )}
    </span>
  );
}
