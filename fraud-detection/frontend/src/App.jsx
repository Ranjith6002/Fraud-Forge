import React, { useState } from "react";
import { NavLink, Route, Routes, useNavigate } from "react-router-dom";
import Dashboard from "./pages/Dashboard.jsx";
import TransactionsPage from "./pages/TransactionsPage.jsx";
import TransactionDetails from "./pages/TransactionDetails.jsx";
import SubmitTransaction from "./pages/SubmitTransaction.jsx";
import RulesPage from "./pages/RulesPage.jsx";
import AuditLogPage from "./pages/AuditLogPage.jsx";
import { API_BASE, api } from "./services/api.js";
import { useAsync } from "./hooks/useAsync.js";
import {
  AlertTriangleIcon,
  AuditIcon,
  BellIcon,
  CreditCardIcon,
  DashboardIcon,
  ExternalLinkIcon,
  MenuIcon,
  RulesIcon,
  SearchIcon,
  SendIcon,
  ShieldLogoIcon,
  UserIcon,
} from "./components/Icons.jsx";

const navItems = [
  { to: "/", label: "Dashboard", icon: DashboardIcon, end: true },
  { to: "/flagged", label: "Fraud Alerts", icon: AlertTriangleIcon },
  { to: "/transactions", label: "All Transactions", icon: CreditCardIcon },
  { to: "/rules", label: "Fraud Rules", icon: RulesIcon },
  { to: "/audit", label: "Audit Log", icon: AuditIcon },
  { to: "/submit", label: "Submit Sandbox", icon: SendIcon },
];

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [globalSearch, setGlobalSearch] = useState("");
  const [showNotifications, setShowNotifications] = useState(false);
  const navigate = useNavigate();

  // Fetch telemetry stats for live header notifications
  const stats = useAsync(() => api.stats(), []);
  const highRiskCount = stats.data?.high_risk_transactions || 0;
  const pendingCount = stats.data?.pending_reviews || 0;

  function handleSearchSubmit(e) {
    e.preventDefault();
    if (globalSearch.trim()) {
      navigate(`/transactions?search=${encodeURIComponent(globalSearch.trim())}`);
      setGlobalSearch("");
    }
  }

  const linkCls = ({ isActive }) =>
    `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-semibold tracking-wide transition-all ${
      isActive
        ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-md shadow-cyan-950/20"
        : "text-slate-400 hover:bg-slate-800/60 hover:text-slate-200"
    }`;

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100 flex flex-col font-sans">
      {/* TOP BAR */}
      <header className="sticky top-0 z-40 bg-[#0F1420]/90 backdrop-blur-md border-b border-slate-800/80">
        <div className="mx-auto flex h-16 max-w-[1600px] items-center justify-between px-4 sm:px-6">
          {/* Logo & Product Name */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white"
              aria-label="Toggle Navigation Sidebar"
            >
              <MenuIcon className="w-5 h-5" />
            </button>

            <NavLink to="/" className="flex items-center gap-2.5 group">
              <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 group-hover:border-cyan-500/40 transition-colors">
                <ShieldLogoIcon className="w-6 h-6 text-cyan-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-base font-extrabold tracking-tight text-white font-sans">
                    Sentinel<span className="text-cyan-400">Fraud</span>
                  </span>
                  <span className="hidden sm:inline-block rounded-full bg-cyan-500/10 border border-cyan-500/30 px-2 py-0.2 text-[10px] font-mono text-cyan-400">
                    v1.0 SOC
                  </span>
                </div>
                <p className="text-[10px] font-mono tracking-widest text-slate-400 uppercase hidden sm:block">
                  Transaction Risk Intelligence
                </p>
              </div>
            </NavLink>
          </div>

          {/* Search Box */}
          <form onSubmit={handleSearchSubmit} className="hidden md:flex flex-1 max-w-md mx-6">
            <div className="relative w-full">
              <SearchIcon className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search transaction ID, user ID..."
                value={globalSearch}
                onChange={(e) => setGlobalSearch(e.target.value)}
                className="w-full rounded-lg border border-slate-700/80 bg-slate-900/80 pl-9 pr-4 py-1.5 text-xs font-mono text-slate-200 placeholder:text-slate-500 focus:border-cyan-500 focus:outline-none focus:ring-1 focus:ring-cyan-500"
              />
            </div>
          </form>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            {/* Live Operational Status */}
            <div className="hidden xl:flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-[11px] font-mono text-emerald-400">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              <span>SOC Monitoring Active</span>
            </div>

            {/* Notification Bell */}
            <div className="relative">
              <button
                onClick={() => setShowNotifications(!showNotifications)}
                className="relative p-2 rounded-lg text-slate-400 hover:bg-slate-800 hover:text-white transition-colors"
                aria-label="Notifications"
              >
                <BellIcon className="w-5 h-5" />
                {highRiskCount > 0 && (
                  <span className="absolute top-1 right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-mono font-bold text-white shadow-lg animate-pulse">
                    {highRiskCount}
                  </span>
                )}
              </button>

              {/* Dropdown menu for notifications */}
              {showNotifications && (
                <div className="absolute right-0 mt-2 w-80 rounded-xl border border-slate-800 bg-[#111726] p-4 shadow-2xl z-50 animate-fade-in space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                    <span className="text-xs font-mono font-bold uppercase text-slate-200">
                      Live Telemetry Alerts
                    </span>
                    <button onClick={() => setShowNotifications(false)} className="text-xs text-slate-500 hover:text-white">
                      ✕
                    </button>
                  </div>
                  <div className="space-y-2">
                    <div className="rounded-lg border border-red-900/50 bg-red-950/30 p-2.5 text-xs text-red-300">
                      <p className="font-bold flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full bg-red-500" />
                        {highRiskCount} High Risk Flagged
                      </p>
                      <p className="mt-0.5 text-[11px] text-slate-400">Transactions exceeding critical risk thresholds</p>
                    </div>
                    <div className="rounded-lg border border-amber-900/50 bg-amber-950/30 p-2.5 text-xs text-amber-300">
                      <p className="font-bold">{pendingCount} Pending Reviews</p>
                      <p className="mt-0.5 text-[11px] text-slate-400">Awaiting analyst action</p>
                    </div>
                  </div>
                  <NavLink
                    to="/flagged"
                    onClick={() => setShowNotifications(false)}
                    className="block text-center text-xs font-semibold text-cyan-400 hover:underline pt-1"
                  >
                    View All Flagged Alerts →
                  </NavLink>
                </div>
              )}
            </div>

            {/* API Docs Button */}
            <a
              href={`${API_BASE}/docs`}
              target="_blank"
              rel="noreferrer"
              className="hidden sm:inline-flex items-center gap-1.5 rounded-lg border border-slate-700 bg-slate-800/80 px-3 py-1.5 text-xs font-semibold text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
            >
              <span>API Docs</span>
              <ExternalLinkIcon className="w-3.5 h-3.5 text-slate-400" />
            </a>

            {/* User Profile */}
            <div className="flex items-center gap-2 pl-2 border-l border-slate-800">
              <div className="p-1.5 rounded-full bg-slate-800 border border-slate-700 text-cyan-400">
                <UserIcon className="w-4 h-4" />
              </div>
              <div className="hidden lg:block text-left">
                <p className="text-xs font-semibold text-slate-200 leading-tight">Analyst Ops</p>
                <p className="text-[10px] font-mono text-slate-400">admin@sentinel</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* BODY CONTAINER */}
      <div className="flex-1 mx-auto flex w-full max-w-[1600px]">
        {/* SIDEBAR */}
        <aside
          className={`fixed inset-y-0 left-0 z-30 w-64 bg-[#0F1420] border-r border-slate-800/80 p-4 transition-transform duration-300 ease-in-out lg:static lg:translate-x-0 ${
            sidebarOpen ? "translate-x-0 pt-20" : "-translate-x-full"
          }`}
        >
          <nav className="space-y-1" aria-label="Main Navigation">
            <p className="px-3 py-2 text-[10px] font-mono uppercase tracking-widest text-slate-400 font-bold">
              SOC CONSOLE NAV
            </p>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  onClick={() => setSidebarOpen(false)}
                  className={linkCls}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>

          {/* Engine Info Box at Sidebar Bottom */}
          <div className="mt-10 rounded-xl border border-slate-800/80 bg-[#111726] p-4 space-y-2">
            <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
              <span>ENGINE STATUS</span>
              <span className="text-emerald-400 font-bold">ONLINE</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed font-sans">
              Rule engine monitoring transaction velocity, geographical distance, and value anomalies.
            </p>
          </div>
        </aside>

        {/* Backdrop for Mobile Sidebar */}
        {sidebarOpen && (
          <div
            onClick={() => setSidebarOpen(false)}
            className="fixed inset-0 z-20 bg-slate-950/70 backdrop-blur-xs lg:hidden"
          />
        )}

        {/* MAIN CONTENT AREA */}
        <main className="flex-1 px-4 py-6 sm:px-8 max-w-full overflow-hidden">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/flagged" element={<TransactionsPage key="flagged" flaggedOnly />} />
            <Route path="/transactions" element={<TransactionsPage key="all" />} />
            <Route path="/transactions/:id" element={<TransactionDetails />} />
            <Route path="/rules" element={<RulesPage />} />
            <Route path="/audit" element={<AuditLogPage />} />
            <Route path="/reviews" element={<AuditLogPage />} />
            <Route path="/submit" element={<SubmitTransaction />} />
            <Route
              path="*"
              element={
                <div className="py-20 text-center space-y-3">
                  <h2 className="text-2xl font-extrabold text-slate-200">404 - Page Not Found</h2>
                  <p className="text-xs text-slate-400">The requested SOC console route does not exist.</p>
                  <NavLink to="/" className="inline-block rounded-lg bg-cyan-600 px-4 py-2 text-xs font-semibold text-white">
                    Return to Dashboard
                  </NavLink>
                </div>
              }
            />
          </Routes>
        </main>
      </div>
    </div>
  );
}
