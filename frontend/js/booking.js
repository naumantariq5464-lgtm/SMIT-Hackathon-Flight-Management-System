/**
 * SkyFlow Interactive Seat Map & Atomic Booking Module
 */
const BookingModule = {
  currentFlightId: null,
  selectedSeat: null,
  selectedSeatNumber: null,
  seatClass: 'ECONOMY',
  flightDetails: null,
  seatsList: [],
  holdTimerInterval: null,
  holdExpiresAt: null,

  async openSeatMap(flightId, btnEl) {
    BookingModule.currentFlightId = flightId;
    BookingModule.selectedSeat = null;
    BookingModule.selectedSeatNumber = null;
    BookingModule.seatClass = (document.getElementById('search-class')?.value || 'ECONOMY').toUpperCase();

    const btn = btnEl || document.getElementById(`btn-seat-${flightId}`);
    const originalText = btn ? btn.innerHTML : 'Select Seats &rarr;';
    if (btn) {
      btn.classList.add('btn-loading');
      btn.innerHTML = '<span class="btn-spinner"></span> Loading Cabin...';
    }

    try {
      const flight = await API.get(`/flights/${flightId}`);
      BookingModule.flightDetails = flight;

      const seatsData = await API.get(`/flights/${flightId}/seats`);
      const seats = Array.isArray(seatsData) ? seatsData : (seatsData?.seats || []);
      BookingModule.seatsList = seats;
      
      App.showView('seat-map');
      BookingModule.renderSeatMap(flight, seats);
      
      // Scroll to seat map
      document.getElementById('view-seat-map')?.scrollIntoView({ behavior: 'smooth' });

    } catch (e) {
      console.error('Failed to open seat map:', e);
      API.showToast('Could not load seat map: ' + (e.message || e), 'error');
    } finally {
      if (btn) {
        btn.classList.remove('btn-loading');
        btn.innerHTML = originalText;
      }
    }
  },

  renderSeatMap(flight, seats) {
    const container = document.getElementById('view-seat-map');
    if (!container) return;

    const seatList = Array.isArray(seats) ? seats : (seats?.seats || []);

    // Group seats by Class and Row
    const grouped = {};
    seatList.forEach(s => {
      const cls = (s.seat_class || 'ECONOMY').toUpperCase();
      if (!grouped[cls]) grouped[cls] = {};
      const rowMatch = s.seat_number ? s.seat_number.match(/\d+/) : null;
      const row = s.row_number || (rowMatch ? parseInt(rowMatch[0]) : 1);
      if (!grouped[cls][row]) grouped[cls][row] = [];
      grouped[cls][row].push(s);
    });

    container.innerHTML = `
      <div class="seatmap-container">
        
        <!-- Header -->
        <div class="seatmap-header">
          <div class="seatmap-flight-summary">
            <button class="btn-login" onclick="App.showView('search-results')">&larr; Back to Search</button>
            <div>
              <h2 class="section-title" style="font-size: 22px;">Select Your Seat — ${flight.flight_number}</h2>
              <p class="section-subtitle">${flight.origin} &rarr; ${flight.destination} (${flight.aircraft?.model || 'Boeing 777'})</p>
            </div>
          </div>
          <div class="badge badge-primary">Class: ${BookingModule.seatClass}</div>
        </div>

        <!-- 10-Minute Hold Timer Box (Active when seat clicked) -->
        <div class="hold-timer-card" id="seat-hold-timer-box" style="display: none;">
          <div>
            <strong>⏱️ Seat Reserved (10-Minute Lock Active)</strong>
            <p style="font-size: 12px; margin-top: 2px;">Your seat is temporarily locked against overselling.</p>
          </div>
          <div class="timer-countdown-clock" id="hold-countdown-display">10:00</div>
        </div>

        <!-- Legend -->
        <div class="seat-legend-bar">
          <div class="legend-item"><div class="legend-box legend-available"></div> Available</div>
          <div class="legend-item"><div class="legend-box legend-selected"></div> Selected</div>
          <div class="legend-item"><div class="legend-box legend-booked"></div> Occupied / Held</div>
        </div>

        <!-- Aircraft Fuselage -->
        <div class="aircraft-cabin-wrapper">
          <div class="cabin-cockpit-nose"></div>

          ${['FIRST', 'BUSINESS', 'ECONOMY'].map(cls => {
            const rows = grouped[cls] || {};
            const rowKeys = Object.keys(rows).sort((a,b) => parseInt(a) - parseInt(b));
            if (rowKeys.length === 0) return '';

            return `
              <div class="cabin-class-section">
                <div class="cabin-section-title">${cls} CLASS</div>
                ${rowKeys.map(rowNum => {
                  const rowSeats = rows[rowNum] || [];
                  const half = Math.ceil(rowSeats.length / 2);
                  const leftSeats = rowSeats.slice(0, half);
                  const rightSeats = rowSeats.slice(half);

                  return `
                    <div class="seat-grid-row">
                      ${leftSeats.map(s => BookingModule.renderSeatButton(s)).join('')}
                      <div class="aisle-gap"></div>
                      ${rightSeats.map(s => BookingModule.renderSeatButton(s)).join('')}
                    </div>
                  `;
                }).join('')}
              </div>
            `;
          }).join('')}
        </div>

        <!-- Checkout Dock -->
        <div class="checkout-dock">
          <div>
            <div style="font-size: 13px; color: var(--color-text-muted);">Selected Seat</div>
            <div style="font-family: var(--font-heading); font-size: 20px; font-weight: 800; color: var(--color-primary);" id="selected-seat-label">
              None Selected
            </div>
          </div>

          <div style="display: flex; gap: 12px; align-items: center;">
            <button type="button" class="btn-select-flight" id="btn-proceed-checkout" disabled onclick="BookingModule.openCheckoutModal()">
              Proceed to Checkout &rarr;
            </button>
          </div>
        </div>

      </div>
    `;
  },

  renderSeatButton(seat) {
    const isBooked = seat.status ? (seat.status !== 'AVAILABLE') : (!seat.is_available);
    const isSelected = (BookingModule.selectedSeat && BookingModule.selectedSeat.id === seat.id) || BookingModule.selectedSeatNumber === seat.seat_number;
    const isTargetClass = (seat.seat_class || '').toUpperCase() === BookingModule.seatClass.toUpperCase();

    return `
      <button 
        type="button" 
        id="seat-btn-${seat.id}"
        class="seat-btn ${isSelected ? 'selected' : ''}" 
        ${isBooked || !isTargetClass ? 'disabled' : ''}
        onclick="BookingModule.handleSeatClick('${seat.id}', '${seat.seat_number}', '${seat.seat_class}')"
        title="Seat ${seat.seat_number} (${seat.seat_class}) - ${isBooked ? (seat.status || 'Occupied') : 'Available'}"
      >
        ${seat.seat_number}
      </button>
    `;
  },

  async handleSeatClick(seatId, seatNumber, seatClass) {
    BookingModule.selectedSeat = { id: seatId, seat_number: seatNumber, seat_class: seatClass };
    BookingModule.selectedSeatNumber = seatNumber;
    BookingModule.seatClass = seatClass.toUpperCase();

    // Update UI highlights
    document.querySelectorAll('.seat-btn').forEach(btn => btn.classList.remove('selected'));
    const clickedBtn = document.getElementById(`seat-btn-${seatId}`);
    if (clickedBtn) clickedBtn.classList.add('selected');

    const seatLabel = document.getElementById('selected-seat-label');
    if (seatLabel) seatLabel.textContent = `Seat ${seatNumber} (${seatClass})`;

    const proceedBtn = document.getElementById('btn-proceed-checkout');
    if (proceedBtn) proceedBtn.removeAttribute('disabled');

    // Trigger 10-minute hold if user is logged in
    if (AuthModule.currentUser) {
      try {
        await API.post('/bookings/hold', {
          flight_id: BookingModule.currentFlightId,
          seat_ids: [seatId]
        });

        BookingModule.startHoldTimer(10 * 60);
        API.showToast(`Seat ${seatNumber} held for 10 minutes!`, 'info');
      } catch (e) {
        console.error('Seat hold notice:', e);
      }
    }
  },

  startHoldTimer(seconds) {
    clearInterval(BookingModule.holdTimerInterval);
    const box = document.getElementById('seat-hold-timer-box');
    const clock = document.getElementById('hold-countdown-display');
    if (box) box.style.display = 'flex';

    let remaining = seconds;
    const updateDisplay = () => {
      const mins = Math.floor(remaining / 60);
      const secs = remaining % 60;
      if (clock) clock.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

      if (remaining <= 0) {
        clearInterval(BookingModule.holdTimerInterval);
        API.showToast('Your 10-minute seat hold has expired.', 'warning');
        if (box) box.style.display = 'none';
      }
      remaining--;
    };

    updateDisplay();
    BookingModule.holdTimerInterval = setInterval(updateDisplay, 1000);
  },

  openCheckoutModal() {
    if (!AuthModule.currentUser) {
      API.showToast('Please login first to complete your reservation.', 'warning');
      AuthModule.openLoginModal();
      return;
    }

    const flight = BookingModule.flightDetails || {};
    const currency = SearchModule.currentCurrency || 'USD';
    const symbol = CONFIG.CURRENCY_SYMBOLS[currency] || '$';
    const price = flight.calculated_price || flight.base_price || 250;

    const modalHtml = `
      <div class="modal-overlay active" id="modal-checkout">
        <div class="modal-card" style="max-width: 580px;">
          <div class="modal-header">
            <h3 class="modal-title">Confirm Booking Checkout</h3>
            <button class="modal-close-btn" onclick="document.getElementById('modal-checkout').remove()">✕</button>
          </div>
          <div class="modal-body">
            
            <div style="background: var(--color-accent-soft); padding: 14px; border-radius: var(--radius-md); margin-bottom: 20px;">
              <div style="display:flex; justify-content:space-between; font-weight:700; color:var(--color-primary);">
                <span>${flight.flight_number || 'Flight'} (${flight.origin} &rarr; ${flight.destination})</span>
                <span>Seat ${BookingModule.selectedSeatNumber || 'Assigned'}</span>
              </div>
              <div style="font-size:12.5px; color:var(--color-text-muted); margin-top:4px;">
                Class: <b>${BookingModule.seatClass}</b> | Total: <b>${symbol}${price} ${currency}</b>
              </div>
            </div>

            <form id="form-checkout-submit" onsubmit="BookingModule.submitBooking(event)">
              
              <div class="form-group">
                <label class="form-label">Passenger Full Name</label>
                <input type="text" id="chk-name" class="form-input" value="${AuthModule.currentUser.full_name || ''}" required />
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px;">
                <div class="form-group">
                  <label class="form-label">Passport / ID Number</label>
                  <input type="text" id="chk-passport" class="form-input" placeholder="e.g. PK9876543" required />
                </div>
                <div class="form-group">
                  <label class="form-label">Date of Birth</label>
                  <input type="date" id="chk-dob" class="form-input" required />
                </div>
              </div>

              <div class="form-group" style="margin-top: 14px;">
                <label class="form-label">Payment Method</label>
                <select id="chk-payment" class="form-select">
                  <option value="CREDIT_CARD">Credit / Debit Card</option>
                  <option value="TRAVEL_CREDIT">Use Available Travel Credit</option>
                </select>
              </div>

              <div style="margin-top: 14px; display: flex; align-items: center; gap: 8px;">
                <input type="checkbox" id="chk-partial" style="width:16px; height:16px; accent-color:var(--color-primary);" />
                <label for="chk-partial" style="font-size: 13px; font-weight: 600; color: var(--color-text-muted);">
                  Allow Partial Booking (if group booking exceeds available capacity)
                </label>
              </div>

              <button type="submit" class="btn-primary-full" style="margin-top: 24px;">
                Confirm & Issue E-Ticket (${symbol}${price})
              </button>

            </form>
          </div>
        </div>
      </div>
    `;

    // Remove existing checkout modal if any
    document.getElementById('modal-checkout')?.remove();
    document.body.insertAdjacentHTML('beforeend', modalHtml);
  },

  async submitBooking(event) {
    event.preventDefault();
    const fullName = (document.getElementById('chk-name')?.value || 'Valued Passenger').trim();
    const nameParts = fullName.split(' ');
    const firstName = nameParts[0] || 'Passenger';
    const lastName = nameParts.slice(1).join(' ') || 'User';
    const passport = document.getElementById('chk-passport')?.value.trim() || 'PK123456';
    const allowPartial = document.getElementById('chk-partial')?.checked || false;

    const submitBtn = event.target.querySelector('button[type="submit"]') || document.querySelector('#form-checkout-submit button[type="submit"]');
    const originalText = submitBtn ? submitBtn.innerHTML : 'Confirm & Issue E-Ticket';
    if (submitBtn) {
      submitBtn.classList.add('btn-loading');
      submitBtn.innerHTML = '<span class="btn-spinner"></span> Reserving Seat & Issuing Ticket...';
    }

    try {
      // 1. Get Fare Rules to pick matching rule for class
      let matchedRule = null;
      
      // Try from search results fare_options first
      const currentFlight = SearchModule.searchResults.find(f => (f.flight_id || f.id) === BookingModule.currentFlightId);
      if (currentFlight && currentFlight.fare_options && currentFlight.fare_options.length > 0) {
        matchedRule = currentFlight.fare_options.find(fo => (fo.seat_class || '').toUpperCase() === BookingModule.seatClass.toUpperCase()) || currentFlight.fare_options[0];
      }

      // Fallback to public fare rules endpoint
      if (!matchedRule) {
        const fareRules = await API.get('/flights/fare-rules/all').catch(() => []);
        const rList = Array.isArray(fareRules) ? fareRules : (fareRules.items || []);
        matchedRule = rList.find(r => (r.seat_class || '').toUpperCase() === BookingModule.seatClass.toUpperCase()) || rList[0];
      }

      const fareRuleId = matchedRule ? (matchedRule.fare_rule_id || matchedRule.id) : null;

      if (!fareRuleId) {
        API.showToast('No active fare rules found. Please check system configuration.', 'warning');
        return;
      }

      const res = await API.post('/bookings', {
        flights: [
          {
            flight_id: BookingModule.currentFlightId,
            fare_rule_id: fareRuleId
          }
        ],
        passengers: [
          {
            first_name: firstName,
            last_name: lastName,
            passport_number: passport,
            seat_class: BookingModule.seatClass,
            seat_id: BookingModule.selectedSeat?.id || undefined
          }
        ],
        group_failure_policy: allowPartial ? 'PARTIAL_ALLOWED' : 'FULL_FAILURE'
      });

      document.getElementById('modal-checkout')?.remove();
      clearInterval(BookingModule.holdTimerInterval);

      const pnr = (Array.isArray(res) && res[0]) ? res[0].booking_reference : 'Confirmed';
      API.showToast(`🎉 Booking Confirmed (PNR: ${pnr})! E-Ticket sent to your email.`, 'success');
      
      // Navigate to My Bookings
      App.navigate('bookings');

    } catch (e) {
      console.error('Booking submission error:', e);
      API.showToast(e.message || 'Failed to complete booking', 'error');
    } finally {
      if (submitBtn) {
        submitBtn.classList.remove('btn-loading');
        submitBtn.innerHTML = originalText;
      }
    }
  },

  async joinWaitlist(flightId, btnEl) {
    if (!AuthModule.currentUser) {
      API.showToast('Please login first to join the waitlist.', 'warning');
      AuthModule.openLoginModal();
      return;
    }

    const btn = btnEl || document.getElementById(`btn-waitlist-${flightId}`);
    const originalText = btn ? btn.innerHTML : 'Join Waitlist';
    if (btn) {
      btn.classList.add('btn-loading');
      btn.innerHTML = '<span class="btn-spinner"></span> Joining...';
    }

    try {
      await API.post('/waitlist', {
        flight_id: flightId,
        seat_class: document.getElementById('search-class')?.value || 'ECONOMY'
      });

      API.showToast('Added to flight waitlist with priority status!', 'success');
      if (btn) btn.innerHTML = '✅ Waitlisted';
    } catch (e) {
      console.error('Waitlist error:', e);
      API.showToast(e.message || 'Failed to join waitlist', 'error');
      if (btn) btn.innerHTML = originalText;
    } finally {
      if (btn && btn.innerHTML !== '✅ Waitlisted') {
        btn.classList.remove('btn-loading');
        btn.innerHTML = originalText;
      }
    }
  }
};
