/* Projects list page logic */
let allProjects = [];

async function loadProjects(params = {}) {
  const grid  = document.getElementById("projectsGrid");
  const empty = document.getElementById("projectsEmpty");
  grid.innerHTML  = Array(4).fill(`<div class="project-card skeleton" style="height:160px"></div>`).join("");
  empty.style.display = "none";

  try {
    const data = await api.projects.list(params);
    allProjects = data.results || [];
    document.getElementById("projectsSubtitle").textContent =
      `${data.count} project${data.count !== 1 ? "s" : ""}`;

    // Sidebar badge
    const sbc = document.getElementById("sidebarProjectCount");
    if (sbc) sbc.textContent = data.count;

    if (!allProjects.length) {
      grid.innerHTML = "";
      empty.style.display = "block";
      return;
    }
    renderGrid(allProjects);
  } catch (err) {
    grid.innerHTML = `<p class="text-secondary text-sm">Failed to load projects.</p>`;
  }
}

function renderGrid(projects) {
  const grid = document.getElementById("projectsGrid");
  grid.innerHTML = projects.map(p => {
    const pct = p.completion_percentage || 0;
    const deadline = p.deadline ? `Due ${Helpers.formatDate(p.deadline)}` : "No deadline";
    return `
      <div class="project-card" onclick="window.location='/projects/${p.id}/'">
        <div class="project-card-header">
          <div style="flex:1;min-width:0">
            <div class="project-name">${Helpers.escapeHtml(p.name)}</div>
            <div class="project-desc">${Helpers.escapeHtml(p.description || "No description")}</div>
          </div>
          ${Helpers.projectStatusBadge(p.status)}
        </div>
        <div class="progress-bar">
          <div class="progress-fill ${pct===100?'green':''}" style="width:${pct}%"></div>
        </div>
        <div class="project-meta">
          <span>👤 ${p.member_count}</span>
          <span>📌 ${p.task_count} tasks</span>
          <span>${deadline}</span>
          <span style="margin-left:auto;font-weight:600;color:${pct===100?'var(--green)':'var(--text-secondary)'}">${pct}%</span>
        </div>
      </div>`;
  }).join("");
}

// Search + filter
let debounceTimer;
document.getElementById("projectSearch").addEventListener("input", function() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    const q = this.value.trim();
    const status = document.getElementById("statusFilter").value;
    loadProjects({ search: q || undefined, status: status || undefined });
  }, 350);
});

document.getElementById("statusFilter").addEventListener("change", function() {
  const q = document.getElementById("projectSearch").value.trim();
  loadProjects({ search: q || undefined, status: this.value || undefined });
});

// Create project
document.getElementById("createProjectForm").addEventListener("submit", async function(e) {
  e.preventDefault();
  clearFormErrors(this);
  setFormLoading(this, true);
  try {
    await api.projects.create(serializeForm(this));
    Modal.close("createProjectModal");
    Toast.success("Project created successfully!");
    this.reset();
    loadProjects();
  } catch (err) {
    const details = err.data?.error?.details || {};
    Object.entries(details).forEach(([f, msgs]) => showFieldError(this, f, Array.isArray(msgs) ? msgs[0] : msgs));
    if (!Object.keys(details).length) Toast.error(err.message);
  } finally {
    setFormLoading(this, false);
  }
});

loadProjects();
