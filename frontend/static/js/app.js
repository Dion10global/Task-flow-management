/* ════════════════════════════════════════════════════════
   TaskFlow — App Shell
   Toast system, modals, helpers, route guard
   ════════════════════════════════════════════════════════ */

/* ── Toast ────────────────────────────────────────────── */
const Toast = (() => {
  let container;
  function getContainer() {
    if (!container) {
      container = document.createElement("div");
      container.className = "toast-container";
      document.body.appendChild(container);
    }
    return container;
  }

  function show(message, type = "info", duration = 3500) {
    const icons = { success: "✓", error: "✕", info: "i", warning: "⚠" };
    const colors = { success: "var(--green)", error: "var(--red)", info: "var(--blue)", warning: "var(--amber)" };

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span style="color:${colors[type]};font-weight:700;font-size:13px">${icons[type]}</span>
      <span>${message}</span>
    `;
    getContainer().appendChild(toast);

    setTimeout(() => {
      toast.classList.add("dismissing");
      toast.addEventListener("animationend", () => toast.remove(), { once: true });
    }, duration);
  }

  return { show, success: m => show(m, "success"), error: m => show(m, "error"), info: m => show(m, "info") };
})();

/* ── Modal ────────────────────────────────────────────── */
const Modal = (() => {
  function open(id) {
    const el = document.getElementById(id);
    if (el) el.classList.add("open");
  }
  function close(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove("open");
  }
  function closeAll() {
    document.querySelectorAll(".modal-backdrop.open").forEach(el => el.classList.remove("open"));
  }
  // Close on backdrop click
  document.addEventListener("click", e => {
    if (e.target.classList.contains("modal-backdrop")) closeAll();
  });
  // Close on Escape
  document.addEventListener("keydown", e => {
    if (e.key === "Escape") closeAll();
  });
  return { open, close, closeAll };
})();

/* ── Helpers ──────────────────────────────────────────── */
const Helpers = {
  formatDate(dateStr) {
    if (!dateStr) return "—";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  },

  formatRelative(dateStr) {
    if (!dateStr) return "";
    const diff = (Date.now() - new Date(dateStr)) / 1000;
    if (diff < 60)   return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400)return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  },

  initials(name = "") {
    return name.trim().split(/\s+/).map(p => p[0]?.toUpperCase()).join("").slice(0, 2) || "?";
  },

  statusBadge(status) {
    const map = {
      todo:        ["badge-todo",     "To Do"],
      in_progress: ["badge-progress", "In Progress"],
      in_review:   ["badge-review",   "In Review"],
      done:        ["badge-done",     "Done"],
      cancelled:   ["badge-cancelled","Cancelled"],
    };
    const [cls, label] = map[status] || ["badge-todo", status];
    return `<span class="badge ${cls}">${label}</span>`;
  },

  priorityBadge(priority) {
    const map = {
      low:      ["badge-low",      "Low"],
      medium:   ["badge-medium",   "Medium"],
      high:     ["badge-high",     "High"],
      critical: ["badge-critical", "Critical"],
    };
    const [cls, label] = map[priority] || ["badge-medium", priority];
    return `<span class="badge ${cls}">${label}</span>`;
  },

  projectStatusBadge(status) {
    const map = {
      active:    ["badge-active",    "Active"],
      archived:  ["badge-archived",  "Archived"],
      completed: ["badge-completed", "Completed"],
    };
    const [cls, label] = map[status] || ["badge-active", status];
    return `<span class="badge ${cls}">${label}</span>`;
  },

  isOverdue(dueDateStr, status) {
    if (!dueDateStr || ["done", "cancelled"].includes(status)) return false;
    return new Date(dueDateStr) < new Date();
  },

  skeleton(lines = 3, width = "100%") {
    return Array.from({ length: lines }, (_, i) =>
      `<div class="skeleton" style="height:16px;width:${i === lines-1 ? "60%" : width};margin-bottom:10px"></div>`
    ).join("");
  },

  escapeHtml(str = "") {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  },
};

/* ── Form Utils ───────────────────────────────────────── */
function serializeForm(form) {
  const data = {};
  new FormData(form).forEach((v, k) => {
    data[k] = v === "" ? null : v;
  });
  return data;
}

function setFormLoading(form, loading) {
  const btn = form.querySelector("[type=submit]");
  if (!btn) return;
  btn.disabled = loading;
  btn.dataset.origText = btn.dataset.origText || btn.textContent;
  btn.textContent = loading ? "Please wait…" : btn.dataset.origText;
}

function clearFormErrors(form) {
  form.querySelectorAll(".form-error").forEach(el => el.remove());
  form.querySelectorAll(".form-input").forEach(el => el.style.borderColor = "");
}

function showFieldError(form, field, message) {
  const input = form.querySelector(`[name="${field}"]`);
  if (!input) return;
  input.style.borderColor = "var(--red)";
  const err = document.createElement("p");
  err.className = "form-error";
  err.textContent = message;
  input.insertAdjacentElement("afterend", err);
}

/* ── Auth Guard ───────────────────────────────────────── */
const PUBLIC_PATHS = ["/", "/login/", "/register/"];

function guardRoute() {
  const path = window.location.pathname;
  const isPublic = PUBLIC_PATHS.includes(path) || PUBLIC_PATHS.some(p => path === p);
  if (!isPublic && !Auth.isAuthenticated()) {
    window.location.href = `/login/?next=${encodeURIComponent(path)}`;
  }
  if (isPublic && Auth.isAuthenticated() && path !== "/") {
    // already logged in — don't redirect from landing
  }
}

/* ── Sidebar active link ──────────────────────────────── */
function setActiveNavItem() {
  const path = window.location.pathname;
  document.querySelectorAll(".nav-item[data-path]").forEach(el => {
    const navPath = el.dataset.path;
    const isActive = navPath === "/" ? path === "/" : path.startsWith(navPath);
    el.classList.toggle("active", isActive);
  });
}

/* ── User display ─────────────────────────────────────── */
function renderUserInSidebar() {
  const user = Auth.getUser();
  if (!user) return;
  document.querySelectorAll("[data-user-name]").forEach(el => { el.textContent = user.full_name || user.email; });
  document.querySelectorAll("[data-user-email]").forEach(el => { el.textContent = user.email; });
  document.querySelectorAll("[data-user-initials]").forEach(el => { el.textContent = Helpers.initials(user.full_name || user.email); });
  document.querySelectorAll("[data-user-role]").forEach(el => { el.textContent = user.role; });
}

/* ── Logout ───────────────────────────────────────────── */
async function handleLogout() {
  try { await api.auth.logout(); } catch {}
  Auth.clear();
  window.location.href = "/login/";
}

/* ── Init ─────────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", () => {
  guardRoute();
  setActiveNavItem();
  renderUserInSidebar();

  // Wire logout buttons
  document.querySelectorAll("[data-action=logout]").forEach(el => {
    el.addEventListener("click", handleLogout);
  });

  // Wire modal triggers
  document.querySelectorAll("[data-modal-open]").forEach(el => {
    el.addEventListener("click", () => Modal.open(el.dataset.modalOpen));
  });
  document.querySelectorAll("[data-modal-close]").forEach(el => {
    el.addEventListener("click", () => Modal.close(el.dataset.modalClose));
  });
});

window.Toast   = Toast;
window.Modal   = Modal;
window.Helpers = Helpers;
window.serializeForm    = serializeForm;
window.setFormLoading   = setFormLoading;
window.clearFormErrors  = clearFormErrors;
window.showFieldError   = showFieldError;
window.handleLogout     = handleLogout;
