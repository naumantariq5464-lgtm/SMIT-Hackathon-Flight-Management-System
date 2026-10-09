/**
 * SkyFlow Configuration
 */
const CONFIG = {
  API_BASE_URL: 'http://127.0.0.1:8000/api/v1',
  DEFAULT_CURRENCY: 'USD',
  CURRENCY_SYMBOLS: {
    USD: '$',
    PKR: 'Rs ',
    EUR: '€',
    GBP: '£',
    AED: 'AED ',
    SAR: 'SAR ',
    CAD: 'CA$ ',
    INR: '₹',
    AUD: 'AU$ ',
    JPY: '¥'
  },
  EXCHANGE_RATES: {
    USD: 1.0,
    EUR: 0.92,
    GBP: 0.79,
    AED: 3.67,
    PKR: 278.50,
    INR: 83.25,
    SAR: 3.75,
    CAD: 1.36,
    AUD: 1.53,
    JPY: 149.50
  },
  HOLD_DURATION_MINUTES: 10,
  PRICE_HOLD_DURATION_MINUTES: 15
};
