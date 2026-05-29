export function filterEvents(events, filters) {
  let out = events;
  if (filters.q) {
    const q = filters.q.toLowerCase();
    out = out.filter(e =>
      e.title.toLowerCase().includes(q) ||
      e.city.toLowerCase().includes(q) ||
      e.category.toLowerCase().includes(q) ||
      e.venue.toLowerCase().includes(q) ||
      e.blurb.toLowerCase().includes(q)
    );
  }
  if (filters.city !== 'All cities') out = out.filter(e => e.city === filters.city);
  if (filters.price === 'free') out = out.filter(e => e.price === 'Free');
  if (filters.price === 'paid') out = out.filter(e => e.price !== 'Free');
  if (filters.date !== 'any') {
    const now = new Date();
    const d = new Date();
    if (filters.date === 'today') {
      out = out.filter(e => new Date(e.date).toDateString() === now.toDateString());
    } else if (filters.date === 'week') {
      d.setDate(d.getDate() + 7);
      out = out.filter(e => { const ed = new Date(e.date); return ed >= now && ed <= d; });
    } else if (filters.date === 'month') {
      d.setDate(d.getDate() + 30);
      out = out.filter(e => { const ed = new Date(e.date); return ed >= now && ed <= d; });
    }
  }
  return out;
}
