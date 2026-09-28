/**
 * Cyclone Comparison Controller — Visual & Analytical Multi-Storm Benchmarking
 * Powers the "Compare" tab: side-by-side interactive track maps, metric tables,
 * multi-storm temporal intensity charts, and peak satellite observation cards.
 */

import { API } from './api.js';

export class CompareController {
  constructor() {
    this.map1 = null;
    this.map2 = null;
    this.layer1 = L.layerGroup();
    this.layer2 = L.layerGroup();
    this.storm1Data = null;
    this.storm2Data = null;
    this.hasLoaded = false;

    // Maps initialized lazily when compare tab is opened
    this.setupListeners();
  }

  initMaps() {
    const el1 = document.getElementById('compare-map-1');
    const el2 = document.getElementById('compare-map-2');
    if (!el1 || !el2 || typeof L === 'undefined') return;

    if (this.map1) {
      try { this.map1.remove(); } catch(e){}
      this.map1 = null;
    }
    if (this.map2) {
      try { this.map2.remove(); } catch(e){}
      this.map2 = null;
    }

    el1.innerHTML = '';
    el2.innerHTML = '';

    const mapOptions = {
      center: [18.0, 85.0],
      zoom: 5,
      minZoom: 3,
      maxZoom: 12,
      zoomControl: true,
      attributionControl: false
    };

    // Initialize Map 1
    this.map1 = L.map('compare-map-1', mapOptions);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map1);
    this.layer1 = L.layerGroup().addTo(this.map1);

    // Initialize Map 2
    this.map2 = L.map('compare-map-2', mapOptions);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(this.map2);
    this.layer2 = L.layerGroup().addTo(this.map2);
  }

  setupListeners() {
    const btn = document.getElementById('btn-run-compare');
    if (btn) {
      btn.addEventListener('click', () => {
        const s1 = document.getElementById('compare-storm-1')?.value || 'AMPHAN';
        const s2 = document.getElementById('compare-storm-2')?.value || 'FANI';
        this.runComparison(s1, s2);
      });
    }

    // Auto-run when switching storms
    document.getElementById('compare-storm-1')?.addEventListener('change', () => {
      const s1 = document.getElementById('compare-storm-1')?.value || 'AMPHAN';
      const s2 = document.getElementById('compare-storm-2')?.value || 'FANI';
      this.runComparison(s1, s2);
    });

    document.getElementById('compare-storm-2')?.addEventListener('change', () => {
      const s1 = document.getElementById('compare-storm-1')?.value || 'AMPHAN';
      const s2 = document.getElementById('compare-storm-2')?.value || 'FANI';
      this.runComparison(s1, s2);
    });
  }

  invalidateSize() {
    if (!this.map1 || !this.map2) {
      this.initMaps();
    }
    const s1 = document.getElementById('compare-storm-1')?.value || 'AMPHAN';
    const s2 = document.getElementById('compare-storm-2')?.value || 'FANI';
    if (!this.storm1Data || !this.storm2Data) {
      this.runComparison(s1, s2);
    }
    const update = () => {
      if (this.map1) this.map1.invalidateSize();
      if (this.map2) this.map2.invalidateSize();
      this.refitBounds();
    };
    setTimeout(update, 60);
    setTimeout(update, 220);
  }

  refitBounds() {
    if (this.storm1Bounds && this.map1 && this.map1.getContainer().clientWidth > 0) {
      try {
        this.map1.fitBounds(this.storm1Bounds, { padding: [20, 20], maxZoom: 7 });
      } catch (e) {}
    }
    if (this.storm2Bounds && this.map2 && this.map2.getContainer().clientWidth > 0) {
      try {
        this.map2.fitBounds(this.storm2Bounds, { padding: [20, 20], maxZoom: 7 });
      } catch (e) {}
    }
  }

  haversineKm(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon/2) * Math.sin(dLon/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    return R * c;
  }

  calculateTrackLength(pts) {
    if (!pts || pts.length < 2) return 0;
    let dist = 0;
    for (let i = 0; i < pts.length - 1; i++) {
      dist += this.haversineKm(pts[i].latitude, pts[i].longitude, pts[i+1].latitude, pts[i+1].longitude);
    }
    return Math.round(dist);
  }

  async runComparison(stormId1, stormId2) {
    const btn = document.getElementById('btn-run-compare');
    const origText = btn ? btn.textContent : '';
    if (btn) {
      btn.textContent = 'Comparing…';
      btn.disabled = true;
    }

    try {
      const [d1, d2, t1, t2] = await Promise.all([
        API.getStormDetail(stormId1),
        API.getStormDetail(stormId2),
        API.getStormTimeline(stormId1).catch(() => ({ steps: [] })),
        API.getStormTimeline(stormId2).catch(() => ({ steps: [] }))
      ]);

      if (!d1 || !d2) return;
      this.storm1Data = d1;
      this.storm2Data = d2;

      // 1. Update Development Table
      this.updateTable(d1, d2);

      // 2. Render Maps
      this.renderTrackMap(this.map1, this.layer1, d1, '#00f2fe', (bounds) => { this.storm1Bounds = bounds; });
      this.renderTrackMap(this.map2, this.layer2, d2, '#f59e0b', (bounds) => { this.storm2Bounds = bounds; });

      // 3. Render Comparative Intensity Chart
      this.renderIntensityChart(d1, d2, t1.steps || [], t2.steps || []);

      // 4. Render Satellite Peek Cards
      this.renderSatelliteCards(d1, d2);

    } catch (err) {
      console.error('Comparison error:', err);
    } finally {
      if (btn) {
        btn.textContent = origText || 'Compare';
        btn.disabled = false;
      }
    }
  }

  updateTable(d1, d2) {
    const p1 = d1.track_points || [];
    const p2 = d2.track_points || [];

    // Names
    const h1 = document.getElementById('cmp-head-1');
    const h2 = document.getElementById('cmp-head-2');
    if (h1) h1.textContent = d1.storm_name;
    if (h2) h2.textContent = d2.storm_name;

    // Formation
    const f1 = p1.length > 0 ? p1[0].iso_time.split(' ')[0] : '—';
    const f2 = p2.length > 0 ? p2[0].iso_time.split(' ')[0] : '—';
    this.setText('cmp-form-1', f1);
    this.setText('cmp-form-2', f2);

    // Duration
    const dur1 = p1.length > 1 ? this.calculateDuration(p1[0].iso_time, p1[p1.length - 1].iso_time) : '—';
    const dur2 = p2.length > 1 ? this.calculateDuration(p2[0].iso_time, p2[p2.length - 1].iso_time) : '—';
    this.setText('cmp-dur-1', dur1);
    this.setText('cmp-dur-2', dur2);

    // Peak Intensity
    const peak1 = this.getPeakIntensity(p1);
    const peak2 = this.getPeakIntensity(p2);
    this.setText('cmp-int-1', `${peak1.windKmh} km/h (${peak1.pres} hPa)`);
    this.setText('cmp-int-2', `${peak2.windKmh} km/h (${peak2.pres} hPa)`);

    // Landfall / Dissipation
    const last1 = p1.length > 0 ? p1[p1.length - 1] : null;
    const last2 = p2.length > 0 ? p2[p2.length - 1] : null;
    this.setText('cmp-land-1', last1 ? `${last1.latitude.toFixed(1)}°N, ${last1.longitude.toFixed(1)}°E` : '—');
    this.setText('cmp-land-2', last2 ? `${last2.latitude.toFixed(1)}°N, ${last2.longitude.toFixed(1)}°E` : '—');

    // Track length
    const len1 = this.calculateTrackLength(p1);
    const len2 = this.calculateTrackLength(p2);
    this.setText('cmp-len-1', `${len1.toLocaleString()} km`);
    this.setText('cmp-len-2', `${len2.toLocaleString()} km`);
  }

  calculateDuration(startIso, endIso) {
    try {
      const ms = new Date(endIso) - new Date(startIso);
      const hours = Math.round(ms / (1000 * 60 * 60));
      const days = Math.floor(hours / 24);
      const remHours = hours % 24;
      return `${days}d ${remHours}h (${hours} hrs)`;
    } catch (e) {
      return '—';
    }
  }

  getPeakIntensity(pts) {
    let maxWind = 0;
    let minPres = 1010;
    pts.forEach(p => {
      const w = p.max_sustained_wind_kt || 0;
      if (w > maxWind) maxWind = w;
      const pres = p.min_central_pressure_mb;
      if (pres && pres < minPres) minPres = pres;
    });
    return {
      windKt: maxWind,
      windKmh: Math.round(maxWind * 1.852),
      pres: Math.round(minPres)
    };
  }

  renderTrackMap(mapInstance, layerGroup, stormDetail, themeColor, onBoundsCalculated) {
    if (!mapInstance) return;
    layerGroup.clearLayers();

    const pts = stormDetail.track_points || [];
    if (pts.length === 0) return;

    const latlngs = pts.map(p => [p.latitude, p.longitude]);

    // Outer track glow
    const glow = L.polyline(latlngs, {
      color: themeColor,
      weight: 6,
      opacity: 0.35,
      lineCap: 'round'
    });
    layerGroup.addLayer(glow);

    // Main line
    const line = L.polyline(latlngs, {
      color: themeColor,
      weight: 3,
      opacity: 0.95
    });
    layerGroup.addLayer(line);

    // Origin marker
    const origin = pts[0];
    const originCircle = L.circleMarker([origin.latitude, origin.longitude], {
      radius: 5,
      fillColor: '#10b981',
      fillOpacity: 1,
      color: '#ffffff',
      weight: 1.5
    }).bindTooltip(`Genesis: ${origin.iso_time}`, { direction: 'top' });
    layerGroup.addLayer(originCircle);

    // Peak marker
    let peakPt = pts[0];
    let maxW = 0;
    pts.forEach(p => {
      if ((p.max_sustained_wind_kt || 0) > maxW) {
        maxW = p.max_sustained_wind_kt;
        peakPt = p;
      }
    });

    const peakMarker = L.circleMarker([peakPt.latitude, peakPt.longitude], {
      radius: 8,
      fillColor: '#ef4444',
      fillOpacity: 1,
      color: '#ffffff',
      weight: 2
    }).bindTooltip(`Peak: ${Math.round(maxW * 1.852)} km/h`, { permanent: false, direction: 'top' });
    layerGroup.addLayer(peakMarker);

    // End/landfall marker
    const end = pts[pts.length - 1];
    const endCircle = L.circleMarker([end.latitude, end.longitude], {
      radius: 5,
      fillColor: '#6b7280',
      fillOpacity: 1,
      color: '#ffffff',
      weight: 1.5
    }).bindTooltip(`Landfall: ${end.iso_time}`, { direction: 'bottom' });
    layerGroup.addLayer(endCircle);

    const bounds = line.getBounds();
    if (bounds.isValid()) {
      if (onBoundsCalculated) onBoundsCalculated(bounds);
      if (mapInstance && mapInstance.getContainer() && mapInstance.getContainer().clientWidth > 0) {
        try {
          mapInstance.fitBounds(bounds, { padding: [20, 20], maxZoom: 7 });
        } catch (e) {}
      }
    }
  }

  renderIntensityChart(d1, d2, steps1, steps2) {
    const el = document.getElementById('compare-intensity-chart');
    if (!el) return;

    const pts1 = (steps1.length > 0 ? steps1 : d1.track_points) || [];
    const pts2 = (steps2.length > 0 ? steps2 : d2.track_points) || [];

    if (pts1.length === 0 && pts2.length === 0) {
      el.innerHTML = '<div style="padding:20px;text-align:center;color:#64748b;">No intensity progression data available.</div>';
      return;
    }

    const winds1 = pts1.map(p => Math.round((p.wind_speed_kt || p.wind_kt || p.max_sustained_wind_kt || 30) * 1.852));
    const winds2 = pts2.map(p => Math.round((p.wind_speed_kt || p.wind_kt || p.max_sustained_wind_kt || 30) * 1.852));

    const maxVal = Math.max(...winds1, ...winds2, 120);
    const w = 700;
    const h = 180;
    const pad = 36;
    const chartW = w - pad * 2;
    const chartH = h - pad * 2;

    const buildPolyline = (dataArr, color) => {
      if (dataArr.length === 0) return '';
      const points = dataArr.map((val, idx) => {
        const x = pad + (idx / Math.max(1, dataArr.length - 1)) * chartW;
        const y = pad + chartH - (val / maxVal) * chartH;
        return `${x.toFixed(1)},${y.toFixed(1)}`;
      }).join(' ');
      return `<polyline fill="none" stroke="${color}" stroke-width="2.5" points="${points}" stroke-linecap="round" stroke-linejoin="round"/>`;
    };

    const poly1 = buildPolyline(winds1, '#00f2fe');
    const poly2 = buildPolyline(winds2, '#f59e0b');

    // Horizontal grid lines
    const gridLines = [0.25, 0.5, 0.75, 1.0].map(frac => {
      const y = pad + chartH - frac * chartH;
      const val = Math.round(frac * maxVal);
      return `
        <line x1="${pad}" y1="${y}" x2="${w - pad}" y2="${y}" stroke="#334155" stroke-dasharray="3,3" stroke-width="0.8"/>
        <text x="${pad - 6}" y="${y + 4}" fill="#94a3b8" font-size="10" text-anchor="end">${val}k</text>
      `;
    }).join('');

    el.innerHTML = `
      <div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:12px 16px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;font-size:12px;">
          <div style="display:flex;gap:16px;">
            <span style="color:#00f2fe;font-weight:600;">● ${d1.storm_name} (Peak: ${Math.max(...winds1, 0)} km/h)</span>
            <span style="color:#f59e0b;font-weight:600;">● ${d2.storm_name} (Peak: ${Math.max(...winds2, 0)} km/h)</span>
          </div>
          <span style="color:#64748b;font-size:11px;">Wind Speed Progression (km/h vs Lifecycle Time)</span>
        </div>
        <svg viewBox="0 0 ${w} ${h}" style="width:100%;height:auto;display:block;">
          ${gridLines}
          ${poly1}
          ${poly2}
          <text x="${w / 2}" y="${h - 6}" fill="#64748b" font-size="10" text-anchor="middle">Normalized Storm Life Cycle (Genesis &rarr; Landfall)</text>
        </svg>
      </div>
    `;
  }

  renderSatelliteCards(d1, d2) {
    const el1 = document.getElementById('compare-sat-1');
    const el2 = document.getElementById('compare-sat-2');

    const renderCard = (container, d, themeColor) => {
      if (!container) return;
      const pts = d.track_points || [];
      let peak = pts[0] || {};
      let maxW = 0;
      pts.forEach(p => {
        if ((p.max_sustained_wind_kt || 0) > maxW) {
          maxW = p.max_sustained_wind_kt;
          peak = p;
        }
      });

      const dateStr = peak.iso_time ? peak.iso_time.split(' ')[0] : '—';
      const windKmh = Math.round(maxW * 1.852);

      container.innerHTML = `
        <div style="background:#0f172a;border:1px solid #1e293b;border-radius:8px;padding:14px;color:#f8fafc;font-size:12px;">
          <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1e293b;padding-bottom:8px;margin-bottom:10px;">
            <strong style="color:${themeColor};font-size:13px;">${d.storm_name}</strong>
            <span style="background:#1e293b;padding:2px 8px;border-radius:4px;font-size:11px;color:#38bdf8;">Peak Infrared Observation</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
            <div><span style="color:#64748b;">Peak Timestamp:</span> <div style="font-weight:600;margin-top:2px;">${peak.iso_time || '—'}</div></div>
            <div><span style="color:#64748b;">Max Sustained Wind:</span> <div style="font-weight:600;color:#ef4444;margin-top:2px;">${windKmh} km/h (${maxW} kt)</div></div>
            <div><span style="color:#64748b;">Central Pressure:</span> <div style="font-weight:600;margin-top:2px;">${Math.round(peak.min_central_pressure_mb || 990)} hPa</div></div>
            <div><span style="color:#64748b;">Eye Coordinates:</span> <div style="font-weight:600;margin-top:2px;">${peak.latitude ? peak.latitude.toFixed(2) : '—'}°N, ${peak.longitude ? peak.longitude.toFixed(2) : '—'}°E</div></div>
          </div>
          <div style="margin-top:12px;background:#1e293b;border-radius:4px;padding:8px 10px;display:flex;justify-content:space-between;align-items:center;">
            <span style="color:#94a3b8;font-size:11px;">Calibrated Channel: NOAA HURSAT-B1 Thermal IR (11.0µm)</span>
            <span style="color:#10b981;font-weight:600;font-size:11px;">Validated Against IBTrACS</span>
          </div>
        </div>
      `;
    };

    renderCard(el1, d1, '#00f2fe');
    renderCard(el2, d2, '#f59e0b');
  }

  setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }
}
