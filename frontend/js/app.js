/**
 * app.js — Dashboard application logic.
 * Loaded only on dashboard.html.
 */

/* ── Auth guard ──────────────────────────────────────────────── */
const _user = getUser();
if (!_user) window.location.href = 'index.html';

/* ── State ───────────────────────────────────────────────────── */
let allProjects = [];
let allTasks    = [];

/* ── Init ────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  populateUserUI();
  initNavigation();
  initSidebar();
  initModals();
  loadPage('dashboard');
});

/* ── User UI ─────────────────────────────────────────────────── */
function populateUserUI() {
  const initial = (_user.username || 'U')[0].toUpperCase();
  setText('sb-avatar',   initial);
  setText('sb-username', _user.username);
  setText('sb-role',     _user.role);
  setText('top-avatar',  initial);
  setText('top-username',_user.username);
  setText('top-role',    _user.role);

  // Show "New Project" button only for admins
  if (_user.role === 'admin') {
    const btn = document.getElementById('new-project-btn');
    if (btn) btn.style.display = 'inline-flex';
  }

  document.getElementById('logout-btn').addEventListener('click', () => Auth.logout());
}

/* ── Navigation ──────────────────────────────────────────────── */
function initNavigation() {
  document.querySelectorAll('[data-page]').forEach(el => {
    el.addEventListener('click', e => {
      e.preventDefault();
      loadPage(el.dataset.page);
    });
  });
}

function loadPage(name) {
  // Update sidebar active state
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.page === name);
  });

  // Update topbar title
  const titles = { dashboard: 'Dashboard', projects: 'Projects', tasks: 'My Tasks' };
  setText('page-title', titles[name] || name);

  // Show page
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const page = document.getElementById('page-' + name);
  if (page) page.classList.add('active');

  // Load data
  if (name === 'dashboard') loadDashboard();
  if (name === 'projects')  loadProjects();
  if (name === 'tasks')     loadTasks();
}

/* ── Sidebar mobile toggle ───────────────────────────────────── */
function initSidebar() {
  const toggle  = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  if (!toggle) return;
  toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.addEventListener('click', e => {
    if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
      sidebar.classList.remove('open');
    }
  });
}

/* ═══════════════════════════════════════════════════════════════
   DASHBOARD
   ═══════════════════════════════════════════════════════════════ */

async function loadDashboard() {
  // Greeting
  const hour = new Date().getHours();
  const greet = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  setText('dash-greeting', `${greet}, ${_user.username} 👋`);

  try {
    const [summary, recent] = await Promise.all([
      Dashboard.summary(),
      Dashboard.recent()
    ]);
    renderStatCards(summary);
    renderRecentTable(recent.tasks || []);
  } catch (err) {
    document.getElementById('stat-grid').innerHTML = errorHtml(err.message);
    document.getElementById('recent-tasks-body').innerHTML = errorHtml(err.message);
  }
}

function renderStatCards(s) {
  const t = s.tasks || {};
  const grid = document.getElementById('stat-grid');
  grid.innerHTML = `
    ${statCard('indigo', iconClipboard(), 'Total Tasks',       t.total       || 0)}
    ${statCard('green',  iconCheck(),     'Completed',         t.done        || 0)}
    ${statCard('amber',  iconClock(),     'In Progress',       t.in_progress || 0)}
    ${statCard('red',    iconAlert(),     'Overdue',           t.overdue     || 0)}
  `;
}

function statCard(color, icon, label, value) {
  return `
    <div class="stat-card">
      <div class="stat-icon-wrap ${color}">${icon}</div>
      <div class="stat-info">
        <div class="stat-value">${value}</div>
        <div class="stat-label">${label}</div>
      </div>
    </div>`;
}

function renderRecentTable(tasks) {
  const body = document.getElementById('recent-tasks-body');
  if (!tasks.length) {
    body.innerHTML = emptyState('No tasks yet', 'Create a project and add tasks to get started.');
    return;
  }
  body.innerHTML = `
    <div class="table-wrap">
      <table class="task-table">
        <thead>
          <tr>
            <th>Task</th>
            <th>Assigned To</th>
            <th>Status</th>
            <th>Priority</th>
            <th>Deadline</th>
          </tr>
        </thead>
        <tbody>
          ${tasks.map(t => taskRow(t, false)).join('')}
        </tbody>
      </table>
    </div>`;
}

/* ═══════════════════════════════════════════════════════════════
   PROJECTS
   ═══════════════════════════════════════════════════════════════ */

async function loadProjects() {
  const grid = document.getElementById('project-grid');
  grid.innerHTML = spinnerHtml();
  try {
    const data = await Projects.all();
    allProjects = data.projects || [];
    renderProjects(allProjects);
  } catch (err) {
    grid.innerHTML = errorHtml(err.message);
  }
}

function renderProjects(list) {
  const grid = document.getElementById('project-grid');
  if (!list.length) {
    grid.innerHTML = `<div class="empty-state">
      ${iconFolder(48)}
      <h3>No projects yet</h3>
      <p>${_user.role === 'admin' ? 'Create your first project to get started.' : 'Ask an admin to add you to a project.'}</p>
      ${_user.role === 'admin' ? `<button class="btn-primary" onclick="openModal('modal-project')">+ New Project</button>` : ''}
    </div>`;
    return;
  }
  grid.innerHTML = list.map(p => `
    <div class="project-card">
      <div class="project-card-top">
        <div class="project-card-icon">${iconFolder(20)}</div>
        <div class="project-card-actions">
          ${_user.role === 'admin' ? `
            <button class="action-btn del" onclick="deleteProject(${p.id})" title="Delete project">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/></svg>
            </button>` : ''}
        </div>
      </div>
      <div>
        <div class="project-card-name">${esc(p.name)}</div>
        <div class="project-card-desc">${esc(p.description || 'No description provided.')}</div>
      </div>
      <div class="project-card-footer">
        <div class="project-stat">
          <div class="project-stat-val">${(p.members || []).length}</div>
          <div class="project-stat-lbl">Members</div>
        </div>
      </div>
    </div>`).join('');
}

window.deleteProject = async function(id) {
  if (!confirm('Delete this project and all its tasks?')) return;
  try {
    await Projects.del(id);
    toast('Project deleted', 'success');
    loadProjects();
  } catch (err) { toast(err.message, 'error'); }
};

/* ═══════════════════════════════════════════════════════════════
   TASKS
   ═══════════════════════════════════════════════════════════════ */

async function loadTasks() {
  const wrap = document.getElementById('tasks-table-wrap');
  wrap.innerHTML = spinnerHtml();

  try {
    // Load projects for filter dropdown + task modal
    if (!allProjects.length) {
      const pd = await Projects.all();
      allProjects = pd.projects || [];
    }
    populateProjectFilter();
    populateTaskProjectSelect();

    // Load users for assign dropdown
    const ud = await Auth.users();
    populateAssignSelect(ud.users || []);

    // Fetch tasks
    const params = {};
    const statusVal   = document.getElementById('filter-status').value;
    const priorityVal = document.getElementById('filter-priority').value;
    if (statusVal)   params.status   = statusVal;
    if (priorityVal) params.priority = priorityVal;

    const projectVal = document.getElementById('filter-project').value;
    let tasks = [];

    if (projectVal) {
      const td = await Tasks.byProject(projectVal, params);
      tasks = (td.tasks || []).map(t => ({ ...t, _projectName: projectName(t.project_id) }));
    } else if (_user.role === 'admin') {
      // Admin: fetch tasks from all projects
      for (const p of allProjects) {
        const td = await Tasks.byProject(p.id, params);
        tasks = tasks.concat((td.tasks || []).map(t => ({ ...t, _projectName: p.name })));
      }
    } else {
      const td = await Tasks.mine(params);
      tasks = (td.tasks || []).map(t => ({ ...t, _projectName: projectName(t.project_id) }));
    }

    allTasks = tasks;
    renderTasksTable(tasks);
  } catch (err) {
    wrap.innerHTML = errorHtml(err.message);
  }
}

function renderTasksTable(tasks) {
  const wrap = document.getElementById('tasks-table-wrap');
  if (!tasks.length) {
    wrap.innerHTML = emptyState('No tasks found', 'Try adjusting your filters or create a new task.');
    return;
  }
  wrap.innerHTML = `
    <table class="task-table">
      <thead>
        <tr>
          <th>Task</th>
          <th>Assigned To</th>
          <th>Status</th>
          <th>Priority</th>
          <th>Deadline</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        ${tasks.map(t => taskRow(t, true)).join('')}
      </tbody>
    </table>`;
}

function taskRow(t, showActions) {
  const overdue = t.is_overdue;
  return `
    <tr class="${overdue ? 'overdue' : ''}">
      <td class="task-title-cell">
        <span class="task-title-text" title="${esc(t.title)}">${esc(t.title)}</span>
        ${t._projectName || t.project_name
          ? `<div class="task-project-tag">${esc(t._projectName || t.project_name)}</div>`
          : ''}
      </td>
      <td>
        ${t.assigned_username
          ? `<div class="assignee-cell">
               <div class="assignee-avatar">${t.assigned_username[0].toUpperCase()}</div>
               ${esc(t.assigned_username)}
             </div>`
          : '<span style="color:var(--slate-400);font-size:.8rem">Unassigned</span>'}
      </td>
      <td>
        ${showActions
          ? `<select class="status-select" onchange="updateStatus(${t.id}, this.value)">
               <option value="todo"        ${t.status==='todo'        ?'selected':''}>Todo</option>
               <option value="in_progress" ${t.status==='in_progress' ?'selected':''}>In Progress</option>
               <option value="done"        ${t.status==='done'        ?'selected':''}>Done</option>
             </select>`
          : `<span class="status-badge status-${t.status}">${statusLabel(t.status)}</span>`}
      </td>
      <td><span class="priority-badge priority-${t.priority}">${t.priority}</span></td>
      <td class="deadline-cell ${overdue ? 'deadline-overdue' : ''}">
        ${t.deadline ? formatDate(t.deadline) + (overdue ? ' ⚠' : '') : '—'}
      </td>
      ${showActions ? `
      <td>
        <button class="action-btn del" onclick="deleteTask(${t.id})" title="Delete task">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/></svg>
        </button>
      </td>` : '<td></td>'}
    </tr>`;
}

window.updateStatus = async function(taskId, status) {
  try {
    await Tasks.update(taskId, { status });
    toast('Status updated', 'success');
    // Refresh dashboard stats silently if on dashboard
    if (document.getElementById('page-dashboard').classList.contains('active')) loadDashboard();
  } catch (err) { toast(err.message, 'error'); }
};

window.deleteTask = async function(id) {
  if (!confirm('Delete this task?')) return;
  try {
    await Tasks.del(id);
    toast('Task deleted', 'success');
    loadTasks();
  } catch (err) { toast(err.message, 'error'); }
};

/* ── Filter listeners ────────────────────────────────────────── */
['filter-project', 'filter-status', 'filter-priority'].forEach(id => {
  document.getElementById(id)?.addEventListener('change', loadTasks);
});

function populateProjectFilter() {
  const sel = document.getElementById('filter-project');
  if (!sel) return;
  const current = sel.value;
  sel.innerHTML = '<option value="">All Projects</option>' +
    allProjects.map(p => `<option value="${p.id}" ${p.id == current ? 'selected' : ''}>${esc(p.name)}</option>`).join('');
}

function populateTaskProjectSelect() {
  const sel = document.getElementById('task-project');
  if (!sel) return;
  sel.innerHTML = allProjects.length
    ? allProjects.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('')
    : '<option value="">No projects available</option>';
}

function populateAssignSelect(users) {
  const sel = document.getElementById('task-assign');
  if (!sel) return;
  sel.innerHTML = '<option value="">Unassigned</option>' +
    users.map(u => `<option value="${u.id}">${esc(u.username)}</option>`).join('');
}

function projectName(id) {
  const p = allProjects.find(p => p.id === id);
  return p ? p.name : '';
}

/* ═══════════════════════════════════════════════════════════════
   MODALS
   ═══════════════════════════════════════════════════════════════ */

function initModals() {
  // Close on overlay click
  document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', e => {
      if (e.target === overlay) overlay.classList.remove('open');
    });
  });

  // Create project
  document.getElementById('form-project').addEventListener('submit', async e => {
    e.preventDefault();
    const name = document.getElementById('proj-name').value.trim();
    const desc = document.getElementById('proj-desc').value.trim();
    if (!name) return;
    try {
      await Projects.create(name, desc);
      closeModal('modal-project');
      e.target.reset();
      toast('Project created!', 'success');
      loadProjects();
    } catch (err) { toast(err.message, 'error'); }
  });

  // Create task
  document.getElementById('form-task').addEventListener('submit', async e => {
    e.preventDefault();
    const pid      = document.getElementById('task-project').value;
    const title    = document.getElementById('task-title').value.trim();
    const desc     = document.getElementById('task-desc').value.trim();
    const status   = document.getElementById('task-status').value;
    const priority = document.getElementById('task-priority').value;
    const deadline = document.getElementById('task-deadline').value;
    const assignTo = document.getElementById('task-assign').value;

    if (!pid || !title) { toast('Project and title are required', 'error'); return; }

    try {
      await Tasks.create(pid, {
        title, description: desc, status, priority,
        deadline: deadline ? deadline + 'T00:00:00' : null,
        assigned_to: assignTo ? parseInt(assignTo) : null
      });
      closeModal('modal-task');
      e.target.reset();
      toast('Task created!', 'success');
      if (document.getElementById('page-tasks').classList.contains('active')) loadTasks();
      if (document.getElementById('page-dashboard').classList.contains('active')) loadDashboard();
    } catch (err) { toast(err.message, 'error'); }
  });
}

function openModal(id)  { document.getElementById(id)?.classList.add('open'); }
function closeModal(id) { document.getElementById(id)?.classList.remove('open'); }

// Expose for onclick in HTML
window.openModal  = openModal;
window.closeModal = closeModal;

/* ═══════════════════════════════════════════════════════════════
   HELPERS
   ═══════════════════════════════════════════════════════════════ */

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function esc(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g,'&amp;').replace(/</g,'&lt;')
    .replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function statusLabel(s) {
  return { todo: 'Todo', in_progress: 'In Progress', done: 'Done' }[s] || s;
}

function spinnerHtml() {
  return '<div class="spinner-wrap"><div class="spinner"></div></div>';
}

function errorHtml(msg) {
  return `<div style="padding:2rem;color:var(--red-600);font-size:.875rem">⚠ ${esc(msg)}</div>`;
}

function emptyState(title, desc) {
  return `<div class="empty-state">
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg>
    <h3>${title}</h3><p>${desc}</p>
  </div>`;
}

/* ── Toast ───────────────────────────────────────────────────── */
let _toastTimer;
function toast(msg, type = '') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast show' + (type ? ' ' + type : '');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => el.classList.remove('show'), 3000);
}

/* ── SVG icons ───────────────────────────────────────────────── */
function iconClipboard() {
  return `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg>`;
}
function iconCheck() {
  return `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`;
}
function iconClock() {
  return `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`;
}
function iconAlert() {
  return `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
}
function iconFolder(size = 20) {
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>`;
}
