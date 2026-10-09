/**
 * SkyFlow Flight Search & Multi-Currency Engine
 */
const SearchModule = {
  currentCurrency: 'USD',
  searchResults: [],
  selectedFlight: null,

  init() {
    const today = new Date().toISOString().split('T')[0];
    const dateInput = document.getElementById('search-date');
    if (dateInput) {
      dateInput.min = today;
      dateInput.value = today;
    }
  },

  handleCurrencyChange(currency) {
    SearchModule.currentCurrency = currency;
    API.showToast(`Display currency changed to ${currency}`, 'info');

    const badge = document.getElementById('search-results-currency-badge');
    if (badge) {
      badge.textContent = `Displaying in ${currency} (${CONFIG.CURRENCY_SYMBOLS[currency] || ''})`;
    }

    // Re-render flight cards if currently searching or viewing
    if (SearchModule.searchResults.length > 0) {
      SearchModule.renderFlightCards(SearchModule.searchResults);
    }
  },

  async handleSearchSubmit(event) {
    if (event) event.preventDefault();

    const origin = document.getElementById('search-origin')?.value.trim();
    const destination = document.getElementById('search-destination')?.value.trim();
    const departure_date = document.getElementById('search-date')?.value;
    const seat_class = document.getElementById('search-class')?.value || 'ECONOMY';

    if (!origin || !destination) {
      API.showToast('Please enter both Origin and Destination.', 'warning');
      return;
    }

    const submitBtn = document.getElementById('btn-search-submit');
    const originalText = submitBtn ? submitBtn.innerHTML : '<span>Search Flights</span> &rarr;';
    if (submitBtn) {
      submitBtn.classList.add('btn-loading');
      submitBtn.innerHTML = '<span class="btn-spinner"></span> Searching Flights...';
    }

    try {
      const results = await API.get('/flights/search', {
        origin,
        destination,
        departure_date,
        seat_class,
        display_currency: SearchModule.currentCurrency,
        passengers: 1
      });

      SearchModule.searchResults = Array.isArray(results) ? results : (results.items || []);
      
      App.showView('search-results');
      SearchModule.renderFlightCards(SearchModule.searchResults);

      // Scroll smoothly to results
      document.getElementById('view-search-results')?.scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
      // Handled in API client
    } finally {
      if (submitBtn) {
        submitBtn.classList.remove('btn-loading');
        submitBtn.innerHTML = originalText;
      }
    }
  },

  renderFlightCards(flights) {
    const container = document.getElementById('flight-cards-container');
    const heading = document.getElementById('search-results-heading');
    if (!container) return;

    if (!flights || flights.length === 0) {
      heading.textContent = 'No Flights Found';
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 40px;">
          <div style="font-size: 40px; margin-bottom: 12px;">🛫</div>
          <h3 style="color: var(--color-primary); margin-bottom: 8px;">No Scheduled Flights Matching Route</h3>
          <p style="color: var(--color-text-muted); font-size: 14px; max-width: 480px; margin: 0 auto 20px;">
            We couldn't find available seats for this date. You can create a test flight in the Admin Portal or adjust search dates.
          </p>
          <button class="btn-select-flight" onclick="App.navigate('admin')">Create Flight in Admin Portal &rarr;</button>
        </div>
      `;
      return;
    }

    heading.textContent = `${flights.length} Available Flight${flights.length > 1 ? 's' : ''}`;
    
    container.innerHTML = flights.map(flight => {
      const flightId = flight.flight_id || flight.id;
      const depDate = new Date(flight.departure_datetime || flight.departure_time);
      const arrDate = new Date(flight.arrival_datetime || flight.arrival_time);
      
      const depTimeStr = depDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const arrTimeStr = arrDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      const price = flight.display_price || flight.calculated_price || flight.base_price || 250;
      const currencySymbol = CONFIG.CURRENCY_SYMBOLS[SearchModule.currentCurrency] || '$';
      const formattedPrice = Number(price).toLocaleString();

      const availableSeats = flight.available_seats_in_class ?? flight.available_economy_seats ?? 50;

      const defaultFareOption = (flight.fare_options && flight.fare_options[0]) || null;
      const fareRuleId = defaultFareOption ? defaultFareOption.fare_rule_id : '';

      return `
        <div class="flight-ticket-card">
          
          <!-- Airline & Flight Code -->
          <div class="flight-airline-info">
            <div class="flight-icon-box">✈️</div>
            <div>
              <div class="flight-num">${flight.flight_number || 'PK-301'}</div>
              <div class="flight-aircraft">${flight.aircraft_model || 'Boeing 777-300ER'}</div>
              <span class="badge badge-primary" style="margin-top: 4px;">Direct Flight</span>
            </div>
          </div>

          <!-- Timeline & Cities -->
          <div class="flight-timeline-block">
            <div class="timeline-point">
              <div class="timeline-time">${depTimeStr}</div>
              <div class="timeline-city">${flight.origin}</div>
            </div>
            
            <div class="timeline-path">
              <div class="timeline-duration">Non-stop</div>
              <div class="timeline-line"></div>
              <div style="font-size: 11px; color: var(--color-text-muted);">${depDate.toLocaleDateString()}</div>
            </div>

            <div class="timeline-point">
              <div class="timeline-time">${arrTimeStr}</div>
              <div class="timeline-city">${flight.destination}</div>
            </div>
          </div>

          <!-- Pricing & CTA -->
          <div class="flight-pricing-box">
            <div class="fare-price-currency">${SearchModule.currentCurrency}</div>
            <div class="fare-price-display">${currencySymbol}${formattedPrice}</div>
            <div class="seat-status-pill badge ${availableSeats > 5 ? 'badge-success' : 'badge-warning'}">
              ${availableSeats > 0 ? `${availableSeats} Seats Available` : 'Waitlist Only'}
            </div>

            <div class="card-actions-group">
              <button type="button" id="btn-hold-${flightId}" class="btn-price-hold" onclick="SearchModule.handlePriceHold('${flightId}', '${fareRuleId}', ${price}, this)">
                ⏱️ Hold Price (15m)
              </button>
              
              ${availableSeats > 0 ? `
                <button type="button" id="btn-seat-${flightId}" class="btn-select-flight" onclick="BookingModule.openSeatMap('${flightId}', this)">
                  Select Seats &rarr;
                </button>
              ` : `
                <button type="button" id="btn-waitlist-${flightId}" class="btn-select-flight" style="background:#B45309;" onclick="BookingModule.joinWaitlist('${flightId}', this)">
                  Join Waitlist
                </button>
              `}
            </div>
          </div>

        </div>
      `;
    }).join('');
  },

  async handlePriceHold(flightId, fareRuleId, price, btnEl) {
    if (!AuthModule.currentUser) {
      API.showToast('Please login first to hold a price quote.', 'warning');
      AuthModule.openLoginModal();
      return;
    }

    const btn = btnEl || document.getElementById(`btn-hold-${flightId}`);
    const originalText = btn ? btn.innerHTML : '⏱️ Hold Price (15m)';
    if (btn) {
      btn.classList.add('btn-loading');
      btn.innerHTML = '<span class="btn-spinner dark"></span> Locking...';
    }

    try {
      let ruleId = fareRuleId;
      if (!ruleId || ruleId === 'undefined' || ruleId === 'null') {
        const flight = SearchModule.searchResults.find(f => (f.flight_id || f.id) === flightId);
        if (flight && flight.fare_options && flight.fare_options.length > 0) {
          ruleId = flight.fare_options[0].fare_rule_id;
        }
      }

      if (!ruleId || ruleId === 'undefined' || ruleId === 'null') {
        const rules = await API.get('/flights/fare-rules/all').catch(() => []);
        const rList = Array.isArray(rules) ? rules : (rules.items || []);
        const selectedClass = (document.getElementById('search-class')?.value || 'ECONOMY').toUpperCase();
        const matched = rList.find(r => (r.seat_class || '').toUpperCase() === selectedClass) || rList[0];
        if (matched) ruleId = matched.id;
      }

      if (!ruleId) {
        API.showToast('Could not find active fare rule for this flight.', 'warning');
        return;
      }

      const res = await API.post('/price-holds', {
        flight_id: flightId,
        seat_class: document.getElementById('search-class')?.value || 'ECONOMY',
        fare_rule_id: ruleId,
        passenger_count: 1
      });

      API.showToast(`Price quote of ${SearchModule.currentCurrency} ${price} locked for 15 minutes!`, 'success');
      if (btn) btn.innerHTML = '✅ Price Locked (15m)';
    } catch (e) {
      console.error('Price hold error:', e);
      API.showToast(e.message || 'Failed to lock price hold', 'error');
      if (btn) btn.innerHTML = originalText;
    } finally {
      if (btn && btn.innerHTML !== '✅ Price Locked (15m)') {
        btn.classList.remove('btn-loading');
        btn.innerHTML = originalText;
      }
    }
  }
};
