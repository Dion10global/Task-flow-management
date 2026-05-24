/* Project detail / Kanban board */
const PROJECT_ID = window.location.pathname.split("/").filter(Boolean).pop();
let currentProject = null;
let allTasks = [];
let members  = [];

const COLUMNS = ["todo", "in_progress", "in_review", "done"];

/* ── Load project ─────────────────────────────────── */
async function loadProject() {
  try {
    currentProject = await api.projects.get(PROJECT_ID);
    document.getElementById("projectName").textContent = currentProject.name;
    document.getElementById("projectDesc").textContent = currentProject.description || "";
    document.getElementById("projectStatusBadge").innerHTML = Helpers.projectStatusBadge(currentProject.status);
    document.title = `${currentProject.name} — TaskFlow`;
  } catch {
    document.getElementById("projectName").textContent = "Project not found";
  }
}

async function loadStats() {
  try {
    const stats = await api.projects.stats(PROJECT_ID);
    const d = stats.data;
    document.getElementById("projectMiniStats").innerHTML = `
      <span>📌 ${d.total} tasks</span>
      <span style="color:var(--blue)">⚡ ${d.by_status.in_progress} in progress</span>
      <span style="color:var(--green)">✓ ${d.by_status.done} done</span>
      <span style="color:${d.overdue ? 'var(--red)' : 'var(--text-muted)'}">⚠ ${d.overdue} overdue</span>
      <span style="margin-left:auto;font-weight:600">${d.completion_percentage}% complete</span>
    `;
  } catch {}
}

/* ── Load tasks ───────────────────────────────────── */
async function loadTasks(params = {}) {
  COLUMNS.forEach(c => {
    document.getElementById(`col-${c}`).innerHTML =
      `<div class="skeleton" style="height:70px;border-radius:8px;margin-bottom:8px"></div>`;
  });
  try {
    const data = await api.tasks.list(PROJECT_ID, params);
    allTasks = data.results || [];
    renderBoard(allTasks);
  } catch {
    COLUMNS.forEach(c => { document.getElementById(`col-${c}`).innerHTML = ""; });
    Toast.error("Failed to load tasks.");
  }
}

function renderBoard(tasks) {
  const grouped = { todo: [], in_progress: [], in_review: [], done: [] };
  tasks.forEach(t => { if (grouped[t.status]) grouped[t.status].push(t); });

  COLUMNS.forEach(status => {
    const col = document.getElementById(`col-${status}`);
    const count = document.getElementById(`count-${status}`);
    const list = grouped[status] || [];
    count.textContent = list.length;

    if (!list.length) {
      col.innerHTML = `<div style="height:40px;border:2px dashed var(--border);border-radius:8px;display:flex;align-items:center;justify-content:center">
        <span class="text-xs text-muted">Empty</span></div>`;
      return;
    }
    col.innerHTML = list.map(t => renderTaskCard(t)).join("");
    col.querySelectorAll(".task-card").forEach(el => {
      el.addEventListener("click", () => openTaskDetail(el.dataset.taskId));
    });
  });
}

function renderTaskCard(t) {
  const overdue = t.is_overdue;
  const initials = t.assigned_to ? Helpers.initials(t.assigned_to.full_name) : null;
  return `
    <div class="task-card" data-task-id="${t.id}">
      <div class="flex items-start justify-between gap-2" style="margin-bottom:6px">
        ${Helpers.priorityBadge(t.priority)}
        ${initials ? `<div class="assignee-avatar" title="${Helpers.escapeHtml(t.assigned_to.full_name)}">${initials}</div>` : ""}
      </div>
      <div class="task-card-title">${Helpers.escapeHtml(t.title)}</div>
      <div class="task-card-meta">
        <span class="text-xs text-muted">💬 ${t.comment_count}</span>
        ${t.due_date ? `<span class="task-due ${overdue ? "overdue" : ""}">${overdue ? "⚠ " : ""}${Helpers.formatDate(t.due_date)}</span>` : ""}
      </div>
    </div>`;
}

/* ── Task detail modal ────────────────────────────── */
async function openTaskDetail(taskId) {
  Modal.open("taskDetailModal");
  const body = document.getElementById("taskDetailBody");
  body.innerHTML = `<div class="skeleton" style="height:200px;border-radius:8px"></div>`;

  try {
    const [task, comments] = await Promise.all([
      api.tasks.get(taskId),
      api.tasks.comments.list(taskId),
    ]);
    document.getElementById("taskDetailTitle").textContent = task.title;

    body.innerHTML = `
      <div class="flex flex-col gap-4">
        <div class="flex gap-3 flex-wrap">
          ${Helpers.statusBadge(task.status)}
          ${Helpers.priorityBadge(task.priority)}
          ${task.due_date ? `<span class="badge ${task.is_overdue?'badge-critical':'badge-todo'}">${task.is_overdue?'⚠ OVERDUE — ':''} Due ${Helpers.formatDate(task.due_date)}</span>` : ""}
        </div>
        ${task.description ? `<p class="text-sm text-secondary" style="line-height:1.6">${Helpers.escapeHtml(task.description)}</p>` : ""}

        <!-- Status updater -->
        <div class="flex gap-2 items-center">
          <span class="text-sm text-secondary">Move to:</span>
          ${["todo","in_progress","in_review","done"].filter(s=>s!==task.status).map(s => `
            <button class="btn btn-secondary btn-sm" onclick="quickUpdateStatus(${task.id},'${s}')">
              ${s.replace("_"," ")}
            </button>`).join("")}
        </div>

        <hr class="divider" />

        <!-- Comments -->
        <div>
          <h4 style="font-family:var(--font-display);font-size:14px;font-weight:600;margin-bottom:12px">
            Comments (${comments.results?.length || 0})
          </h4>
          <div id="commentsList" style="display:flex;flex-direction:column;gap:10px;margin-bottom:16px">
            ${(comments.results || []).map(c => `
              <div class="card-elevated">
                <div class="flex items-center gap-2 mb-2">
                  <div class="avatar" style="width:24px;height:24px;font-size:10px">${Helpers.initials(c.author.full_name)}</div>
                  <span class="text-sm font-medium">${Helpers.escapeHtml(c.author.full_name)}</span>
                  <span class="text-xs text-muted">${Helpers.formatRelative(c.created_at)}</span>
                </div>
                <p class="text-sm">${Helpers.escapeHtml(c.body)}</p>
              </div>`).join("") || '<p class="text-sm text-muted">No comments yet.</p>'}
          </div>
          <form id="commentForm" data-task-id="${task.id}">
            <div class="flex gap-2">
              <input class="form-input" name="body" type="text" placeholder="Add a comment…" style="flex:1" />
              <button type="submit" class="btn btn-primary btn-sm">Send</button>
            </div>
          </form>
        </div>
      </div>`;

    document.getElementById("commentForm").addEventListener("submit", async function(e) {
      e.preventDefault();
      const input = this.querySelector("input");
      const body  = input.value.trim();
      if (!body) return;
      try {
        await api.tasks.comments.create(this.dataset.taskId, body);
        input.value = "";
        Toast.success("Comment added.");
        openTaskDetail(this.dataset.taskId);
      } catch { Toast.error("Failed to post comment."); }
    });

  } catch { body.innerHTML = `<p class="text-secondary">Could not load task.</p>`; }
}

async function quickUpdateStatus(taskId, newStatus) {
  try {
    await api.tasks.updateStatus(taskId, newStatus);
    Toast.success("Status updated!");
    Modal.close("taskDetailModal");
    await loadTasks();
    await loadStats();
  } catch { Toast.error("Failed to update status."); }
}

/* ── Create task ──────────────────────────────────── */
async function loadMembersIntoSelect() {
  try {
    const data = await api.projects.members.list(PROJECT_ID);
    members = data.results || [];
    const sel = document.getElementById("assigneeSelect");
    sel.innerHTML = `<option value="">Unassigned</option>` +
      members.map(m => `<option value="${m.user.id}">${Helpers.escapeHtml(m.user.full_name)}</option>`).join("");
  } catch {}
}

document.getElementById("createTaskForm").addEventListener("submit", async function(e) {
  e.preventDefault();
  clearFormErrors(this);
  setFormLoading(this, true);
  const data = { ...serializeForm(this), project: PROJECT_ID };
  if (!data.assigned_to_id) delete data.assigned_to_id;
  try {
    await api.tasks.create(PROJECT_ID, data);
    Modal.close("createTaskModal");
    Toast.success("Task created!");
    this.reset();
    await loadTasks();
    await loadStats();
  } catch (err) {
    Toast.error(err.message);
  } finally {
    setFormLoading(this, false);
  }
});

/* ── Members modal ────────────────────────────────── */
document.querySelector("[data-modal-open='membersModal']").addEventListener("click", async () => {
  const list = document.getElementById("membersList");
  list.innerHTML = `<div class="skeleton" style="height:60px;border-radius:8px"></div>`;
  try {
    const data = await api.projects.members.list(PROJECT_ID);
    const ms = data.results || [];
    list.innerHTML = ms.map(m => `
      <div class="flex items-center gap-3 p-3" style="border-bottom:1px solid var(--border)">
        <div class="avatar">${Helpers.initials(m.user.full_name)}</div>
        <div style="flex:1">
          <div class="text-sm font-medium">${Helpers.escapeHtml(m.user.full_name)}</div>
          <div class="text-xs text-muted">${m.user.email}</div>
        </div>
        <span class="badge badge-todo">${m.role}</span>
      </div>`).join("") || `<p class="text-secondary text-sm p-4">No members yet.</p>`;
  } catch { list.innerHTML = `<p class="text-secondary text-sm p-4">Failed to load members.</p>`; }
});

/* ── Filters ──────────────────────────────────────── */
let filterDebounce;
document.getElementById("taskSearch").addEventListener("input", function() {
  clearTimeout(filterDebounce);
  filterDebounce = setTimeout(() => {
    const priority = document.getElementById("priorityFilter").value;
    loadTasks({ search: this.value.trim() || undefined, priority: priority || undefined });
  }, 350);
});

document.getElementById("priorityFilter").addEventListener("change", function() {
  const search = document.getElementById("taskSearch").value.trim();
  loadTasks({ search: search || undefined, priority: this.value || undefined });
});

/* ── Boot ─────────────────────────────────────────── */
async function boot() {
  await loadProject();
  await Promise.all([loadStats(), loadTasks(), loadMembersIntoSelect()]);
}
boot();
