import React from 'react';
import { AlertTriangleIcon, RefreshCwIcon, ShieldLogoIcon } from './Icons';

export function Loading({ label = "Loading live risk data…" }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-slate-400" role="status">
      <div className="relative flex items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-slate-700 border-t-cyan-500" />
        <ShieldLogoIcon className="absolute w-5 h-5 text-cyan-400/80 animate-pulse" />
      </div>
      <p className="text-xs font-mono uppercase tracking-wider text-slate-400">{label}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="rounded-xl border border-red-900/50 bg-red-950/30 p-5 text-sm text-red-300 shadow-lg" role="alert">
      <div className="flex items-start gap-3">
        <AlertTriangleIcon className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <p className="font-semibold text-red-200">API Connection Error</p>
          <p className="mt-1 text-xs text-red-300/80 leading-relaxed">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 inline-flex items-center gap-2 rounded-lg bg-red-900/60 hover:bg-red-900 px-3.5 py-1.5 text-xs font-medium text-red-100 transition-colors border border-red-700/50"
            >
              <RefreshCwIcon className="w-3.5 h-3.5" />
              Retry Connection
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function EmptyState({ title, children, icon: Icon }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-800 bg-[#111726]/60 p-10 text-center shadow-inner">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-900 border border-slate-800 text-slate-500 mb-3">
        {Icon ? <Icon className="w-6 h-6" /> : <ShieldLogoIcon className="w-6 h-6 text-slate-600" />}
      </div>
      <p className="text-base font-semibold text-slate-200">{title}</p>
      {children && <div className="mt-1.5 text-xs text-slate-400 max-w-md mx-auto">{children}</div>}
    </div>
  );
}
