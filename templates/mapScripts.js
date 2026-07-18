const map = L.map('map', { zoomSnap: 0.25 });
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

console.log("Leaflet: map init successful");

function escapeHtml(str) {
  return (str ?? "").toString()
    .replaceAll('&','&amp;')
    .replaceAll('<','&lt;')
    .replaceAll('>','&gt;')
    .replaceAll('"','&quot;')
    .replaceAll("'","&#039;");
}

let allPoints = [];
let clusterGroup = null;

function dateInRange(dateStr, fromStr, toStr) {
  if (!dateStr) return false;
  if (fromStr && dateStr < fromStr) return false;
  if (toStr && dateStr > toStr) return false;
  return true;
}


// BEGIN helpers for "show all" button 

function parseYMDToLocalDate(ymdStr) {
  const s = String(ymdStr || "").trim();
  // expecting YYYY-MM-DD
  const m = s.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return null;

  const y = Number(m[1]);
  const mo = Number(m[2]) - 1;
  const d = Number(m[3]);
  return new Date(y, mo, d, 0, 0, 0, 0);
}

function ymdFromLocalDate(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function findLargestContiguousDateRun(uniqueSortedDates) {
  /**
   * Returns the overall observed date span (min/max) as [bestStart, bestEnd].
   * Works even if the caller passes unsorted input.
   *
   * @param {string[]} uniqueSortedDates - ISO dates 'YYYY-MM-DD' (ideally unique; sorting makes it safe).
   * @returns {[string, string]} - [bestStart, bestEnd]
   *
   * call it like this:
   * const [ bestStart, bestEnd ] = findLargestContiguousDateRun(uniqueDates);
   */
  // #CAREFUL: avoid index errors on empty/null input.
  if (!uniqueSortedDates || uniqueSortedDates.length === 0) {
    return [null, null];
  }

  const sortedDates = [...uniqueSortedDates].sort(); // 'YYYY-MM-DD' => lexicographic == chronological
  const bestStart = sortedDates[0];
  const bestEnd = sortedDates[sortedDates.length - 1];

  return [bestStart, bestEnd];
}
// END helpers for "show all" button 

function renderFiltered(fromStr, toStr) {
  console.log("renderFiltered: start", { fromStr, toStr });

  if (clusterGroup) {
    map.removeLayer(clusterGroup);
    clusterGroup = null;
  }

  const total = allPoints.length; // Y
  const filtered = allPoints.filter(p => dateInRange(p.date, fromStr || "", toStr || ""));
  console.log("renderFiltered: filtered count", filtered.length);

  document.getElementById('status').textContent =
    filtered.length
      ? `Showing ${filtered.length} of ${total} event(s)`
      : `No events in range (${fromStr || '…'} → ${toStr || '…'})`;

  console.log("renderFiltered: status set");

  clusterGroup = L.markerClusterGroup({
    chunkedLoading: true,
    showCoverageOnHover: true,
    maxClusterRadius: 50
  });

  let bounds = [];

  for (const p of filtered) {
    const lat = p.lat, lon = p.lon;
    const latType = typeof lat;
    const lonType = typeof lon;

    if (typeof lat !== 'number' || typeof lon !== 'number') {
      console.log("marker skip: lat/lon not numbers", { lat, lon, latType, lonType, uid: p.uid, date: p.date });
      continue;
    }

    if (Number.isNaN(lat) || Number.isNaN(lon)) {
      console.log("marker skip: lat/lon is NaN", { lat, lon, uid: p.uid, date: p.date });
      continue;
    }

    const loc = p.location_text || "";
    const display = p.display_name || "";
    const summary = p.summary || "";
    const date = p.date || "";

    const popupHtml = `
      <div style="max-width:280px;">
        <div style="font-weight:700; margin-bottom:4px;">${escapeHtml(summary || 'Event')}</div>
        <div style="font-size:12px;"><b>Date:</b> ${escapeHtml(date)}</div>
        <div style="font-size:12px; margin-top:4px;"><b>Location:</b> ${escapeHtml(loc)}</div>
        <div style="font-size:12px; margin-top:4px;"><b>Geocoder:</b> ${escapeHtml(display)}</div>
      </div>
    `;

    const marker = L.circleMarker([lat, lon], {
      radius: 7,
      weight: 1,
      color: '#2563eb',
      fillColor: '#3b82f6',
      fillOpacity: 0.85
    }).bindPopup(popupHtml);

    marker.addTo(clusterGroup);
    bounds.push([lat, lon]);
  }

  clusterGroup.addTo(map);
  console.log("renderFiltered: markers added to clusterGroup", { boundsCount: bounds.length });

  if (bounds.length) map.fitBounds(L.latLngBounds(bounds).pad(0.15));

  console.log("renderFiltered: done");
}


/* debugging only, see duck.ai 2026/07/18 */ 

function debugSampleDates(points, limit = 20) {
  // Human-readable logging to quickly detect date formats in mapData.json
  const samples = (points || [])
    .map(p => p && p.date)
    .filter(v => v !== null && v !== undefined)
    .slice(0, limit);

  console.log("DEBUG: date samples (raw):", samples);

  const unique = Array.from(new Set(samples.map(v => String(v))));
  console.log("DEBUG: unique raw date strings (first 30):", unique.slice(0, 30));

  if (samples.length > 0) {
    const s = String(samples[0]);
    console.log("DEBUG: first sample length:", s.length);
    console.log("DEBUG: first sample prefix(0..10):", s.slice(0, 10));
  }

  // Also helpful: show whether values look like YYYY-MM-DD or full ISO datetime
  const counts = { "YYYY-MM-DD": 0, "ISO-like": 0, "other": 0 };
  for (const v of unique) {
    const t = v.trim();
    if (/^\d{4}-\d{2}-\d{2}$/.test(t)) counts["YYYY-MM-DD"]++;
    else if (/^\d{4}-\d{2}-\d{2}T/.test(t) || /^\d{4}-\d{2}-\d{2} /.test(t)) counts["ISO-like"]++;
    else counts["other"]++;
  }
  console.log("DEBUG: date format counts:", counts);
}

/* debugging end, see duck.ai 2026/07/18 */ 



async function loadMapData() {
  /* load mapData.json converted to JS objects */
  console.log("loadMapData: start");

  const resp = await fetch('mapData.json');
  const data = await resp.json();

  // debugSampleDates(data, 30); // <-- debug only, see duck.ai 2026/07/18

  allPoints = (data || []).map(p => ({
    summary: p.summary,
    uid: p.uid,
    date: p.date,
    location_text: p.location_text,
    lat: Number(p.lat),
    lon: Number(p.lon),
    display_name: p.display_name,
    country_code: p.country_code
  }));

  console.log("loadMapData: parsed points", allPoints.length);

  const dates = allPoints.map(p => p.date).filter(Boolean).sort();
  const min = dates[0] || "";
  const max = dates[dates.length - 1] || "";

  if (document.getElementById('fromDate')) document.getElementById('fromDate').value = min;
  if (document.getElementById('toDate')) document.getElementById('toDate').value = max;

  renderFiltered(min, max);
  return allPoints;
}

loadMapData().catch(e => {
  console.error(e);
  console.error("loadMapData failed", e?.name, e?.message);
  map.setView([51.0, 10.0], 4);
});
