/* ════════════════════════════════════════════════════════
   TaskFlow — API Client
   Centralised fetch wrapper with JWT auto-refresh
   ════════════════════════════════════════════════════════ */

const API_BASE = "/api/v1";

const Auth = {
  getAccess:  () => localStorage.getItem("tf_access"),
  getRefresh: () => localStorage.getItem("tf_refresh"),
  getUser:    () => { try { return JSON.parse(localStorage.getItem("tf_user")); } catch { return null; } },
  set(tokens, user) {
    localStorage.setItem("tf_access",  tokens.access);
    localStorage.setItem("tf_refresh", tokens.refresh || Auth.getRefresh());
    if (user) localStorage.setItem("tf_user", JSON.stringify(user));
  },
  clear() {
    ["tf_access", "tf_refresh", "tf_user"].forEach(k => localStorage.removeItem(k));
  },
  isAuthenticated: () => !!localStorage.getItem("tf_access"),
};

async function refreshAccessToken() {
  const refresh = Auth.getRefresh();
  if (!refresh) throw new Error("No refresh token");
  const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) { Auth.clear(); window.location.href = "/login/"; throw new Error("Session expired"); }
  const data = await res.json();
  Auth.set({ access: data.access, refresh: data.refresh || refresh });
  return data.access;
}

async function apiFetch(endpoint, options = {}, retry = true) {
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;
  const headers = { "Content-Type": "application/json", ...options.headers };
  const token = Auth.getAccess();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, { ...options, headers });

  if (res.status === 401 && retry) {
    try {
      await refreshAccessToken();
      return apiFetch(endpoint, options, false);
    } catch {
      window.location.href = "/login/";
      return;
    }
  }

  const ct = res.headers.get("Content-Type") || "";
  const data = ct.includes("application/json") ? await res.json() : null;

  if (!res.ok) {
    const msg = data?.error?.message || data?.detail || `HTTP ${res.status}`;
    throw Object.assign(new Error(msg), { status: res.status, data });
  }
  return data;
}

const api = {
  get:    (url, opts = {}) => apiFetch(url, { ...opts, method: "GET" }),
  post:   (url, body, opts = {}) => apiFetch(url, { ...opts, method: "POST",  body: JSON.stringify(body) }),
  patch:  (url, body, opts = {}) => apiFetch(url, { ...opts, method: "PATCH", body: JSON.stringify(body) }),
  delete: (url, opts = {})       => apiFetch(url, { ...opts, method: "DELETE" }),

  // ── Auth ──────────────────────────────────────────────
  auth: {
    register:    (data)       => api.post("/auth/register/", data),
    login:       (email)      => api.post("/auth/login/", { email }),
    loginVerify: (email, otp) => api.post("/auth/login/verify/", { email, otp }),
    logout:      ()           => api.post("/auth/logout/", { refresh: Auth.getRefresh() }),
    me:          ()           => api.get("/auth/me/"),
  },

  // ── Projects ──────────────────────────────────────────
  projects: {
    list:   (params = {}) => api.get("/projects/?" + new URLSearchParams(params)),
    get:    (id)   => api.get(`/projects/${id}/`),
    create: (data) => api.post("/projects/", data),
    update: (id, data) => api.patch(`/projects/${id}/`, data),
    delete: (id)   => api.delete(`/projects/${id}/`),
    stats:  (id)   => api.get(`/projects/${id}/stats/`),
    members: {
      list:   (projectId) => api.get(`/projects/${projectId}/members/`),
      add:    (projectId, data) => api.post(`/projects/${projectId}/members/`, data),
      remove: (projectId, memberId) => api.delete(`/projects/${projectId}/members/${memberId}/`),
    },
  },

  // ── Tasks ─────────────────────────────────────────────
  tasks: {
    list:   (projectId, params = {}) => api.get(`/projects/${projectId}/tasks/?` + new URLSearchParams(params)),
    get:    (id)   => api.get(`/tasks/${id}/`),
    create: (projectId, data) => api.post(`/projects/${projectId}/tasks/`, data),
    update: (id, data) => api.patch(`/tasks/${id}/`, data),
    updateStatus: (id, status) => api.patch(`/tasks/${id}/status/`, { status }),
    delete: (id)   => api.delete(`/tasks/${id}/`),
    mine:   (params = {}) => api.get("/tasks/me/?" + new URLSearchParams(params)),
    comments: {
      list:   (taskId) => api.get(`/tasks/${taskId}/comments/`),
      create: (taskId, body) => api.post(`/tasks/${taskId}/comments/`, { body }),
    },
    activity: (taskId) => api.get(`/tasks/${taskId}/activity/`),
  },
};

window.api  = api;
window.Auth = Auth;
