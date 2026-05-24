/* Dashboard page logic */

async function loadDashboard() {
  await Promise.all([loadStats(), loadRecentProjects(), loadMyTasks()]);
}

async function loadStats() {
  try {
    const [projectsData, myTasksData] = await Promise.all([
      api.projects.list({ page_size: 100 }),
      api.tasks.mine(),
    ]);

    const total   = projectsData.count || 0;
    const active  = (projectsData.results || []).filter(p => p.status === "active").length;
    const myTotal = myTasksData.count || 0;
    const overdue = (myTasksData.results || []).filter(t => t.is_overdue).length;

    document.getElementById("statsBar").innerHTML = `
      <div class="stat-card">
        <div class="stat-label">Total Projects</div>
        <div class="stat-value">${total}</div>
        <div class="stat-delta">${active} active</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">My Tasks</div>
        <div class="stat-value">${myTotal}</div>
        <div class="stat-delta ${overdue ? 'down' : ''}">${overdue} overdue</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">In Progress</div>
        <div class="stat-value text-blue">${(myTasksData.results||[]).filter(t=>t.status==='in_progress').length}</div>
        <div class="stat-delta">tasks active</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Done This Week</div>
        <div class="stat-value text-green">${(myTasksData.results||[]).filter(t=>t.status==='done').length}</div>
        <div class="stat-delta up">completed</div>
      </div>
    `;

    // Update sidebar badge
    const sbc = document.getElementById("sidebarProjectCount");
    if (sbc) sbc.textContent = total;

  } catch (err) {
    console.error("Stats error:", err);
  }
}

async function loadRecentProjects() {
  try {
    const data = await api.projects.list({ page_size: 6 });
    const projects = data.results || [];
    const grid = document.getElementById("recentProjects");
    if (!projects.length) {
      grid.innerHTML = `
        <div class="empty-state" style="grid-column:1/-1">
          <div class="empty-icon">📋</div>
          <h3 class="empty-title">No projects yet</h3>
          <p class="empty-desc">Create your first project to get started.</p>
        </div>`;
      return;
    }
    grid.innerHTML = projects.map(renderProjectCard).join("");
  } catch (err) {
    console.error("Projects error:", err);
  }
}

function renderProjectCard(p) {
  const pct = p.completion_percentage || 0;
  const deadline = p.deadline ? `Due ${Helpers.formatDate(p.deadline)}` : "No deadline";
  return `
    <div class="project-card" onclick="window.location='/projects/${p.id}/'">
      <div class="project-card-header">
        <div>
          <div class="project-name">${Helpers.escapeHtml(p.name)}</div>
          <div class="project-desc">${Helpers.escapeHtml(p.description || "No description")}</div>
        </div>
        ${Helpers.projectStatusBadge(p.status)}
      </div>
      <div class="progress-bar">
        <div class="progress-fill ${pct===100?'green':''}" style="width:${pct}%"></div>
      </div>
      <div class="project-meta">
        <span>👤 ${p.member_count} member${p.member_count!==1?'s':''}</span>
        <span>📌 ${p.task_count} task${p.task_count!==1?'s':''}</span>
        <span>${deadline}</span>
        <span style="margin-left:auto;font-weight:600;color:${pct===100?'var(--green)':'var(--text-secondary)'}">${pct}%</span>
      </div>
    </div>`;
}

async function loadMyTasks(statusFilter = "") {
  const container = document.getElementById("myTasksList");
  container.innerHTML = `<div style="height:60px" class="skeleton" style="border-radius:10px"></div>`;
  try {
    const params = statusFilter ? { status: statusFilter } : {};
    const data = await api.tasks.mine(params);
    const tasks = data.results || [];
    if (!tasks.length) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">✅</div>
          <h3 class="empty-title">All clear!</h3>
          <p class="empty-desc">No tasks assigned to you${statusFilter ? ' with this status' : ''}.</p>
        </div>`;
      return;
    }
    container.innerHTML = `
      <div style="display:grid;gap:8px">
        ${tasks.map(t => `
          <div class="card-elevated flex items-center gap-4"
               style="cursor:pointer"
               onclick="window.location='/projects/${t.project}/'">
            <div style="flex:1;min-width:0">
              <div class="text-sm font-medium" style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
                ${Helpers.escapeHtml(t.title)}
              </div>
              <div class="text-xs text-muted mt-1">${t.project_name || 'Project'}</div>
            </div>
            ${Helpers.priorityBadge(t.priority)}
            ${Helpers.statusBadge(t.status)}
            <div class="text-xs ${t.is_overdue ? 'text-red' : 'text-muted'}">
              ${t.due_date ? Helpers.formatDate(t.due_date) : '—'}
            </div>
          </div>`).join("")}
      </div>`;
  } catch (err) {
    container.innerHTML = `<p class="text-secondary text-sm">Could not load tasks.</p>`;
  }
}

// Create project form
document.getElementById("createProjectForm").addEventListener("submit", async function(e) {
  e.preventDefault();
  clearFormErrors(this);
  setFormLoading(this, true);
  try {
    await api.projects.create(serializeForm(this));
    Modal.close("createProjectModal");
    Toast.success("Project created!");
    this.reset();
    await loadDashboard();
  } catch (err) {
    Toast.error(err.message);
  } finally {
    setFormLoading(this, false);
  }
});

// My tasks filter
document.getElementById("myTasksFilter").addEventListener("change", function() {
  loadMyTasks(this.value);
});

// Boot
loadDashboard();
