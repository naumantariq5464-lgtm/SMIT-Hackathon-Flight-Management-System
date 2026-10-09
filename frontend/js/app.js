/**
 * SkyFlow Main Application Controller & View Router
 */
const App = {
  currentView: 'search',

  init() {
    console.log('✈️ SkyFlow Aviation Cloud UI initializing...');

    // Initialize modules
    AuthModule.init();
    SearchModule.init();
    ChatModule.init();
    App.initHeroVideoLoop();

    // Scroll listener for sticky header
    window.addEventListener('scroll', () => {
      const header = document.getElementById('site-header');
      if (header) {
        if (window.scrollY > 20) {
          header.classList.add('scrolled');
        } else {
          header.classList.remove('scrolled');
        }
      }
    });

    // Default route
    App.navigate('search');
  },

  navigate(viewName) {
    App.currentView = viewName;

    // Update active nav links (desktop + mobile)
    document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => link.classList.remove('active'));
    if (viewName === 'search') {
      document.getElementById('nav-search')?.classList.add('active');
      document.getElementById('mob-nav-search')?.classList.add('active');
    }
    if (viewName === 'bookings') {
      document.getElementById('nav-bookings')?.classList.add('active');
      document.getElementById('mob-nav-bookings')?.classList.add('active');
    }
    if (viewName === 'admin') {
      document.getElementById('nav-admin')?.classList.add('active');
      document.getElementById('mob-nav-admin')?.classList.add('active');
    }

    // Show/Hide hero section & search section
    const heroSection = document.getElementById('hero-section');
    const searchSection = document.getElementById('flight-search-section');
    if (heroSection) {
      heroSection.style.display = viewName === 'search' ? 'flex' : 'none';
    }
    if (searchSection) {
      searchSection.style.display = viewName === 'search' ? 'block' : 'none';
    }

    // Switch view
    if (viewName === 'search') {
      if (SearchModule.searchResults.length > 0) {
        App.showView('search-results');
      } else {
        App.hideAllViews();
      }
    } else if (viewName === 'bookings') {
      DashboardModule.loadBookings();
    } else if (viewName === 'admin') {
      AdminModule.init();
    }
  },

  showView(viewId) {
    App.hideAllViews();
    const target = document.getElementById(`view-${viewId}`);
    if (target) {
      target.style.display = 'block';
      target.style.animation = 'none';
      target.offsetHeight; // trigger reflow
      target.style.animation = 'smoothPageFadeIn 0.75s cubic-bezier(0.22, 1, 0.36, 1) forwards';
    }
  },

  hideAllViews() {
    ['search-results', 'seat-map', 'passenger-dashboard', 'admin-portal'].forEach(id => {
      const el = document.getElementById(`view-${id}`);
      if (el) el.style.display = 'none';
    });
  },

  initHeroVideoLoop() {
    const video = document.querySelector('.hero-video-bg');
    if (!video) return;

    // Instant seamless loop without any opacity flash or green background reveal
    video.addEventListener('timeupdate', () => {
      if (video.duration && video.currentTime >= video.duration - 0.08) {
        video.currentTime = 0;
        video.play().catch(() => {});
      }
    });

    video.addEventListener('ended', () => {
      video.currentTime = 0;
      video.play().catch(() => {});
    });
  },

  toggleMobileMenu(open) {
    const drawer = document.getElementById('mobile-nav-drawer');
    const backdrop = document.getElementById('mobile-nav-backdrop');
    if (!drawer || !backdrop) return;

    const shouldOpen = (typeof open === 'boolean') ? open : !drawer.classList.contains('open');
    if (shouldOpen) {
      drawer.classList.add('open');
      backdrop.classList.add('active');
      document.body.style.overflow = 'hidden';
    } else {
      drawer.classList.remove('open');
      backdrop.classList.remove('active');
      document.body.style.overflow = '';
    }
  }
};

// Auto boot on DOM load
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
