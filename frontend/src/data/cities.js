// India-first city catalogue for the discovery selector. EventMesh launches in
// India, so Indian cities lead; a small international set follows. Coordinates
// power "Use my location" → nearest supported city (haversine).

export const ALL_CITIES = 'All Cities';

// Shown in the Recommended group (detected city is prepended at runtime).
export const RECOMMENDED_CITIES = ['Mumbai', 'Bangalore'];

export const MAJOR_INDIAN_CITIES = [
  'Delhi NCR',
  'Hyderabad',
  'Chennai',
  'Pune',
  'Kolkata',
  'Ahmedabad',
  'Jaipur',
  'Kochi',
  'Goa',
  'Chandigarh',
  'Indore',
  'Lucknow',
  'Surat',
  'Nagpur',
  'Bhubaneswar',
];

export const INTERNATIONAL_CITIES = [
  'Singapore',
  'Dubai',
  'London',
  'Berlin',
  'New York',
  'San Francisco',
];

// [lat, lon] for every selectable city — used only for nearest-city detection.
const CITY_COORDS = {
  Mumbai: [19.076, 72.8777],
  Bangalore: [12.9716, 77.5946],
  'Delhi NCR': [28.6139, 77.209],
  Hyderabad: [17.385, 78.4867],
  Chennai: [13.0827, 80.2707],
  Pune: [18.5204, 73.8567],
  Kolkata: [22.5726, 88.3639],
  Ahmedabad: [23.0225, 72.5714],
  Jaipur: [26.9124, 75.7873],
  Kochi: [9.9312, 76.2673],
  Goa: [15.4909, 73.8278],
  Chandigarh: [30.7333, 76.7794],
  Indore: [22.7196, 75.8577],
  Lucknow: [26.8467, 80.9462],
  Surat: [21.1702, 72.8311],
  Nagpur: [21.1458, 79.0882],
  Bhubaneswar: [20.2961, 85.8245],
  Singapore: [1.3521, 103.8198],
  Dubai: [25.2048, 55.2708],
  London: [51.5074, -0.1278],
  Berlin: [52.52, 13.405],
  'New York': [40.7128, -74.006],
  'San Francisco': [37.7749, -122.4194],
};

// Display name → backend `city` query value, where they differ. The backend
// matches on lower(city); "Delhi NCR" is a region label, so query plain "Delhi".
const CITY_QUERY = {
  'Delhi NCR': 'Delhi',
};

export function cityQueryValue(city) {
  return CITY_QUERY[city] || city;
}

function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

/** Nearest selectable city to the given coordinates. */
export function nearestSupportedCity(lat, lon) {
  let best = null;
  let bestDist = Infinity;
  for (const [name, [clat, clon]] of Object.entries(CITY_COORDS)) {
    const dist = haversineKm(lat, lon, clat, clon);
    if (dist < bestDist) {
      bestDist = dist;
      best = name;
    }
  }
  return best;
}
