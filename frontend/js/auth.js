/**
 * SkyFlow Authentication & Session Module
 */
const AuthModule = {
  currentUser: null,

  init() {
    const savedUser = localStorage.getItem('skyflow_user');
    if (savedUser) {
      try {
        AuthModule.currentUser = JSON.parse(savedUser);
      } catch (e) {
        AuthModule.logout();
      }
    }
    AuthModule.updateUI();

    const pill = document.getElementById('user-profile-pill');
    if (pill) {
      pill.onclick = (e) => AuthModule.toggleUserDropdown(e);
    }
  },

  openLoginModal() {
    document.getElementById('modal-login')?.classList.add('active');
    document.getElementById('modal-register')?.classList.remove('active');
  },

  openRegisterModal() {
    document.getElementById('modal-register')?.classList.add('active');
    document.getElementById('modal-login')?.classList.remove('active');
  },

  closeModals() {
    document.getElementById('modal-login')?.classList.remove('active');
    document.getElementById('modal-register')?.classList.remove('active');
  },

  switchToRegister() {
    AuthModule.openRegisterModal();
  },

  switchToLogin() {
    AuthModule.openLoginModal();
  },

  async handleLogin(event) {
    event.preventDefault();
    const btn = document.getElementById('btn-login-submit');
    const originalContent = btn ? btn.innerHTML : 'Login to Account';

    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;

    try {
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="btn-spinner"></span> Authenticating...';
      }

      const data = await API.post('/auth/login', { email, password });
      localStorage.setItem('skyflow_token', data.access_token);
      
      // Fetch full user profile
      const userProfile = await API.get('/users/me');
      AuthModule.currentUser = userProfile;
      localStorage.setItem('skyflow_user', JSON.stringify(userProfile));

      AuthModule.updateUI();
      AuthModule.closeModals();
      API.showToast(`Welcome back, ${userProfile.full_name || 'Passenger'}!`, 'success');

      // If Admin or Ops Agent, navigate directly to Admin Operations Portal
      const roleName = AuthModule.getRoleName();
      if (['SUPER_ADMIN', 'OPS_AGENT', 'ADMIN'].includes(roleName) || userProfile.email === 'admin@gmail.com') {
        if (typeof AdminModule !== 'undefined' && typeof AdminModule.init === 'function') {
          AdminModule.init();
        }
        if (typeof App !== 'undefined' && typeof App.navigate === 'function') {
          App.navigate('admin');
        }
      } else if (App.currentView === 'bookings') {
        DashboardModule.loadBookings();
      }
    } catch (error) {
      // Handled in API client
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = originalContent;
      }
    }
  },

  async handleRegister(event) {
    event.preventDefault();
    const btn = document.getElementById('btn-register-submit');
    const originalContent = btn ? btn.innerHTML : 'Create Account';

    const full_name = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;

    try {
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="btn-spinner"></span> Creating Account...';
      }

      await API.post('/auth/register', { full_name, email, password });
      API.showToast('Account created successfully! Logging you in...', 'success');

      // Auto login
      const data = await API.post('/auth/login', { email, password });
      localStorage.setItem('skyflow_token', data.access_token);

      const userProfile = await API.get('/users/me');
      AuthModule.currentUser = userProfile;
      localStorage.setItem('skyflow_user', JSON.stringify(userProfile));

      AuthModule.updateUI();
      AuthModule.closeModals();
    } catch (error) {
      // Handled in API
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = originalContent;
      }
    }
  },

  logout() {
    localStorage.removeItem('skyflow_token');
    localStorage.removeItem('skyflow_user');
    AuthModule.currentUser = null;
    AuthModule.updateUI();
    API.showToast('You have been logged out.', 'info');
    App.navigate('search');
  },

  updateUI() {
    const guestButtons = document.getElementById('guest-auth-buttons');
    const userPill = document.getElementById('user-profile-pill');
    const adminNav = document.getElementById('nav-admin');

    const mobGuestButtons = document.getElementById('mobile-guest-buttons');
    const mobUserCard = document.getElementById('mobile-user-card');
    const mobAdminNav = document.getElementById('mob-nav-admin');

    if (AuthModule.currentUser) {
      const userRole = AuthModule.getRoleName();
      const canAccessAdmin = AuthModule.isAgentOrAdmin();

      if (guestButtons) guestButtons.style.display = 'none';
      if (mobGuestButtons) mobGuestButtons.style.display = 'none';

      if (userPill) {
        userPill.style.display = 'flex';
        const nameEl = document.getElementById('user-pill-name');
        const roleEl = document.getElementById('user-pill-role');
        const avatarEl = document.getElementById('user-avatar-initials');

        if (nameEl) nameEl.textContent = AuthModule.currentUser.full_name || 'User';
        if (roleEl) roleEl.textContent = userRole;
        if (avatarEl) avatarEl.textContent = (AuthModule.currentUser.full_name || 'U').charAt(0).toUpperCase();
      }

      if (mobUserCard) {
        mobUserCard.style.display = 'flex';
        const mobNameEl = document.getElementById('mobile-user-name');
        const mobRoleEl = document.getElementById('mobile-user-role');
        const mobAvatarEl = document.getElementById('mobile-user-avatar');

        if (mobNameEl) mobNameEl.textContent = AuthModule.currentUser.full_name || 'User';
        if (mobRoleEl) mobRoleEl.textContent = userRole;
        if (mobAvatarEl) mobAvatarEl.textContent = (AuthModule.currentUser.full_name || 'U').charAt(0).toUpperCase();
      }

      // Update user dropdown menu fields
      const dropName = document.getElementById('dropdown-user-name');
      const dropEmail = document.getElementById('dropdown-user-email');
      const dropRole = document.getElementById('dropdown-user-role');
      const dropAvatar = document.getElementById('dropdown-user-avatar');
      const dropAdminLink = document.getElementById('dropdown-admin-link');

      if (dropName) dropName.textContent = AuthModule.currentUser.full_name || 'Passenger User';
      if (dropEmail) dropEmail.textContent = AuthModule.currentUser.email || '';
      if (dropRole) dropRole.textContent = userRole;
      if (dropAvatar) dropAvatar.textContent = (AuthModule.currentUser.full_name || 'U').charAt(0).toUpperCase();
      if (dropAdminLink) dropAdminLink.style.display = canAccessAdmin ? 'block' : 'none';

      // Show Admin portal if Super Admin or Ops Agent
      if (adminNav) adminNav.style.display = canAccessAdmin ? 'block' : 'none';
      if (mobAdminNav) mobAdminNav.style.display = canAccessAdmin ? 'block' : 'none';
    } else {
      if (guestButtons) guestButtons.style.display = 'flex';
      if (userPill) userPill.style.display = 'none';
      if (adminNav) adminNav.style.display = 'none';

      if (mobGuestButtons) mobGuestButtons.style.display = 'flex';
      if (mobUserCard) mobUserCard.style.display = 'none';
      if (mobAdminNav) mobAdminNav.style.display = 'none';
      AuthModule.closeUserDropdown();
    }
  },

  toggleUserDropdown(event) {
    if (event && typeof event.stopPropagation === 'function') {
      event.stopPropagation();
    }
    const dropdown = document.getElementById('user-dropdown-menu');
    const pill = document.getElementById('user-profile-pill');
    if (!dropdown) return;

    const isActive = dropdown.classList.contains('active');
    if (isActive) {
      AuthModule.closeUserDropdown();
    } else {
      dropdown.classList.add('active');
      pill?.classList.add('active');
    }
  },

  closeUserDropdown() {
    const dropdown = document.getElementById('user-dropdown-menu');
    const pill = document.getElementById('user-profile-pill');
    if (dropdown) dropdown.classList.remove('active');
    if (pill) pill.classList.remove('active');
  },

  openUserMenu() {
    AuthModule.toggleUserDropdown();
  },

  getRoleName() {
    if (!AuthModule.currentUser) return '';
    let r = AuthModule.currentUser.role;
    if (typeof r === 'object' && r !== null) {
      r = r.name || r.value || '';
    }
    if (!r && AuthModule.currentUser.role_name) {
      r = AuthModule.currentUser.role_name;
    }
    const roleStr = String(r || '').toUpperCase();
    if (!roleStr && AuthModule.currentUser.email === 'admin@gmail.com') {
      return 'SUPER_ADMIN';
    }
    return roleStr || 'PASSENGER';
  },

  isAdmin() {
    const role = AuthModule.getRoleName();
    return role === 'SUPER_ADMIN' || AuthModule.currentUser?.email === 'admin@gmail.com';
  },

  isAgentOrAdmin() {
    const role = AuthModule.getRoleName();
    return ['SUPER_ADMIN', 'OPS_AGENT', 'ADMIN'].includes(role) || AuthModule.currentUser?.email === 'admin@gmail.com';
  }
};

// Global click-outside listener to close dropdown
document.addEventListener('click', (e) => {
  const wrapper = document.getElementById('user-menu-wrapper');
  if (wrapper && !wrapper.contains(e.target)) {
    AuthModule.closeUserDropdown();
  }
});
