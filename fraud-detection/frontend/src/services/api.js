export const API_BASE = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

function describeError(detail, fallback) {
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => `${(d.loc || []).slice(1).join(".") || "field"}: ${d.msg}`).join("; ");
  }
  return fallback;
}

async function request(path, options = {}) {
  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new Error(`Cannot reach the API at ${API_BASE}. Is the backend running?`);
  }
  if (!res.ok) {
    let body = null;
    try {
      body = await res.json();
    } catch {
      /* non-JSON error body */
    }
    throw new Error(describeError(body?.detail, `Request failed (${res.status})`));
  }
  return res.json();
}

const qs = (params) => {
  const sp = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") sp.set(k, v);
  });
  const s = sp.toString();
  return s ? `?${s}` : "";
};

export const api = {
  stats: () => request("/api/dashboard/stats"),
  rules: () => request("/api/rules"),
  createRule: (body) => request("/api/rules", { method: "POST", body: JSON.stringify(body) }),
  updateRule: (id, body) => request(`/api/rules/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteRule: (id) => request(`/api/rules/${id}`, { method: "DELETE" }),
  seed: () => request("/api/seed", { method: "POST" }),
  listTransactions: (params) => request(`/api/transactions${qs(params)}`),
  listFlagged: (params) => request(`/api/transactions/flagged${qs(params)}`),
  getTransaction: (id) => request(`/api/transactions/${encodeURIComponent(id)}`),
  createTransaction: (body) => request("/api/transactions", { method: "POST", body: JSON.stringify(body) }),
  review: (id, body) =>
    request(`/api/transactions/${encodeURIComponent(id)}/review`, { method: "PATCH", body: JSON.stringify(body) }),
  clear: (id, body) =>
    request(`/api/transactions/${encodeURIComponent(id)}/clear`, { method: "PATCH", body: JSON.stringify(body) }),
};
