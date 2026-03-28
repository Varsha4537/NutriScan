/**
 * auth.js — Handles login and register form submissions
 */

(function () {
  // ── API Service Layer ────────────────────────────────────────────────
  const ApiService = {
    login: async (email, password) => {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Login failed.');
      return data;
    },
    register: async (name, email, password, dietary_profile) => {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password, dietary_profile })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Registration failed.');
      return data;
    }
  };

  // ── UI Helpers ───────────────────────────────────────────────────────
  function showAlert(id, message, type = 'error') {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = `alert alert-${type} show`;
    el.textContent = message;
  }
  function hideAlert(id) {
    const el = document.getElementById(id);
    if (el) el.classList.remove('show');
  }
  function setLoading(btn, loading) {
    if (loading) {
      btn.dataset.originalText = btn.innerHTML;
      btn.innerHTML = '<span class="spinner"></span> Please wait…';
      btn.disabled = true;
    } else {
      btn.innerHTML = btn.dataset.originalText || 'Submit';
      btn.disabled = false;
    }
  }

  // ──  Login form ───────────────────────────────────────────────────────
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert('login-alert');
      const btn   = document.getElementById('login-btn');
      const email = document.getElementById('email').value.trim();
      const pwd   = document.getElementById('password').value;

      if (!email || !pwd) {
        return showAlert('login-alert', 'Please fill in all fields.');
      }

      setLoading(btn, true);
      try {
        const data = await ApiService.login(email, pwd);
        showAlert('login-alert', '✅ Logged in! Redirecting…', 'success');
        setTimeout(() => window.location.href = data.redirect || '/dashboard', 600);
      } catch (err) {
        showAlert('login-alert', err.message || 'Network error. Please try again.');
        setLoading(btn, false);
      }
    });
  }

  // ── Register form ─────────────────────────────────────────────────────
  const registerForm = document.getElementById('register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      hideAlert('register-alert');
      const btn     = document.getElementById('register-btn');
      const name    = document.getElementById('name').value.trim();
      const email   = document.getElementById('email').value.trim();
      const pwd     = document.getElementById('password').value;
      const confirm = document.getElementById('confirm').value;

      const dietType   = document.querySelector('input[name="diet-type"]:checked').value;
      const isGlutenFree = document.getElementById('gluten-free').checked;
      
      const dietaryProfile = [dietType];
      if (isGlutenFree) dietaryProfile.push('gluten-free');

      if (!name || !email || !pwd || !confirm) {
        return showAlert('register-alert', 'Please fill in all fields.');
      }
      if (pwd.length < 6) {
        return showAlert('register-alert', 'Password must be at least 6 characters.');
      }
      if (pwd !== confirm) {
        return showAlert('register-alert', 'Passwords do not match.');
      }

      setLoading(btn, true);
      try {
        const data = await ApiService.register(name, email, pwd, dietaryProfile);
        showAlert('register-alert', '🎉 Account created! Redirecting…', 'success');
        setTimeout(() => window.location.href = data.redirect || '/dashboard', 700);
      } catch (err) {
        showAlert('register-alert', err.message || 'Network error. Please try again.');
        setLoading(btn, false);
      }
    });
  }
})();
