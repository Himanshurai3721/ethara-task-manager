/**
 * api.js — All HTTP calls to the Flask backend.
 * No ES modules — plain globals, works in any browser without a bundler.
 */

const API = '/api';

/* ── Storage helpers ─────────────────────────────────────────── */
function getToken()  { return localStorage.getItem('tt_token'); }
function getUser()   { const u = localStorage.getItem('tt_user'); return u ? JSON.parse(u) : null; }
function setAuth(token, user) {
  localStorage.setItem('tt_token', token);
  localStorage.setItem('tt_user', JSON.stringify(user));
}
function clearAuth() {
  localStorage.removeItem('tt_token');
  localStorage.removeItem('tt_user');
}

/* ── Core fetch wrapper ──────────────────────────────────────── */
async function req(path, opts = {}) {
  const token = getToken();
  const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
  if (token) headers['Authorization'] = 'Bearer ' + token;

  const res = await fetch(API + path, { ...opts, headers });
  const data = await res.json().catch(() => ({}));

  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

/* ── Auth ────────────────────────────────────────────────────── */
const Auth = {
  async register(username, email, password, role) {
    const d = await req('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password, role })
    });
    if (d.token) setAuth(d.token, d.user);
    return d;
  },
  async login(username, password) {
    const d = await req('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    if (d.token) setAuth(d.token, d.user);
    return d;
  },
  async me()       { return req('/auth/me'); },
  async users()    { return req('/auth/users'); },
  logout()         { clearAuth(); window.location.href = 'index.html'; }
};

/* ── Projects ────────────────────────────────────────────────── */
const Projects = {
  all()              { return req('/projects'); },
  get(id)            { return req(`/projects/${id}`); },
  create(name, desc) { return req('/projects', { method:'POST', body: JSON.stringify({ name, description: desc }) }); },
  update(id, data)   { return req(`/projects/${id}`, { method:'PUT', body: JSON.stringify(data) }); },
  del(id)            { return req(`/projects/${id}`, { method:'DELETE' }); },
  members(id)        { return req(`/projects/${id}/members`); },
  addMember(id, userId, role) {
    return req(`/projects/${id}/members`, { method:'POST', body: JSON.stringify({ user_id: userId, role }) });
  },
  removeMember(id, userId) { return req(`/projects/${id}/members/${userId}`, { method:'DELETE' }); }
};

/* ── Tasks ───────────────────────────────────────────────────── */
const Tasks = {
  byProject(pid, params) {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return req(`/projects/${pid}/tasks${qs}`);
  },
  get(id)          { return req(`/tasks/${id}`); },
  create(pid, data){ return req(`/projects/${pid}/tasks`, { method:'POST', body: JSON.stringify(data) }); },
  update(id, data) { return req(`/tasks/${id}`, { method:'PUT', body: JSON.stringify(data) }); },
  del(id)          { return req(`/tasks/${id}`, { method:'DELETE' }); },
  mine(params) {
    const qs = params ? '?' + new URLSearchParams(params).toString() : '';
    return req(`/my-tasks${qs}`);
  }
};

/* ── Dashboard ───────────────────────────────────────────────── */
const Dashboard = {
  summary() { return req('/dashboard/summary'); },
  overdue()  { return req('/dashboard/overdue'); },
  recent()   { return req('/dashboard/recent'); }
};
