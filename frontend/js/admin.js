/**
 * SkyFlow Admin Portal & Operations Module
 * Comprehensive Operations for all FastAPI Endpoints:
 * - GET/POST /admin/flights (List & Create flights with layout & inventory)
 * - PATCH /admin/flights/{id} (Edit schedule with impact analysis)
 * - PATCH /admin/flights/{id}/inventory (Adjust class seat allocation)
 * - POST /admin/flights/{id}/cancel (Cancel flight with downstream refund/credit resolution)
 * - GET/POST /admin/aircraft (List & Create aircraft configurations)
 * - GET/POST /admin/fare-rules (List & Create fare rules)
 * - GET /admin/audit-logs (Query immutable audit logs)
 * - GET /admin/pending-approvals (List actions pending human approval)
 * - POST /admin/audit-logs/{id}/approve & reject (Approve/reject pending audit actions)
 */
const AdminModule = {
  currentTab: 'flights',
  aircraftList: [],
  flightsList: [],

  async init() {
    // If not admin, show login prompt inside admin portal view
    if (!AuthModule.isAgentOrAdmin()) {
      App.showView('admin-portal');
      const container = document.getElementById('view-admin-portal');
      if (container) {
        container.innerHTML = `
          <div class="card" style="text-align: center; padding: 60px 20px; max-width: 540px; margin: 40px auto;">
            <div style="font-size: 54px; margin-bottom: 16px;">🛡️</div>
            <h3 style="color: var(--color-primary); margin-bottom: 8px; font-size: 22px;">Operations Portal Sign-In Required</h3>
            <p style="color: var(--color-text-muted); font-size: 14px; line-height: 1.6; margin-bottom: 24px;">
              Please login with <b>Super Admin</b> or <b>Ops Agent</b> credentials to create flights, manage aircraft configurations, and review autonomy approvals.
            </p>
            <div style="font-size: 13px; color: var(--color-text-muted); background: var(--color-accent-soft); padding: 12px; border-radius: var(--radius-sm); margin-bottom: 24px;">
              💡 <b>Super Admin Demo:</b> <code>admin@gmail.com</code> / <code>123@#$</code>
            </div>
            <button class="btn-primary-full" style="max-width: 240px; margin: 0 auto;" onclick="AuthModule.openLoginModal()">Login as Admin &rarr;</button>
          </div>
        `;
      }
      return;
    }

    App.showView('admin-portal');
    AdminModule.renderLayout();
  },

  renderLayout() {
    const container = document.getElementById('view-admin-portal');
    if (!container) return;

    const userRole = (typeof AuthModule.getRoleName === 'function' ? AuthModule.getRoleName() : '') || 'SUPER_ADMIN';

    container.innerHTML = `
      <div class="admin-dashboard-wrapper" style="max-width: 1300px; margin: 0 auto; padding: 10px 16px 50px;">
        
        <!-- Operations Header Banner -->
        <div class="card" style="background: linear-gradient(135deg, #064E3B 0%, #065F46 100%); color: white; margin-bottom: 24px; padding: 24px 28px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; border-radius: var(--radius-lg); box-shadow: 0 10px 25px rgba(6, 78, 59, 0.2);">
          <div>
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
              <span style="font-size: 22px;">🛡️</span>
              <h2 style="font-family: var(--font-heading); font-size: 24px; font-weight: 800; color: white; margin: 0;">Aviation Operations Control Center</h2>
              <span class="badge" style="background: rgba(255,255,255,0.22); color: #A7F3D0; font-weight: 700;">${userRole}</span>
            </div>
            <p style="font-size: 13.5px; opacity: 0.92; margin: 4px 0 0;">
              Full-featured administrative panel for Flight Scheduling, Inventory Reallocation, Aircraft Fleet, Fare Policies, and Safety Approvals.
            </p>
          </div>
          <div style="display: flex; gap: 10px;">
            <button type="button" class="btn-select-flight" style="background: #10B981; border: none; padding: 10px 18px; font-size: 13px; font-weight: 700; border-radius: var(--radius-full);" onclick="AdminModule.loadTabContent()">
              🔄 Refresh Data
            </button>
          </div>
        </div>

        <!-- Operations Navigation Tabs -->
        <div class="admin-tabs-nav" style="margin-bottom: 24px;">
          <button class="admin-tab-btn ${AdminModule.currentTab === 'flights' ? 'active' : ''}" onclick="AdminModule.switchTab('flights')">
            ✈️ Flight Manager
          </button>
          <button class="admin-tab-btn ${AdminModule.currentTab === 'aircraft' ? 'active' : ''}" onclick="AdminModule.switchTab('aircraft')">
            🛫 Aircraft Fleet Config
          </button>
          <button class="admin-tab-btn ${AdminModule.currentTab === 'fare-rules' ? 'active' : ''}" onclick="AdminModule.switchTab('fare-rules')">
            📜 Fare Rules Engine
          </button>
          <button class="admin-tab-btn ${AdminModule.currentTab === 'approvals' ? 'active' : ''}" onclick="AdminModule.switchTab('approvals')">
            🛡️ Autonomy Approvals
          </button>
          <button class="admin-tab-btn ${AdminModule.currentTab === 'audit-logs' ? 'active' : ''}" onclick="AdminModule.switchTab('audit-logs')">
            📋 System Audit Logs
          </button>
          <button class="admin-tab-btn ${AdminModule.currentTab === 'refunds' ? 'active' : ''}" onclick="AdminModule.switchTab('refunds')">
            💰 System Refunds
          </button>
        </div>

        <!-- Tab Content View Container -->
        <div id="admin-tab-content">
          <div style="text-align: center; padding: 50px; color: var(--color-text-muted);">
            <div class="btn-spinner" style="width: 32px; height: 32px; border-width: 3px; border-top-color: var(--color-primary); margin: 0 auto 14px;"></div>
            Loading operations data from server...
          </div>
        </div>

      </div>
    `;

    AdminModule.loadTabContent();
  },

  switchTab(tab) {
    AdminModule.currentTab = tab;
    AdminModule.renderLayout();
  },

  async loadTabContent() {
    const content = document.getElementById('admin-tab-content');
    if (!content) return;

    if (AdminModule.currentTab === 'flights') {
      await AdminModule.renderFlightManager(content);
    } else if (AdminModule.currentTab === 'aircraft') {
      await AdminModule.renderAircraftManager(content);
    } else if (AdminModule.currentTab === 'fare-rules') {
      await AdminModule.renderFareRulesManager(content);
    } else if (AdminModule.currentTab === 'approvals') {
      await AdminModule.renderApprovalsPanel(content);
    } else if (AdminModule.currentTab === 'audit-logs') {
      await AdminModule.renderAuditLogsPanel(content);
    } else if (AdminModule.currentTab === 'refunds') {
      await AdminModule.renderRefundsPanel(content);
    }
  },

  // ==========================================
  // 1. FLIGHT MANAGER
  // ==========================================
  async renderFlightManager(container) {
    try {
      const [aircraftData, flightsData] = await Promise.all([
        API.get('/admin/aircraft').catch(() => []),
        API.get('/admin/flights').catch(() => [])
      ]);

      AdminModule.aircraftList = Array.isArray(aircraftData) ? aircraftData : (aircraftData.items || []);
      AdminModule.flightsList = Array.isArray(flightsData) ? flightsData : (flightsData.items || []);
    } catch (e) {
      console.error(e);
    }

    const defaultDep = new Date(Date.now() + 24 * 3600 * 1000).toISOString().slice(0, 16);
    const defaultArr = new Date(Date.now() + 26 * 3600 * 1000).toISOString().slice(0, 16);

    container.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1.6fr; gap: 24px;" class="admin-grid-layout">
        
        <!-- Create Flight Form Card -->
        <div class="card">
          <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
            <h3 style="font-family: var(--font-heading); font-size: 18px; color: var(--color-primary); margin: 0;">
              ✈️ Create Scheduled Flight
            </h3>
            <span class="badge badge-success">Atomic Generation</span>
          </div>

          <form onsubmit="AdminModule.handleCreateFlight(event)">
            
            <div class="form-group">
              <label class="form-label">Flight Number</label>
              <input type="text" id="adm-flight-no" class="form-input" placeholder="e.g. PK-301, EK-202, QR-610" required />
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
              <div class="form-group">
                <label class="form-label">Origin (IATA / City)</label>
                <input type="text" id="adm-origin" class="form-input" placeholder="e.g. KHI" required />
              </div>
              <div class="form-group">
                <label class="form-label">Destination (IATA / City)</label>
                <input type="text" id="adm-dest" class="form-input" placeholder="e.g. ISB" required />
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
              <div class="form-group">
                <label class="form-label">Departure (UTC)</label>
                <input type="datetime-local" id="adm-dep-time" class="form-input" value="${defaultDep}" required />
              </div>
              <div class="form-group">
                <label class="form-label">Arrival (UTC)</label>
                <input type="datetime-local" id="adm-arr-time" class="form-input" value="${defaultArr}" required />
              </div>
            </div>

            <div class="form-group" style="margin-top: 10px;">
              <label class="form-label">Assigned Aircraft Fleet</label>
              <select id="adm-aircraft-select" class="form-select" onchange="AdminModule.onAircraftSelectChange(this.value)" required>
                ${AdminModule.aircraftList.length === 0 ? '<option value="">No aircraft configured yet</option>' : 
                  AdminModule.aircraftList.map(a => `
                    <option value="${a.id}" data-total="${a.total_capacity}" data-first="${a.first_seats}" data-biz="${a.business_seats}" data-eco="${a.economy_seats}">
                      ${a.model} (${a.registration_number}) — ${a.total_capacity} Seats (F:${a.first_seats} B:${a.business_seats} E:${a.economy_seats})
                    </option>
                  `).join('')}
              </select>
            </div>

            <!-- Seat Breakdown (Auto-synced with aircraft) -->
            <div style="background: var(--color-accent-soft); padding: 12px; border-radius: var(--radius-sm); margin-top: 10px;">
              <div style="display: flex; justify-content: space-between; font-size: 12.5px; font-weight: 700; color: var(--color-primary); margin-bottom: 6px;">
                <span>Cabin Class Seat Breakdown</span>
                <span id="adm-capacity-sum">Total: 100 Seats</span>
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px;">
                <div>
                  <label style="font-size: 11px; color: var(--color-text-muted);">First Class</label>
                  <input type="number" id="adm-first-seats" class="form-input" value="20" min="0" oninput="AdminModule.updateCapacitySum()" required />
                </div>
                <div>
                  <label style="font-size: 11px; color: var(--color-text-muted);">Business</label>
                  <input type="number" id="adm-biz-seats" class="form-input" value="30" min="0" oninput="AdminModule.updateCapacitySum()" required />
                </div>
                <div>
                  <label style="font-size: 11px; color: var(--color-text-muted);">Economy</label>
                  <input type="number" id="adm-eco-seats" class="form-input" value="50" min="0" oninput="AdminModule.updateCapacitySum()" required />
                </div>
              </div>
            </div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
              <div class="form-group">
                <label class="form-label" id="adm-price-label">Base Price ($ USD)</label>
                <input type="number" id="adm-price" class="form-input" value="250" min="1" required />
              </div>
              <div class="form-group">
                <label class="form-label">Currency</label>
                <select id="adm-curr" class="form-select" onchange="AdminModule.onCurrencyChange(this.value)">
                  <option value="USD" selected>USD ($ - US Dollar)</option>
                  <option value="PKR">PKR (Rs - Pakistani Rupee)</option>
                  <option value="AED">AED (AED - UAE Dirham)</option>
                  <option value="SAR">SAR (SAR - Saudi Riyal)</option>
                  <option value="EUR">EUR (€ - Euro)</option>
                  <option value="GBP">GBP (£ - British Pound)</option>
                  <option value="CAD">CAD (CA$ - Canadian Dollar)</option>
                  <option value="INR">INR (₹ - Indian Rupee)</option>
                  <option value="AUD">AUD (AU$ - Australian Dollar)</option>
                  <option value="JPY">JPY (¥ - Japanese Yen)</option>
                </select>
              </div>
            </div>

            <button type="submit" id="btn-create-flight" class="btn-primary-full" style="margin-top: 18px;">
              + Create & Publish Flight Schedule
            </button>
          </form>
        </div>

        <!-- Master Flights Table -->
        <div class="admin-table-card">
          <div style="padding: 16px 20px; border-bottom: 1px solid var(--color-border); display: flex; justify-content: space-between; align-items: center;">
            <div>
              <span style="font-weight: 800; color: var(--color-primary); font-size: 16px;">Scheduled Flights</span>
              <span class="badge badge-primary" style="margin-left: 8px;">${AdminModule.flightsList.length} Total</span>
            </div>
            <span style="font-size: 12px; color: var(--color-text-muted);">Live Physical & Class Allocations</span>
          </div>

          <div style="overflow-x: auto; max-height: 640px;">
            ${AdminModule.flightsList.length === 0 ? `
              <div style="padding: 48px 20px; text-align: center; color: var(--color-text-muted);">
                <div style="font-size: 40px; margin-bottom: 10px;">🛫</div>
                <h4 style="color: var(--color-primary);">No Flights in Schedule</h4>
                <p style="font-size: 13.5px; margin-bottom: 16px;">Create your first flight schedule using the form on the left.</p>
              </div>
            ` : `
              <table class="admin-table">
                <thead>
                  <tr>
                    <th>Flight</th>
                    <th>Route</th>
                    <th>Departure / Arrival (UTC)</th>
                    <th>Class Seats (Avail/Total)</th>
                    <th>Status</th>
                    <th>Base Price</th>
                    <th>Operations Actions</th>
                  </tr>
                </thead>
                <tbody>
                  ${AdminModule.flightsList.map(f => {
                    const depStr = new Date(f.departure_datetime).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                    const arrStr = new Date(f.arrival_datetime).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                    
                    const isCancelled = f.status === 'CANCELLED';
                    const isDelayed = f.status === 'DELAYED';
                    const badgeClass = isCancelled ? 'badge-danger' : (isDelayed ? 'badge-warning' : 'badge-success');

                    const fAvail = f.available_first ?? (f.first_seats - f.booked_first);
                    const bAvail = f.available_business ?? (f.business_seats - f.booked_business);
                    const eAvail = f.available_economy ?? (f.economy_seats - f.booked_economy);

                    return `
                      <tr>
                        <td>
                          <div style="font-weight: 800; color: var(--color-primary);">${f.flight_number}</div>
                          <div style="font-size: 11px; color: var(--color-text-muted);">${f.aircraft?.model || 'Boeing 777'}</div>
                        </td>
                        <td>
                          <b>${f.origin}</b> &rarr; <b>${f.destination}</b>
                        </td>
                        <td>
                          <div style="font-size: 12.5px; font-weight: 600;">🛫 ${depStr}</div>
                          <div style="font-size: 12px; color: var(--color-text-muted);">🛬 ${arrStr}</div>
                        </td>
                        <td>
                          <div style="font-size: 12px; line-height: 1.4;">
                            <span style="color:#059669; font-weight:700;">F:</span> ${fAvail}/${f.first_seats} &bull; 
                            <span style="color:#2563EB; font-weight:700;">B:</span> ${bAvail}/${f.business_seats} &bull; 
                            <span style="color:#D97706; font-weight:700;">E:</span> ${eAvail}/${f.economy_seats}
                          </div>
                          <div style="font-size: 11px; color: var(--color-text-muted); margin-top: 2px;">
                            Total Capacity: <b>${f.capacity} Seats</b>
                          </div>
                        </td>
                        <td>
                          <span class="badge ${badgeClass}">${f.status}</span>
                        </td>
                        <td>
                          <b>$${f.base_price}</b>
                        </td>
                        <td>
                          <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                            <button type="button" class="btn-price-hold" style="padding: 5px 10px; font-size: 11.5px;" onclick="AdminModule.openScheduleEditModal('${f.id}', '${f.flight_number}')" title="Shift flight schedule and trigger cascade alerts">
                              🕒 Shift
                            </button>
                            <button type="button" class="btn-price-hold" style="padding: 5px 10px; font-size: 11.5px; background: #EEF2FF; color: #4338CA; border-color: #C7D2FE;" onclick="AdminModule.openInventoryAdjustModal('${f.id}', '${f.flight_number}', ${f.first_seats}, ${f.business_seats}, ${f.economy_seats}, ${f.booked_first || 0}, ${f.booked_business || 0}, ${f.booked_economy || 0})" title="Adjust First, Business, Economy allocations">
                              📊 Inventory
                            </button>
                            ${!isCancelled ? `
                              <button type="button" class="btn-action-reject" style="padding: 5px 10px; font-size: 11.5px; margin: 0;" onclick="AdminModule.openCancelFlightModal('${f.id}', '${f.flight_number}')" title="Cancel flight with automated passenger refund or credit resolution">
                                ❌ Cancel
                              </button>
                            ` : `
                              <span style="font-size: 11px; color: var(--color-danger); font-weight: 700;">Cancelled</span>
                            `}
                          </div>
                        </td>
                      </tr>
                    `;
                  }).join('')}
                </tbody>
              </table>
            `}
          </div>
        </div>

      </div>
    `;

    // Initialize first aircraft selection
    if (AdminModule.aircraftList.length > 0) {
      AdminModule.onAircraftSelectChange(AdminModule.aircraftList[0].id);
    }
  },

  onAircraftSelectChange(aircraftId) {
    const aircraft = AdminModule.aircraftList.find(a => a.id === aircraftId);
    if (!aircraft) return;

    const fInput = document.getElementById('adm-first-seats');
    const bInput = document.getElementById('adm-biz-seats');
    const eInput = document.getElementById('adm-eco-seats');

    if (fInput) fInput.value = aircraft.first_seats;
    if (bInput) bInput.value = aircraft.business_seats;
    if (eInput) eInput.value = aircraft.economy_seats;

    AdminModule.updateCapacitySum();
  },

  updateCapacitySum() {
    const f = Number(document.getElementById('adm-first-seats')?.value || 0);
    const b = Number(document.getElementById('adm-biz-seats')?.value || 0);
    const e = Number(document.getElementById('adm-eco-seats')?.value || 0);
    const total = f + b + e;

    const sumEl = document.getElementById('adm-capacity-sum');
    if (sumEl) sumEl.textContent = `Total: ${total} Seats`;
  },

  lastCurrency: 'USD',

  onCurrencyChange(newCurrency) {
    const priceInput = document.getElementById('adm-price');
    const label = document.getElementById('adm-price-label');
    if (!priceInput) return;

    const oldCurrency = AdminModule.lastCurrency || 'USD';
    const oldPrice = Number(priceInput.value) || 0;
    
    // Convert old price to USD base, then to new currency
    const oldRate = (CONFIG.EXCHANGE_RATES && CONFIG.EXCHANGE_RATES[oldCurrency]) || 1;
    const newRate = (CONFIG.EXCHANGE_RATES && CONFIG.EXCHANGE_RATES[newCurrency]) || 1;
    const priceInUSD = oldPrice / oldRate;
    const converted = Math.round(priceInUSD * newRate);

    priceInput.value = converted;
    AdminModule.lastCurrency = newCurrency;
    
    if (label) {
      const sym = (CONFIG.CURRENCY_SYMBOLS && CONFIG.CURRENCY_SYMBOLS[newCurrency]) || '';
      label.innerHTML = `Base Price (${sym} ${newCurrency})`;
    }
  },

  async handleCreateFlight(event) {
    event.preventDefault();
    const btn = document.getElementById('btn-create-flight');
    const origHtml = btn ? btn.innerHTML : 'Create Flight';

    const flight_number = document.getElementById('adm-flight-no').value.trim().toUpperCase();
    const origin = document.getElementById('adm-origin').value.trim().toUpperCase();
    const destination = document.getElementById('adm-dest').value.trim().toUpperCase();
    const departure_datetime = new Date(document.getElementById('adm-dep-time').value).toISOString();
    const arrival_datetime = new Date(document.getElementById('adm-arr-time').value).toISOString();
    const aircraft_id = document.getElementById('adm-aircraft-select').value;
    
    const first_seats = Number(document.getElementById('adm-first-seats').value);
    const business_seats = Number(document.getElementById('adm-biz-seats').value);
    const economy_seats = Number(document.getElementById('adm-eco-seats').value);
    const capacity = first_seats + business_seats + economy_seats;

    const base_price = Number(document.getElementById('adm-price').value);
    const currency = (document.getElementById('adm-curr')?.value || 'USD').toUpperCase();

    if (capacity <= 0) {
      API.showToast('Total capacity must be greater than 0.', 'warning');
      return;
    }

    try {
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="btn-spinner"></span> Generating Seats & Publishing...';
      }

      await API.post('/admin/flights', {
        flight_number,
        origin,
        destination,
        departure_datetime,
        arrival_datetime,
        capacity,
        first_seats,
        business_seats,
        economy_seats,
        base_price,
        currency,
        aircraft_id,
        overbooking_policy: 'HARD_LIMIT',
        first_cutoff_hours: 2,
        business_cutoff_hours: 2,
        economy_cutoff_hours: 1
      });

      API.showToast(`Flight ${flight_number} scheduled and physical seat map generated!`, 'success');
      await AdminModule.loadTabContent();
    } catch (e) {
      // Handled
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = origHtml;
      }
    }
  },

  // Modal: Shift Schedule
  openScheduleEditModal(flightId, flightNo) {
    const defaultDep = new Date(Date.now() + 25 * 3600 * 1000).toISOString().slice(0, 16);
    const defaultArr = new Date(Date.now() + 27 * 3600 * 1000).toISOString().slice(0, 16);

    const modalHtml = `
      <div class="modal-overlay active" id="modal-edit-schedule">
        <div class="modal-card">
          <div class="modal-header">
            <h3 class="modal-title">Shift Flight Schedule — ${flightNo}</h3>
            <button class="modal-close-btn" onclick="document.getElementById('modal-edit-schedule').remove()">✕</button>
          </div>
          <div class="modal-body">
            <p style="font-size: 13.5px; color: var(--color-text-muted); margin-bottom: 16px;">
              Shifting schedule will trigger <b>cascading email alerts</b> to all confirmed passengers. Shifts exceeding 2 hours trigger automatic rebooking workflows.
            </p>

            <form onsubmit="AdminModule.submitScheduleShift(event, '${flightId}')">
              <div class="form-group">
                <label class="form-label">New Departure Datetime (UTC)</label>
                <input type="datetime-local" id="shift-dep" class="form-input" value="${defaultDep}" required />
              </div>
              <div class="form-group" style="margin-top: 12px;">
                <label class="form-label">New Arrival Datetime (UTC)</label>
                <input type="datetime-local" id="shift-arr" class="form-input" value="${defaultArr}" required />
              </div>

              <button type="submit" class="btn-primary-full" style="margin-top: 20px;">
                Apply Schedule Shift & Notify Passengers
              </button>
            </form>
          </div>
        </div>
      </div>
    `;

    document.getElementById('modal-edit-schedule')?.remove();
    document.body.insertAdjacentHTML('beforeend', modalHtml);
  },

  async submitScheduleShift(event, flightId) {
    event.preventDefault();
    const departure_datetime = new Date(document.getElementById('shift-dep').value).toISOString();
    const arrival_datetime = new Date(document.getElementById('shift-arr').value).toISOString();

    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerHTML : 'Apply Schedule Shift';
    if (submitBtn) {
      submitBtn.classList.add('btn-loading');
      submitBtn.innerHTML = '<span class="btn-spinner"></span> Shifting Schedule & Alerting...';
    }

    try {
      await API.patch(`/admin/flights/${flightId}`, {
        departure_datetime,
        arrival_datetime
      });

      document.getElementById('modal-edit-schedule')?.remove();
      API.showToast('Schedule updated & cascade passenger alerts sent!', 'success');
      AdminModule.loadTabContent();
    } catch (e) {
      console.error('Schedule shift error:', e);
      API.showToast(e.message || 'Failed to shift schedule', 'error');
    } finally {
      if (submitBtn) {
        submitBtn.classList.remove('btn-loading');
        submitBtn.innerHTML = originalText;
      }
    }
  },

  // Modal: Adjust Inventory
  openInventoryAdjustModal(flightId, flightNo, first, biz, eco, bookedF, bookedB, bookedE) {
    const modalHtml = `
      <div class="modal-overlay active" id="modal-adjust-inventory">
        <div class="modal-card">
          <div class="modal-header">
            <h3 class="modal-title">Adjust Class Capacity — ${flightNo}</h3>
            <button class="modal-close-btn" onclick="document.getElementById('modal-adjust-inventory').remove()">✕</button>
          </div>
          <div class="modal-body">
            <p style="font-size: 13.5px; color: var(--color-text-muted); margin-bottom: 16px;">
              Reallocate seat inventory across cabin classes. Capacity cannot be reduced below already confirmed passenger counts.
            </p>

            <div style="background: var(--color-accent-soft); padding: 12px; border-radius: var(--radius-sm); margin-bottom: 16px; font-size: 12.5px;">
              <b>Currently Booked:</b> First: ${bookedF} | Business: ${bookedB} | Economy: ${bookedE}
            </div>

            <form onsubmit="AdminModule.submitInventoryAdjust(event, '${flightId}')">
              <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px;">
                <div class="form-group">
                  <label class="form-label">First Class</label>
                  <input type="number" id="adj-first" class="form-input" value="${first}" min="${bookedF}" required />
                </div>
                <div class="form-group">
                  <label class="form-label">Business</label>
                  <input type="number" id="adj-biz" class="form-input" value="${biz}" min="${bookedB}" required />
                </div>
                <div class="form-group">
                  <label class="form-label">Economy</label>
                  <input type="number" id="adj-eco" class="form-input" value="${eco}" min="${bookedE}" required />
                </div>
              </div>

              <button type="submit" class="btn-primary-full" style="margin-top: 20px;">
                Save Safe Inventory Allocation
              </button>
            </form>
          </div>
        </div>
      </div>
    `;

    document.getElementById('modal-adjust-inventory')?.remove();
    document.body.insertAdjacentHTML('beforeend', modalHtml);
  },

  async submitInventoryAdjust(event, flightId) {
    event.preventDefault();
    const first_seats = Number(document.getElementById('adj-first').value);
    const business_seats = Number(document.getElementById('adj-biz').value);
    const economy_seats = Number(document.getElementById('adj-eco').value);

    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerHTML : 'Save Allocation';
    if (submitBtn) {
      submitBtn.classList.add('btn-loading');
      submitBtn.innerHTML = '<span class="btn-spinner"></span> Adjusting Capacity...';
    }

    try {
      await API.patch(`/admin/flights/${flightId}/inventory`, {
        first_seats,
        business_seats,
        economy_seats
      });

      document.getElementById('modal-adjust-inventory')?.remove();
      API.showToast('Class capacity safely adjusted!', 'success');
      AdminModule.loadTabContent();
    } catch (e) {
      console.error('Inventory adjust error:', e);
      API.showToast(e.message || 'Failed to adjust inventory', 'error');
    } finally {
      if (submitBtn) {
        submitBtn.classList.remove('btn-loading');
        submitBtn.innerHTML = originalText;
      }
    }
  },

  // Modal: Cancel Flight
  openCancelFlightModal(flightId, flightNo) {
    const modalHtml = `
      <div class="modal-overlay active" id="modal-cancel-flight">
        <div class="modal-card">
          <div class="modal-header">
            <h3 class="modal-title" style="color: #EF4444;">Cancel Flight Schedule — ${flightNo}</h3>
            <button class="modal-close-btn" onclick="document.getElementById('modal-cancel-flight').remove()">✕</button>
          </div>
          <div class="modal-body">
            <p style="font-size: 13.5px; color: var(--color-text-muted); margin-bottom: 16px;">
              Cancelling a flight automatically marks the flight as CANCELLED, preserves all passenger booking records, and initiates downstream resolution for all booked travelers.
            </p>

            <form onsubmit="AdminModule.submitCancelFlight(event, '${flightId}')">
              <div class="form-group">
                <label class="form-label">Downstream Compensation Resolution</label>
                <select id="adm-cancel-res" class="form-select">
                  <option value="TRAVEL_CREDIT">Issue 1-Year Travel Credit (100% Value)</option>
                  <option value="FULL_REFUND">Full Refund to Original Payment Source</option>
                </select>
              </div>

              <div class="form-group" style="margin-top: 14px;">
                <label class="form-label">Operational Cancellation Reason</label>
                <input type="text" id="adm-cancel-reason" class="form-input" placeholder="e.g. Severe Weather, Technical Maintenance" required />
              </div>

              <button type="submit" class="btn-primary-full" style="background: #EF4444; margin-top: 20px;">
                Confirm Flight Cancellation & Compensate Passengers
              </button>
            </form>
          </div>
        </div>
      </div>
    `;

    document.getElementById('modal-cancel-flight')?.remove();
    document.body.insertAdjacentHTML('beforeend', modalHtml);
  },

  async submitCancelFlight(event, flightId) {
    event.preventDefault();
    const reason = document.getElementById('adm-cancel-reason').value.trim();
    const default_resolution = document.getElementById('adm-cancel-res').value;

    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerHTML : 'Confirm Flight Cancellation';
    if (submitBtn) {
      submitBtn.classList.add('btn-loading');
      submitBtn.innerHTML = '<span class="btn-spinner"></span> Cancelling & Notifying Passengers...';
    }

    try {
      const res = await API.post(`/admin/flights/${flightId}/cancel`, {
        reason,
        default_resolution
      });

      document.getElementById('modal-cancel-flight')?.remove();
      API.showToast(res.message || 'Flight cancelled successfully and resolutions queued.', 'success');
      AdminModule.loadTabContent();
    } catch (e) {
      console.error('Cancel flight error:', e);
      API.showToast(e.message || 'Failed to cancel flight', 'error');
    } finally {
      if (submitBtn) {
        submitBtn.classList.remove('btn-loading');
        submitBtn.innerHTML = originalText;
      }
    }
  },

  // ==========================================
  // 2. AIRCRAFT FLEET MANAGER
  // ==========================================
  async renderAircraftManager(container) {
    try {
      const aircraft = await API.get('/admin/aircraft').catch(() => []);
      const aList = Array.isArray(aircraft) ? aircraft : (aircraft.items || []);

      container.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1.5fr; gap: 24px;" class="admin-grid-layout">
          
          <!-- Create Aircraft Form -->
          <div class="card">
            <h3 style="font-family: var(--font-heading); font-size: 18px; color: var(--color-primary); margin-bottom: 16px;">
              🛫 Add Aircraft to Fleet
            </h3>
            <form onsubmit="AdminModule.handleCreateAircraft(event)">
              <div class="form-group">
                <label class="form-label">Aircraft Model</label>
                <input type="text" id="air-model" class="form-input" placeholder="e.g. Boeing 777-300ER, Airbus A350" required />
              </div>
              <div class="form-group" style="margin-top: 12px;">
                <label class="form-label">Tail / Registration Number</label>
                <input type="text" id="air-reg" class="form-input" placeholder="e.g. AP-BLD, PK-777" required />
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 12px;">
                <div class="form-group">
                  <label class="form-label">First Class</label>
                  <input type="number" id="air-first" class="form-input" value="20" min="0" required />
                </div>
                <div class="form-group">
                  <label class="form-label">Business</label>
                  <input type="number" id="air-biz" class="form-input" value="30" min="0" required />
                </div>
                <div class="form-group">
                  <label class="form-label">Economy</label>
                  <input type="number" id="air-eco" class="form-input" value="50" min="0" required />
                </div>
              </div>

              <button type="submit" id="btn-create-aircraft" class="btn-primary-full" style="margin-top: 20px;">
                + Save Aircraft Configuration
              </button>
            </form>
          </div>

          <!-- Existing Fleet List -->
          <div class="admin-table-card">
            <div style="padding: 16px 20px; border-bottom: 1px solid var(--color-border); font-weight: 700; color: var(--color-primary);">
              Active Aircraft Fleet (${aList.length})
            </div>
            
            ${aList.length === 0 ? `
              <p style="padding: 30px; text-align: center; color: var(--color-text-muted);">No aircraft configured yet.</p>
            ` : `
              <table class="admin-table">
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Tail #</th>
                    <th>Class Layout</th>
                    <th>Total Capacity</th>
                  </tr>
                </thead>
                <tbody>
                  ${aList.map(a => `
                    <tr>
                      <td><b>${a.model}</b></td>
                      <td><span class="badge badge-primary">${a.registration_number}</span></td>
                      <td>F: <b>${a.first_seats}</b> | B: <b>${a.business_seats}</b> | E: <b>${a.economy_seats}</b></td>
                      <td><b>${a.total_capacity} Seats</b></td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            `}
          </div>

        </div>
      `;
    } catch (e) {
      console.error(e);
    }
  },

  async handleCreateAircraft(event) {
    event.preventDefault();
    const btn = document.getElementById('btn-create-aircraft') || event.target.querySelector('button[type="submit"]');
    const originalText = btn ? btn.innerHTML : '+ Save Aircraft Configuration';
    if (btn) {
      btn.classList.add('btn-loading');
      btn.innerHTML = '<span class="btn-spinner"></span> Saving Fleet Record...';
    }

    const model = document.getElementById('air-model').value.trim();
    const registration_number = document.getElementById('air-reg').value.trim().toUpperCase();
    const first_seats = Number(document.getElementById('air-first').value);
    const business_seats = Number(document.getElementById('air-biz').value);
    const economy_seats = Number(document.getElementById('air-eco').value);

    try {
      await API.post('/admin/aircraft', {
        model,
        registration_number,
        total_capacity: first_seats + business_seats + economy_seats,
        first_seats,
        business_seats,
        economy_seats
      });

      API.showToast('Aircraft added to fleet successfully!', 'success');
      AdminModule.loadTabContent();
    } catch (e) {
      console.error('Create aircraft error:', e);
      API.showToast(e.message || 'Failed to create aircraft', 'error');
    } finally {
      if (btn) {
        btn.classList.remove('btn-loading');
        btn.innerHTML = originalText;
      }
    }
  },

  // ==========================================
  // 3. FARE RULES ENGINE
  // ==========================================
  async renderFareRulesManager(container) {
    try {
      const rules = await API.get('/admin/fare-rules').catch(() => []);
      const rList = Array.isArray(rules) ? rules : (rules.items || []);

      container.innerHTML = `
        <div style="display: grid; grid-template-columns: 1fr 1.6fr; gap: 24px;" class="admin-grid-layout">
          
          <!-- Create Fare Rule -->
          <div class="card">
            <h3 style="font-family: var(--font-heading); font-size: 18px; color: var(--color-primary); margin-bottom: 16px;">
              📜 Define Fare Cancellation Rule
            </h3>
            <form onsubmit="AdminModule.handleCreateFareRule(event)">
              <div class="form-group">
                <label class="form-label">Rule Name</label>
                <input type="text" id="fare-name" class="form-input" placeholder="e.g. Economy Flex Policy, First Non-Refundable" required />
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                <div class="form-group">
                  <label class="form-label">Cabin Class</label>
                  <select id="fare-class" class="form-select">
                    <option value="ECONOMY">Economy Class</option>
                    <option value="BUSINESS">Business Class</option>
                    <option value="FIRST">First Class</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">Refund Type</label>
                  <select id="fare-refund-type" class="form-select">
                    <option value="FULL">100% Full Refund</option>
                    <option value="PARTIAL">Partial Refund</option>
                    <option value="NON_REFUNDABLE">Non-Refundable</option>
                  </select>
                </div>
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px;">
                <div class="form-group">
                  <label class="form-label">Penalty Fee (%)</label>
                  <input type="number" id="fare-penalty" class="form-input" value="10" min="0" max="100" required />
                </div>
                <div class="form-group">
                  <label class="form-label">Min Cutoff (Hours)</label>
                  <input type="number" id="fare-hours" class="form-input" value="24" min="0" required />
                </div>
              </div>

              <div style="margin-top: 14px; display: flex; align-items: center; gap: 8px;">
                <input type="checkbox" id="fare-credit" checked style="width:16px; height:16px; accent-color:var(--color-primary);" />
                <label for="fare-credit" style="font-size: 13px; font-weight: 600; color: var(--color-text-muted);">
                  Permit 1-Year Valid Travel Credit conversion
                </label>
              </div>

              <button type="submit" id="btn-create-fare" class="btn-primary-full" style="margin-top: 20px;">
                + Save Fare Rule Policy
              </button>
            </form>
          </div>

          <!-- Fare Rules Table -->
          <div class="admin-table-card">
            <div style="padding: 16px 20px; border-bottom: 1px solid var(--color-border); font-weight: 700; color: var(--color-primary);">
              Active Fare Rules & Policies (${rList.length})
            </div>
            
            ${rList.length === 0 ? `
              <p style="padding: 30px; text-align: center; color: var(--color-text-muted);">No fare rules configured yet.</p>
            ` : `
              <table class="admin-table">
                <thead>
                  <tr>
                    <th>Rule Name</th>
                    <th>Class</th>
                    <th>Refund Type</th>
                    <th>Penalty</th>
                    <th>Min Cutoff</th>
                    <th>Credits Allowed</th>
                  </tr>
                </thead>
                <tbody>
                  ${rList.map(r => `
                    <tr>
                      <td><b>${r.name}</b></td>
                      <td><span class="badge badge-primary">${r.seat_class}</span></td>
                      <td><b>${r.refund_type}</b></td>
                      <td>${r.penalty_percentage}%</td>
                      <td>${r.min_hours_before_departure} hrs</td>
                      <td>${r.allow_travel_credit ? '✅ Yes' : '❌ No'}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            `}
          </div>

        </div>
      `;
    } catch (e) {
      console.error(e);
    }
  },

  async handleCreateFareRule(event) {
    event.preventDefault();
    const btn = document.getElementById('btn-create-fare') || event.target.querySelector('button[type="submit"]');
    const originalText = btn ? btn.innerHTML : '+ Save Fare Rule Policy';
    if (btn) {
      btn.classList.add('btn-loading');
      btn.innerHTML = '<span class="btn-spinner"></span> Saving Policy...';
    }

    const name = document.getElementById('fare-name').value.trim();
    const seat_class = document.getElementById('fare-class').value;
    const refund_type = document.getElementById('fare-refund-type').value;
    const penalty_percentage = Number(document.getElementById('fare-penalty').value);
    const min_hours_before_departure = Number(document.getElementById('fare-hours').value);
    const allow_travel_credit = document.getElementById('fare-credit').checked;

    try {
      await API.post('/admin/fare-rules', {
        name,
        seat_class,
        refund_type,
        penalty_percentage,
        min_hours_before_departure,
        allow_travel_credit
      });

      API.showToast('Fare rule created successfully!', 'success');
      AdminModule.loadTabContent();
    } catch (e) {
      console.error('Create fare rule error:', e);
      API.showToast(e.message || 'Failed to create fare rule', 'error');
    } finally {
      if (btn) {
        btn.classList.remove('btn-loading');
        btn.innerHTML = originalText;
      }
    }
  },

  // ==========================================
  // 4. AUTONOMY APPROVALS
  // ==========================================
  async renderApprovalsPanel(container) {
    try {
      const pendingData = await API.get('/admin/pending-approvals').catch(() => []);
      const items = Array.isArray(pendingData) ? pendingData : (pendingData.items || []);

      container.innerHTML = `
        <div class="admin-table-card">
          <div style="padding: 18px 20px; border-bottom: 1px solid var(--color-border); font-weight: 700; color: var(--color-primary); display: flex; justify-content: space-between; align-items: center;">
            <span>Human-in-the-Loop Autonomy Approvals (Super Admin Only)</span>
            <span class="badge badge-warning">${items.length} Pending</span>
          </div>
          
          ${items.length === 0 ? `
            <div style="padding: 50px 20px; text-align: center; color: var(--color-text-muted);">
              <div style="font-size: 36px; margin-bottom: 8px;">✅</div>
              <h4 style="color: var(--color-primary); margin-bottom: 4px;">Zero Pending Approvals</h4>
              <p style="font-size: 13.5px;">All high-impact system mutations have been reviewed or auto-resolved.</p>
            </div>
          ` : `
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Action</th>
                  <th>Entity Target</th>
                  <th>Status</th>
                  <th>Timestamp (UTC)</th>
                  <th>Decisions</th>
                </tr>
              </thead>
              <tbody>
                ${items.map(log => `
                  <tr>
                    <td><b>${log.action}</b></td>
                    <td>${log.entity_type} <span style="font-family:monospace; font-size:11.5px;">(${log.entity_id})</span></td>
                    <td><span class="badge badge-warning">${log.approval_status}</span></td>
                    <td>${new Date(log.timestamp).toLocaleString()}</td>
                    <td>
                      <button class="btn-action-approve" onclick="AdminModule.approveAction('${log.id}', this)">Approve</button>
                      <button class="btn-action-reject" onclick="AdminModule.rejectAction('${log.id}', this)">Reject</button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          `}
        </div>
      `;
    } catch (e) {
      console.error(e);
    }
  },

  async approveAction(logId, btnEl) {
    if (btnEl) {
      btnEl.classList.add('btn-loading');
      btnEl.innerHTML = '<span class="btn-spinner"></span> Approving...';
    }
    try {
      await API.post(`/admin/audit-logs/${logId}/approve`);
      API.showToast('Action approved successfully by Super Admin.', 'success');
      AdminModule.loadTabContent();
    } catch (e) {
      console.error('Approve action error:', e);
      API.showToast(e.message || 'Failed to approve action', 'error');
    }
  },

  async rejectAction(logId, btnEl) {
    if (btnEl) {
      btnEl.classList.add('btn-loading');
      btnEl.innerHTML = '<span class="btn-spinner"></span> Rejecting...';
    }
    try {
      await API.post(`/admin/audit-logs/${logId}/reject`);
      API.showToast('Action rejected by Super Admin.', 'info');
      AdminModule.loadTabContent();
    } catch (e) {
      console.error('Reject action error:', e);
      API.showToast(e.message || 'Failed to reject action', 'error');
    }
  },

  // ==========================================
  // 5. SYSTEM AUDIT LOGS
  // ==========================================
  async renderAuditLogsPanel(container) {
    try {
      const logsData = await API.get('/admin/audit-logs?page=1&size=50').catch(() => ({ items: [] }));
      const logs = logsData.items || [];

      container.innerHTML = `
        <div class="admin-table-card">
          <div style="padding: 16px 20px; border-bottom: 1px solid var(--color-border); font-weight: 700; color: var(--color-primary); display: flex; justify-content: space-between; align-items: center;">
            <span>Immutable System Audit Logs</span>
            <span class="badge badge-primary">${logsData.total || logs.length} Records</span>
          </div>

          ${logs.length === 0 ? `
            <p style="padding: 40px; text-align: center; color: var(--color-text-muted);">No audit logs recorded yet.</p>
          ` : `
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Action</th>
                  <th>Entity</th>
                  <th>Actor ID</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                ${logs.map(l => `
                  <tr>
                    <td style="font-size: 12px;">${new Date(l.timestamp).toLocaleString()}</td>
                    <td><b>${l.action}</b></td>
                    <td>${l.entity_type} <span style="font-family:monospace; font-size:11px;">(${l.entity_id?.substring(0,8)}...)</span></td>
                    <td style="font-family:monospace; font-size:11.5px;">${l.actor_id ? l.actor_id.substring(0,8) + '...' : 'SYSTEM (n8n)'}</td>
                    <td><span class="badge badge-success">${l.approval_status || 'AUTO_APPROVED'}</span></td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          `}
        </div>
      `;
    } catch (e) {
      console.error(e);
    }
  },

  // ==========================================
  // 6. SYSTEM REFUNDS
  // ==========================================
  async renderRefundsPanel(container) {
    try {
      const refundsData = await API.get('/refunds?page=1&size=50').catch(() => ({ items: [] }));
      const refunds = refundsData.items || [];

      container.innerHTML = `
        <div class="admin-table-card">
          <div style="padding: 16px 20px; border-bottom: 1px solid var(--color-border); font-weight: 700; color: var(--color-primary); display: flex; justify-content: space-between; align-items: center;">
            <span>System Passenger Refunds</span>
            <span class="badge badge-primary">${refundsData.total || refunds.length} Records</span>
          </div>

          ${refunds.length === 0 ? `
            <p style="padding: 40px; text-align: center; color: var(--color-text-muted);">No refunds found in system.</p>
          ` : `
            <table class="admin-table">
              <thead>
                <tr>
                  <th>Refund ID</th>
                  <th>Amount</th>
                  <th>Reason</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${refunds.map(r => `
                  <tr>
                    <td style="font-family:monospace; font-size:12px;">${r.id.substring(0,8).toUpperCase()}</td>
                    <td><b>$${r.amount} ${r.currency}</b></td>
                    <td style="font-size:13px;">${r.reason || 'Booking Cancellation'}</td>
                    <td><span class="badge ${r.status === 'PROCESSED' ? 'badge-success' : 'badge-warning'}">${r.status}</span></td>
                    <td>
                      ${r.status === 'REQUESTED' ? `
                        <button class="btn-action-approve" onclick="AdminModule.updateRefundStatus('${r.id}', 'PROCESSED')">Mark Processed</button>
                        <button class="btn-action-reject" onclick="AdminModule.updateRefundStatus('${r.id}', 'REJECTED')">Reject</button>
                      ` : `
                        <span style="font-size: 12px; color: var(--color-text-muted);">Completed</span>
                      `}
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          `}
        </div>
      `;
    } catch (e) {
      console.error(e);
    }
  },

  async updateRefundStatus(refundId, status) {
    try {
      await API.patch(`/refunds/${refundId}/status`, { status });
      API.showToast(`Refund status updated to ${status}.`, 'success');
      AdminModule.loadTabContent();
    } catch (e) {
      // Handled
    }
  }
};
