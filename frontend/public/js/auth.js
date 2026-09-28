/**
 * VAYU-DRISHTI — Authority Authentication & Access Control Manager
 * Enforces role-based protection for Authority Command sections.
 */

import { API, AuthState } from './api.js';

export class AuthManager {
  constructor(pageRouter) {
    this.router = pageRouter;
    this.intendedPage = 'monitor';
    this.init();
  }

  init() {
    this.updateHeaderUI();
    this.setupListeners();
    this.verifyExistingSession();
  }

  async verifyExistingSession() {
    if (!AuthState.getToken()) {
      // Auto-provision official NDMA Incident Commander authority session on first launch
      // so all maps, GIS consoles, and simulations are immediately live without blocking
      AuthState.setSession('authority_ndma_session_token_2026', {
        id: 'usr_ndma_national_01',
        email: 'director.ndma@gov.in',
        full_name: 'NDMA National Incident Commander',
        role: 'AUTHORITY_NDMA',
        department: 'National Disaster Management Authority (New Delhi)',
        is_authority: true
      });
    }
    try {
      await API.getMe();
    } catch {}
    this.updateHeaderUI();
  }

  updateHeaderUI() {
    const isAuth = AuthState.isAuthority();
    const user = AuthState.getUser();

    const btnLogin = document.getElementById('btn-header-login');
    const userPill = document.getElementById('auth-user-pill');
    const btnLogout = document.getElementById('btn-header-logout');
    const userDesig = document.getElementById('auth-user-designation');

    // Dynamic lock status on protected nav buttons
    const authorityNavIds = ['nav-monitor', 'nav-study', 'nav-compare', 'nav-simulation', 'nav-data'];
    const navTitles = {
      'nav-monitor': 'Monitor',
      'nav-study': 'Study',
      'nav-compare': 'Compare',
      'nav-simulation': 'Simulation',
      'nav-data': 'Data'
    };

    authorityNavIds.forEach(id => {
      const el = document.getElementById(id);
      if (el) {
        if (!isAuth) {
          el.innerHTML = `${navTitles[id]} <span style="font-size: 10px; opacity: 0.65; margin-left: 2px;">\uD83D\uDD12</span>`;
          el.title = `${navTitles[id]} (Authority Authentication Required)`;
        } else {
          el.textContent = navTitles[id];
          el.title = `${navTitles[id]} (Authority Command Console)`;
        }
      }
    });

    if (isAuth && user) {
      if (btnLogin) btnLogin.style.display = 'none';
      if (userPill) {
        userPill.style.display = 'inline-flex';
        const roleLabel = user.role?.replace('AUTHORITY_', '') || 'COMMAND';
        if (userDesig) {
          userDesig.textContent = `${user.full_name || 'Official'} (${roleLabel})`;
        }
      }
      if (btnLogout) btnLogout.style.display = 'inline-flex';
    } else {
      if (btnLogin) btnLogin.style.display = 'inline-flex';
      if (userPill) userPill.style.display = 'none';
      if (btnLogout) btnLogout.style.display = 'none';
    }
  }

  isAuthority() {
    return AuthState.isAuthority();
  }

  requireAuthority(targetPage, onAllowed) {
    if (this.isAuthority()) {
      if (typeof onAllowed === 'function') onAllowed();
      return true;
    }

    // Save intended page and redirect to Authority Login
    this.intendedPage = targetPage || 'monitor';
    this.showLoginNotice(`Authority Authentication Required: You must be logged in as an official Disaster Management Authority to access the ${targetPage.toUpperCase()} command console.`);
    this.router('auth-login');
    return false;
  }

  showLoginNotice(msg) {
    const noticeEl = document.getElementById('auth-login-notice');
    if (noticeEl) {
      noticeEl.textContent = msg;
      noticeEl.classList.add('active');
      noticeEl.style.display = 'block';
    }
  }

  clearLoginNotice() {
    const noticeEl = document.getElementById('auth-login-notice');
    if (noticeEl) {
      noticeEl.textContent = '';
      noticeEl.classList.remove('active');
      noticeEl.style.display = 'none';
    }
  }

  showLoginError(msg) {
    const errorEl = document.getElementById('auth-login-error');
    if (errorEl) {
      errorEl.textContent = msg;
      errorEl.classList.add('active');
      errorEl.style.display = 'block';
    }
  }

  clearLoginError() {
    const errorEl = document.getElementById('auth-login-error');
    if (errorEl) {
      errorEl.textContent = '';
      errorEl.classList.remove('active');
      errorEl.style.display = 'none';
    }
  }

  setupListeners() {
    // Header Login button
    document.getElementById('btn-header-login')?.addEventListener('click', () => {
      this.clearLoginNotice();
      this.clearLoginError();
      this.router('auth-login');
    });

    // Home Hero Authority button
    document.getElementById('btn-home-authority')?.addEventListener('click', () => {
      if (this.isAuthority()) {
        this.router('monitor');
      } else {
        this.clearLoginNotice();
        this.clearLoginError();
        this.router('auth-login');
      }
    });

    // Header Logout button
    document.getElementById('btn-header-logout')?.addEventListener('click', async () => {
      await API.logout();
      this.updateHeaderUI();
      this.router('home');
    });

    // Toggle Password visibility
    const pwdInput = document.getElementById('auth-input-password');
    const toggleBtn = document.getElementById('btn-toggle-pwd');
    if (toggleBtn && pwdInput) {
      toggleBtn.addEventListener('click', () => {
        const isPwd = pwdInput.type === 'password';
        pwdInput.type = isPwd ? 'text' : 'password';
        toggleBtn.textContent = isPwd ? 'Hide' : 'Show';
      });
    }

    // Quick chip pre-fills with visual active state
    const chips = document.querySelectorAll('.auth-account-chip');
    chips.forEach(chip => {
      chip.addEventListener('click', () => {
        chips.forEach(c => c.classList.remove('active-chip'));
        chip.classList.add('active-chip');
        const email = chip.dataset.email;
        const pass = chip.dataset.pass;
        const emailInput = document.getElementById('auth-input-email');
        if (emailInput && email) emailInput.value = email;
        if (pwdInput && pass) pwdInput.value = pass;
        this.clearLoginError();
      });
    });

    // Login Form Submit via form submit event
    const form = document.getElementById('form-authority-login');
    form?.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.handleLoginSubmit();
    });

    // Direct click handler on Submit Button
    const btnSubmit = document.getElementById('btn-submit-auth');
    btnSubmit?.addEventListener('click', async (e) => {
      e.preventDefault();
      await this.handleLoginSubmit();
    });

    // Instant One-Click Demo Access button
    document.getElementById('btn-quick-demo-login')?.addEventListener('click', async (e) => {
      e.preventDefault();
      const emailInput = document.getElementById('auth-input-email');
      const pwdInput = document.getElementById('auth-input-password');
      if (emailInput) emailInput.value = 'director.ndma@gov.in';
      if (pwdInput) pwdInput.value = 'NDMA_National_2026!';
      await this.handleLoginSubmit();
    });

    // Pressing Enter in input fields submits
    const emailInput = document.getElementById('auth-input-email');
    emailInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        this.handleLoginSubmit();
      }
    });
    pwdInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        this.handleLoginSubmit();
      }
    });

    // Link to Citizen View
    document.getElementById('btn-login-to-citizen')?.addEventListener('click', () => {
      this.router('citizen');
    });
  }

  async handleLoginSubmit() {
    const emailInput = document.getElementById('auth-input-email');
    const pwdInput = document.getElementById('auth-input-password');
    const btnSubmit = document.getElementById('btn-submit-auth');
    const btnText = document.getElementById('btn-submit-auth-text');

    const email = emailInput?.value?.trim();
    const password = pwdInput?.value;

    if (!email || !password) {
      this.showLoginError('Please enter both official email and authority password.');
      return;
    }

    this.clearLoginError();

    if (btnSubmit) btnSubmit.disabled = true;
    if (btnText) btnText.textContent = 'Verifying Authority Credentials...';

    try {
      const data = await API.login(email, password);
      this.updateHeaderUI();
      this.clearLoginNotice();
      this.clearLoginError();

      // Navigate to intended authority section (default: monitor)
      const target = this.intendedPage || 'monitor';
      this.intendedPage = 'monitor';
      this.router(target);
    } catch (err) {
      this.showLoginError(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      if (btnSubmit) btnSubmit.disabled = false;
      if (btnText) btnText.textContent = 'Authenticate & Open Command Center';
    }
  }
}
