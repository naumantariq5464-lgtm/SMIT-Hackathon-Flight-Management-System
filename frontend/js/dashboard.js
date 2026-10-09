/**
 * SkyFlow Passenger Dashboard Module
 * Bookings, Priority Flight Waitlist / Wishlist Queue, and 1-Year Travel Credits Wallet
 */
const DashboardModule = {
  currentTab: 'bookings',
  bookings: [],
  waitlists: [],
  credits: [],
  userProfile: null,

  async loadBookings() {
    if (!AuthModule.currentUser) {
      App.showView('passenger-dashboard');
      document.getElementById('view-passenger-dashboard').innerHTML = `
        <div class="card" style="text-align: center; padding: 60px 20px; max-width: 560px; margin: 40px auto;">
          <div style="font-size: 54px; margin-bottom: 16px;">🔒</div>
          <h3 style="color: var(--color-primary); margin-bottom: 8px; font-size: 22px;">Passenger Sign-In Required</h3>
          <p style="color: var(--color-text-muted); font-size: 14px; line-height: 1.6; margin-bottom: 24px;">
            Sign in to view your confirmed E-Tickets, monitor your flight waitlist priority, and access your 1-Year Travel Credit wallet.
          </p>
          <button class="btn-primary-full" style="max-width: 240px; margin: 0 auto;" onclick="AuthModule.openLoginModal()">Login to Dashboard &rarr;</button>
        </div>
      `;
      return;
    }

    App.showView('passenger-dashboard');
    DashboardModule.renderLayout();
  },

  renderLayout() {
    const container = document.getElementById('view-passenger-dashboard');
    if (!container) return;

    const user = AuthModule.currentUser;
    const initial = (user.full_name || 'U').charAt(0).toUpperCase();
    const tier = user.loyalty_tier || 'BRONZE';

    container.innerHTML = `
      <div style="max-width: 1100px; margin: 0 auto;">
        
        <!-- Header & Profile Card -->
        <div class="card" style="margin-bottom: 24px; padding: 24px 28px; display: flex; justify-content: space-between; align-items: center; background: linear-gradient(135deg, #064E3B 0%, #065F46 100%); color: white; border-radius: var(--radius-lg); flex-wrap: wrap; gap: 16px;">
          <div style="display: flex; align-items: center; gap: 18px;">
            <div style="width: 58px; height: 58px; border-radius: 50%; background: #10B981; color: white; display: flex; align-items: center; justify-content: center; font-size: 26px; font-weight: 800; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
              ${initial}
            </div>
            <div>
              <h2 style="font-family: var(--font-heading); font-size: 22px; margin-bottom: 3px; color: white;">${user.full_name || 'Passenger'}</h2>
              <div style="font-size: 13.5px; opacity: 0.9;">
                ${user.email} &bull; Tier: <span style="background: rgba(255,255,255,0.2); color: #A7F3D0; padding: 2px 8px; border-radius: 12px; font-weight: 700; font-size: 11.5px;">${tier}</span>
              </div>
            </div>
          </div>

          <div style="text-align: right; background: rgba(255,255,255,0.1); padding: 12px 22px; border-radius: var(--radius-md); border: 1px solid rgba(255,255,255,0.18);">
            <div style="font-size: 11.5px; opacity: 0.85; text-transform: uppercase; letter-spacing: 0.5px;">Travel Credit Wallet</div>
            <div style="font-family: var(--font-heading); font-size: 26px; font-weight: 800; color: #A7F3D0;" id="dash-total-credit-val">$0</div>
            <div style="font-size: 10.5px; opacity: 0.75;">1-Year Guaranteed Validity</div>
          </div>
        </div>

        <!-- Dashboard Navigation Tabs -->
        <div class="admin-tabs-nav" style="margin-bottom: 20px;">
          <button class="admin-tab-btn ${DashboardModule.currentTab === 'bookings' ? 'active' : ''}" onclick="DashboardModule.switchTab('bookings')">
            🎫 My Bookings
          </button>
          <button class="admin-tab-btn ${DashboardModule.currentTab === 'waitlist' ? 'active' : ''}" onclick="DashboardModule.switchTab('waitlist')">
            ⏳ Flight Waitlist / Wishlist Queue
          </button>
          <button class="admin-tab-btn ${DashboardModule.currentTab === 'credits' ? 'active' : ''}" onclick="DashboardModule.switchTab('credits')">
            💳 Travel Credits Wallet
          </button>
        </div>

        <!-- Tab Content Container -->
        <div id="dash-tab-content">
          <div style="text-align: center; padding: 40px; color: var(--color-text-muted);">
            <div class="btn-spinner" style="width: 28px; height: 28px; border-width: 3px; border-top-color: var(--color-primary); margin: 0 auto 12px;"></div>
            Loading passenger records...
          </div>
        </div>

      </div>
    `;

    DashboardModule.loadTabContent();
  },

  switchTab(tab) {
    DashboardModule.currentTab = tab;
    DashboardModule.renderLayout();
  },

  async loadTabContent() {
    const content = document.getElementById('dash-tab-content');
    if (!content) return;

    try {
      if (DashboardModule.currentTab === 'bookings') {
        const bookingsData = await API.get('/bookings');
        DashboardModule.bookings = Array.isArray(bookingsData) ? bookingsData : (bookingsData.items || []);
        DashboardModule.renderBookingsTab(content);
      } else if (DashboardModule.currentTab === 'waitlist') {
        const waitlistData = await API.get('/waitlist/me');
        DashboardModule.waitlists = Array.isArray(waitlistData) ? waitlistData : (waitlistData.items || []);
        DashboardModule.renderWaitlistTab(content);
      } else if (DashboardModule.currentTab === 'credits') {
        const creditsData = await API.get('/travel-credits/me');
        DashboardModule.credits = Array.isArray(creditsData) ? creditsData : (creditsData.items || []);
        DashboardModule.renderCreditsTab(content);
      }

      // Update credit balance in banner
      const credits = await API.get('/travel-credits/me').catch(() => []);
      const cList = Array.isArray(credits) ? credits : (credits.items || []);
      const total = cList.filter(c => c.status === 'ACTIVE').reduce((sum, c) => sum + Number(c.amount || 0), 0);
      const credVal = document.getElementById('dash-total-credit-val');
      if (credVal) credVal.textContent = `$${total.toLocaleString()}`;

    } catch (e) {
      console.error(e);
    }
  },

  // 1. Bookings Tab
  renderBookingsTab(container) {
    const bookings = DashboardModule.bookings;

    if (bookings.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px 20px;">
          <div style="font-size: 44px; margin-bottom: 12px;">🎫</div>
          <h3 style="color: var(--color-primary); margin-bottom: 6px;">No Active Bookings</h3>
          <p style="color: var(--color-text-muted); font-size: 14px; max-width: 440px; margin: 0 auto 20px;">
            You haven't reserved any flights yet. Browse available flights and lock your seats in real-time.
          </p>
          <button class="btn-select-flight" style="margin: 0 auto;" onclick="App.navigate('search')">Search Flights Now &rarr;</button>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 16px;">
        ${bookings.map(b => DashboardModule.renderBookingCard(b)).join('')}
      </div>
    `;
  },

  renderBookingCard(b) {
    const isCancelled = b.status === 'CANCELLED';
    const flight = b.flight || {};

    const depDate = flight.departure_datetime ? new Date(flight.departure_datetime).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : 'Scheduled';
    const pnr = b.booking_reference || (b.id ? b.id.substring(0,8).toUpperCase() : 'PNR-FLOW');

    return `
      <div class="card" style="display: flex; justify-content: space-between; align-items: center; border-left: 5px solid ${isCancelled ? '#EF4444' : '#10B981'}; padding: 20px 24px; flex-wrap: wrap; gap: 16px;">
        <div>
          <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
            <span style="font-family: var(--font-heading); font-size: 18px; font-weight: 800; color: var(--color-primary);">
              PNR: ${pnr}
            </span>
            <span class="badge ${isCancelled ? 'badge-danger' : 'badge-success'}">
              ${b.status}
            </span>
            <span class="badge badge-primary">Seat: ${b.seat_number || '10A'} (${b.seat_class || 'ECONOMY'})</span>
          </div>

          <div style="font-size: 15px; color: var(--color-text-main); font-weight: 700; margin-top: 4px;">
            Flight ${flight.flight_number || 'PK-301'} &bull; ${flight.origin || 'KHI'} &rarr; ${flight.destination || 'ISB'}
          </div>
          
          <div style="font-size: 13px; color: var(--color-text-muted); margin-top: 4px;">
            Departure: <b>${depDate}</b> &bull; Total Paid: <b>$${b.total_price || 250} ${b.currency || 'USD'}</b>
          </div>
        </div>

        <div>
          ${!isCancelled ? `
            <button type="button" class="btn-action-reject" onclick="DashboardModule.openCancelModal('${b.id}', '${pnr}')" style="padding: 10px 18px; font-size: 13px; font-weight: 700;">
              Cancel Reservation
            </button>
          ` : `
            <div style="text-align: right;">
              <span class="badge badge-danger" style="font-size: 12px;">Cancelled</span>
              <div style="font-size: 11.5px; color: var(--color-text-muted); margin-top: 4px;">Resolution Credited</div>
            </div>
          `}
        </div>
      </div>
    `;
  },

  // 2. Waitlist / Wishlist Tab
  renderWaitlistTab(container) {
    const waitlists = DashboardModule.waitlists;

    if (waitlists.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px 20px;">
          <div style="font-size: 44px; margin-bottom: 12px;">⏳</div>
          <h3 style="color: var(--color-primary); margin-bottom: 6px;">No Active Flight Waitlists</h3>
          <p style="color: var(--color-text-muted); font-size: 14px; max-width: 480px; margin: 0 auto 20px;">
            When fully booked flights become available, passengers in the prioritized queue are automatically notified. You can join a waitlist on any fully booked flight during search.
          </p>
          <button class="btn-select-flight" style="margin: 0 auto;" onclick="App.navigate('search')">Browse Flights &rarr;</button>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="admin-table-card">
        <div style="padding: 16px 20px; border-bottom: 1px solid var(--color-border); font-weight: 700; color: var(--color-primary); display: flex; justify-content: space-between; align-items: center;">
          <span>My Prioritized Flight Waitlists (${waitlists.length})</span>
          <span class="badge badge-primary">Tier Priority Queue</span>
        </div>

        <table class="admin-table">
          <thead>
            <tr>
              <th>Waitlist ID</th>
              <th>Flight ID</th>
              <th>Cabin Class</th>
              <th>Priority Score</th>
              <th>Status</th>
              <th>Joined Date</th>
            </tr>
          </thead>
          <tbody>
            ${waitlists.map(w => `
              <tr>
                <td style="font-family: monospace; font-size: 12px;">${w.id.substring(0,8).toUpperCase()}</td>
                <td style="font-family: monospace; font-size: 12px;">${w.flight_id.substring(0,8)}...</td>
                <td><span class="badge badge-primary">${w.seat_class}</span></td>
                <td><b style="color: var(--color-primary);">${w.priority_score || 100} pts</b></td>
                <td><span class="badge ${w.status === 'OFFERED' ? 'badge-warning' : (w.status === 'CONFIRMED' ? 'badge-success' : 'badge-primary')}">${w.status}</span></td>
                <td style="font-size: 12.5px;">${new Date(w.created_at).toLocaleDateString()}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  },

  // 3. Travel Credits Wallet Tab
  renderCreditsTab(container) {
    const credits = DashboardModule.credits;

    if (credits.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 48px 20px;">
          <div style="font-size: 44px; margin-bottom: 12px;">💳</div>
          <h3 style="color: var(--color-primary); margin-bottom: 6px;">Zero Travel Credits</h3>
          <p style="color: var(--color-text-muted); font-size: 14px; max-width: 480px; margin: 0 auto 20px;">
            Travel credits issued from voluntary flight cancellations or automated airline disruption compensations are stored here with 1-year guaranteed validity.
          </p>
        </div>
      `;
      return;
    }

    container.innerHTML = `
      <div class="admin-table-card">
        <div style="padding: 16px 20px; border-bottom: 1px solid var(--color-border); font-weight: 700; color: var(--color-primary); display: flex; justify-content: space-between; align-items: center;">
          <span>Active Travel Credit Certificates (${credits.length})</span>
          <span class="badge badge-success">1-Year Expiry Protection</span>
        </div>

        <table class="admin-table">
          <thead>
            <tr>
              <th>Credit Certificate</th>
              <th>Amount Available</th>
              <th>Status</th>
              <th>Issue Date</th>
              <th>Expiry Date (1-Year)</th>
            </tr>
          </thead>
          <tbody>
            ${credits.map(c => `
              <tr>
                <td style="font-family: monospace; font-weight: 700; color: var(--color-primary);">${c.credit_code || 'CR-' + c.id.substring(0,8).toUpperCase()}</td>
                <td><b style="font-size: 15px; color: #059669;">$${c.amount} ${c.currency || 'USD'}</b></td>
                <td><span class="badge ${c.status === 'ACTIVE' ? 'badge-success' : 'badge-danger'}">${c.status}</span></td>
                <td style="font-size: 12.5px;">${new Date(c.created_at).toLocaleDateString()}</td>
                <td style="font-size: 12.5px; font-weight: 600;">${new Date(c.expires_at).toLocaleDateString()}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  },

  openCancelModal(bookingId, pnr) {
    const modalHtml = `
      <div class="modal-overlay active" id="modal-cancel">
        <div class="modal-card">
          <div class="modal-header">
            <h3 class="modal-title" style="color: #EF4444;">Cancel Flight (PNR: ${pnr})</h3>
            <button class="modal-close-btn" onclick="document.getElementById('modal-cancel').remove()">✕</button>
          </div>
          <div class="modal-body">
            <p style="font-size: 13.5px; color: var(--color-text-muted); margin-bottom: 16px;">
              Cancelling your booking immediately releases your physical seat and calculates refund or travel credits in compliance with fare policies.
            </p>

            <form onsubmit="DashboardModule.submitCancel(event, '${bookingId}')">
              <div class="form-group">
                <label class="form-label">Refund / Credit Preference</label>
                <select id="cancel-pref" class="form-select">
                  <option value="TRAVEL_CREDIT">1-Year Valid Travel Credit (Instant 100% Value)</option>
                  <option value="ORIGINAL_PAYMENT">Original Payment Refund (Subject to Fare Rules)</option>
                </select>
              </div>

              <div class="form-group" style="margin-top: 14px;">
                <label class="form-label">Cancellation Reason</label>
                <input type="text" id="cancel-reason" class="form-input" placeholder="e.g. Schedule change, personal reason" required />
              </div>

              <button type="submit" class="btn-primary-full" style="background:#EF4444; margin-top: 20px;">
                Confirm Cancellation & Issue Refund / Credit
              </button>
            </form>
          </div>
        </div>
      </div>
    `;

    document.getElementById('modal-cancel')?.remove();
    document.body.insertAdjacentHTML('beforeend', modalHtml);
  },

  async submitCancel(event, bookingId) {
    event.preventDefault();
    const reason = document.getElementById('cancel-reason').value.trim();
    const pref = document.getElementById('cancel-pref').value;

    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerHTML : 'Confirm Cancellation';
    if (submitBtn) {
      submitBtn.classList.add('btn-loading');
      submitBtn.innerHTML = '<span class="btn-spinner"></span> Processing Cancellation...';
    }

    try {
      await API.post(`/bookings/${bookingId}/cancel`, {
        reason: reason || 'Passenger requested cancellation',
        refund_preference: pref
      });

      document.getElementById('modal-cancel')?.remove();
      API.showToast('Booking cancelled successfully and refund/credit processed!', 'success');
      
      DashboardModule.loadTabContent();
    } catch (e) {
      console.error('Cancellation error:', e);
      API.showToast(e.message || 'Failed to cancel booking', 'error');
    } finally {
      if (submitBtn) {
        submitBtn.classList.remove('btn-loading');
        submitBtn.innerHTML = originalText;
      }
    }
  }
};
