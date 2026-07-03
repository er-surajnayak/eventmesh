// Filter option constants for the discovery UI. (The old hardcoded EVENTS array
// was removed in Phase 5B — the feed now comes from GET /api/v1/events.)

export const DEFAULT_FILTERS = {
  q: '', city: 'All cities', date: 'all', price: 'all', type: 'all', source: 'All sources',
};

export const CITIES = ['All cities', 'San Francisco', 'London', 'New York', 'Bangalore', 'Berlin'];

export const DATE_FILTERS = [
  { key: 'all', label: 'Anytime' },
  { key: 'today', label: 'Today' },
  { key: 'week', label: 'This Week' },
  { key: 'month', label: 'This Month' },
];

export const PRICE_FILTERS = [
  { key: 'all', label: 'Pricing' },
  { key: 'free', label: 'Free' },
  { key: 'paid', label: 'Paid' },
];

export const TYPE_FILTERS = [
  { key: 'all', label: 'Format' },
  { key: 'in-person', label: 'In-person' },
  { key: 'online', label: 'Online' },
];
