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

function renderFiltered(fromStr, toStr) {
  console.log("renderFiltered: start", { fromStr, toStr });

  if (clusterGroup) {
    map.removeLayer(clusterGroup);
    clusterGroup = null;
  }

  const filtered = allPoints.filter(p => dateInRange(p.date, fromStr || "", toStr || ""));
  console.log("renderFiltered: filtered count", filtered.length);

  document.getElementById('status').textContent =
    filtered.length ? `Showing ${filtered.length} event(s)` : 'No events in range';

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

async function loadMapData() {
  /* load mapData.json converted to JS objects */
  console.log("loadMapData: start");

  const resp = await fetch('mapData.json');
  const data = await resp.json();

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
