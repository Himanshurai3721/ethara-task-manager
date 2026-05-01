/**
 * auth.js — Login / Register page logic.
 * Loaded only on index.html.
 */

/* Redirect if already logged in */
if (getUser()) window.location.href = 'dashboard.html';

/* ── Tab switching ───────────────────────────────────────────── */
function switchTab(tab) {
  const isLogin = tab === 'login';
  document.getElementById('login-form').style.display    = isLogin ? 'block' : 'none';
  document.getElementById('register-form').style.display = isLogin ? 'none'  : 'block';
  document.getElementById('tab-login').classList.toggle('active', isLogin);
  document.getElementById('tab-register').classList.toggle('active', !isLogin);
  document.getElementById('auth-title').textContent    = isLogin ? 'Welcome back'    : 'Create account';
  document.getElementById('auth-subtitle').textContent = isLogin ? 'Sign in to your account' : 'Get started for free';
  hideAlert();
}

/* ── Alert helpers ───────────────────────────────────────────── */
function showAlert(msg, type = 'error') {
  const el = document.getElementById('auth-alert');
  el.textContent = msg;
  el.className = 'auth-alert' + (type === 'success' ? ' success' : '');
  el.style.display = 'block';
}
function hideAlert() {
  document.getElementById('auth-alert').style.display = 'none';
}

/* ── Password visibility toggle ─────────────────────────────── */
function togglePw(inputId, btn) {
  const input = document.getElementById(inputId);
  const isText = input.type === 'text';
  input.type = isText ? 'password' : 'text';
  btn.style.opacity = isText ? '1' : '.5';
}

/* ── Button loading state ────────────────────────────────────── */
function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  btn.disabled = loading;
  btn.querySelector('span').textContent = loading
    ? (btnId === 'login-btn' ? 'Signing in…' : 'Creating account…')
    : (btnId === 'login-btn' ? 'Sign In' : 'Create Account');
}

/* ── Login ───────────────────────────────────────────────────── */
document.getElementById('login-form').addEventListener('submit', async e => {
  e.preventDefault();
  hideAlert();
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;

  if (!username || !password) { showAlert('Please fill in all fields.'); return; }

  setLoading('login-btn', true);
  try {
    await Auth.login(username, password);
    showAlert('Login successful! Redirecting…', 'success');
    setTimeout(() => window.location.href = 'dashboard.html', 600);
  } catch (err) {
    showAlert(err.message);
    setLoading('login-btn', false);
  }
});

/* ── Register ────────────────────────────────────────────────── */
document.getElementById('register-form').addEventListener('submit', async e => {
  e.preventDefault();
  hideAlert();
  const username = document.getElementById('reg-username').value.trim();
  const email    = document.getElementById('reg-email').value.trim();
  const password = document.getElementById('reg-password').value;
  const role     = document.getElementById('reg-role').value;

  if (!username || !email || !password) { showAlert('Please fill in all fields.'); return; }
  if (password.length < 6) { showAlert('Password must be at least 6 characters.'); return; }

  setLoading('register-btn', true);
  try {
    await Auth.register(username, email, password, role);
    showAlert('Account created! Redirecting…', 'success');
    setTimeout(() => window.location.href = 'dashboard.html', 600);
  } catch (err) {
    showAlert(err.message);
    setLoading('register-btn', false);
  }
});
