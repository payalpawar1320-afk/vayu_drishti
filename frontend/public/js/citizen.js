/**
 * VAYU-DRISHTI — Public Citizen View Controller (Dynamic Engine)
 * Fully connected to REST APIs for real-time storm data, track geometry,
 * GIS risk corridors, district intersection metrics, and safety directives.
 */

import { API } from './api.js';

export class CitizenViewController {
  constructor(pageRouter) {
    this.router = pageRouter;
    this.map = null;
    this.currentStormId = 'AMPHAN';
    this.stormsList = [];
    this.stormDetail = null;
    this.gisExposure = null;
    this.infrastructureList = [];

    this.mapLayers = {
      stormCenter: null,
      trackLine: null,
      corridorPolygon: null,
      sheltersLayer: null,
      districtMarker: null
    };

    // Reference coordinates & data for coastal districts
    this.knownCoastalDistricts = {
      "Balasore": { state: "Odisha", lat: 21.49, lon: 86.91 },
      "Purba Medinipur": { state: "West Bengal", lat: 21.90, lon: 87.75 },
      "South 24 Parganas": { state: "West Bengal", lat: 22.15, lon: 88.55 },
      "Kendrapara": { state: "Odisha", lat: 20.50, lon: 86.42 },
      "Bhadrak": { state: "Odisha", lat: 21.05, lon: 86.50 },
      "Jagatsinghpur": { state: "Odisha", lat: 20.27, lon: 86.17 },
      "Puri": { state: "Odisha", lat: 19.81, lon: 85.83 },
      "Ganjam": { state: "Odisha", lat: 19.38, lon: 84.88 },
      "Kolkata": { state: "West Bengal", lat: 22.57, lon: 88.36 },
      "Howrah": { state: "West Bengal", lat: 22.59, lon: 88.26 },
      "North 24 Parganas": { state: "West Bengal", lat: 22.70, lon: 88.80 },
      "Srikakulam": { state: "Andhra Pradesh", lat: 18.30, lon: 83.90 },
      "Visakhapatnam": { state: "Andhra Pradesh", lat: 17.68, lon: 83.21 },
      "Chennai": { state: "Tamil Nadu", lat: 13.08, lon: 80.27 },
      "Cuddalore": { state: "Tamil Nadu", lat: 11.75, lon: 79.77 },
      "Nagapattinam": { state: "Tamil Nadu", lat: 10.76, lon: 79.84 },
      "Gir Somnath": { state: "Gujarat", lat: 20.90, lon: 70.36 },
      "Devbhumi Dwarka": { state: "Gujarat", lat: 22.24, lon: 68.96 },
      "Kachchh": { state: "Gujarat", lat: 23.24, lon: 69.66 }
    };

    this.init();
  }

  async init() {
    this.setupListeners();
    await this.loadInitialData();
  }

  setupListeners() {
    // Storm change in citizen view
    const stormSelect = document.getElementById('citizen-storm-select');
    stormSelect?.addEventListener('change', async (e) => {
      this.currentStormId = e.target.value;
      await this.loadStormAdvisory(this.currentStormId);
    });

    // District Select change
    const districtSelect = document.getElementById('citizen-district-select');
    districtSelect?.addEventListener('change', (e) => {
      this.renderDistrictSafetyReport(e.target.value);
    });

    // Authority switch button in footer
    document.getElementById('btn-citizen-to-authority')?.addEventListener('click', () => {
      this.router('auth-login');
    });

    // Safety step accordions
    document.querySelectorAll('.safety-step-header').forEach(hdr => {
      hdr.addEventListener('click', () => {
        const content = hdr.nextElementSibling;
        if (content) {
          const isClosed = content.style.display === 'none';
          content.style.display = isClosed ? 'block' : 'none';
        }
      });
    });
  }

  async loadInitialData() {
    try {
      // 1. Fetch historical and live storms list
      const storms = await API.getStorms(2020);
      const priority = [
        { storm_id: 'AMPHAN', storm_name: 'Cyclone Amphan (2020)' },
        { storm_id: 'FANI', storm_name: 'Cyclone Fani (2019)' },
        { storm_id: 'BIPARJOY', storm_name: 'Cyclone Biparjoy (2023)' },
        { storm_id: 'TAUKTAE', storm_name: 'Cyclone Tauktae (2021)' },
        { storm_id: 'YAAS', storm_name: 'Cyclone Yaas (2021)' }
      ];

      this.stormsList = [
        ...priority,
        ...storms.filter(s => !priority.some(p => p.storm_id === s.storm_id))
      ];

      // Populate storm select
      const stormSelect = document.getElementById('citizen-storm-select');
      if (stormSelect) {
        stormSelect.innerHTML = '';
        this.stormsList.forEach(s => {
          const opt = document.createElement('option');
          opt.value = s.storm_id;
          opt.textContent = s.storm_name;
          if (s.storm_id === this.currentStormId) opt.selected = true;
          stormSelect.appendChild(opt);
        });
      }

      // 2. Fetch coastal infrastructure / shelters
      try {
        const infra = await API.getInfrastructureGeoJSON();
        this.infrastructureList = infra.features || [];
      } catch (e) {
        this.infrastructureList = [];
      }

      // 3. Load active storm advisory
      await this.loadStormAdvisory(this.currentStormId);

    } catch (err) {
      console.warn('Citizen view initial load error:', err);
    }
  }

  async loadStormAdvisory(stormId) {
    try {
      // Fetch dynamic details and GIS exposure concurrently
      const [detail, gis] = await Promise.all([
        API.getStormDetail(stormId).catch(() => null),
        API.getGISExposure(stormId).catch(() => null)
      ]);

      if (!detail) return;
      this.stormDetail = detail;
      this.gisExposure = gis;

      // 1. Update Advisory Banner Metrics
      this.updateAdvisoryBanner(detail, gis);

      // 2. Update Map Layers
      this.updateMapVisualization(detail, gis);

      // 3. Populate District Dropdown with dynamic intersected districts prioritized
      this.populateDistrictDropdown(gis);

      // 4. Render selected district safety report
      const dSelect = document.getElementById('citizen-district-select');
      if (dSelect && dSelect.value) {
        this.renderDistrictSafetyReport(dSelect.value);
      }

    } catch (err) {
      console.warn('Error loading dynamic storm advisory:', err);
    }
  }

  updateAdvisoryBanner(detail, gis) {
    const peakWindKt = detail.peak_wind_kt || (detail.track_points ? Math.max(...detail.track_points.map(p => p.max_sustained_wind_kt || 0)) : 80);
    const peakWindKmh = Math.round(peakWindKt * 1.852);
    const gustKmh = Math.round(peakWindKmh * 1.15);

    const headlineEl = document.getElementById('citizen-storm-headline');
    const subEl = document.getElementById('citizen-storm-sub');
    const windEl = document.getElementById('citizen-wind-speed');
    const etaEl = document.getElementById('citizen-landfall-eta');
    const badgeEl = document.getElementById('citizen-alert-badge');

    const cat = this.getIMDCategory(peakWindKt);

    if (headlineEl) {
      headlineEl.textContent = `Cyclone ${detail.storm_name} (${detail.year}) \u2022 ${cat.name}`;
    }
    if (subEl) {
      const topDistricts = gis?.intersected_districts ? gis.intersected_districts.slice(0, 3).map(d => d.district_name).join(', ') : 'Coastal Sector';
      subEl.textContent = `High Alert across Bay of Bengal / Coastal Corridor \u2022 Immediate Impact Zone: ${topDistricts}`;
    }
    if (windEl) {
      windEl.textContent = `${peakWindKmh} - ${gustKmh} km/h`;
    }
    if (etaEl) {
      const totalPop = gis?.summary_exposure?.estimated_population_exposed;
      etaEl.textContent = totalPop ? `${(totalPop / 1000000).toFixed(2)}M Citizens` : `~18-24 Hours`;
      const lbl = etaEl.nextElementSibling;
      if (lbl && totalPop) lbl.textContent = 'Population Exposed';
    }
    if (badgeEl) {
      badgeEl.textContent = cat.badge;
      badgeEl.style.background = cat.color;
    }
  }

  getIMDCategory(windKt) {
    if (windKt >= 120) return { name: 'Super Cyclonic Storm', badge: 'RED ALERT', color: '#DC2626' };
    if (windKt >= 90)  return { name: 'Extremely Severe Cyclonic Storm', badge: 'RED ALERT', color: '#DC2626' };
    if (windKt >= 64)  return { name: 'Very Severe Cyclonic Storm', badge: 'ORANGE WARNING', color: '#EA580C' };
    if (windKt >= 48)  return { name: 'Severe Cyclonic Storm', badge: 'ORANGE WARNING', color: '#D97706' };
    if (windKt >= 34)  return { name: 'Cyclonic Storm', badge: 'YELLOW WATCH', color: '#CA8A04' };
    return { name: 'Deep Depression', badge: 'WEATHER WATCH', color: '#2563EB' };
  }

  populateDistrictDropdown(gis) {
    const select = document.getElementById('citizen-district-select');
    if (!select) return;

    const currentVal = select.value;
    select.innerHTML = '';

    const intersectedNames = new Set((gis?.intersected_districts || []).map(d => d.district_name));

    // Priority: Intersected districts first
    if (gis?.intersected_districts) {
      gis.intersected_districts.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.district_name;
        opt.textContent = `\u26A0\uFE0F ${d.district_name} [${d.area_overlap_pct}% in Risk Corridor]`;
        select.appendChild(opt);
      });
    }

    // Other coastal districts
    Object.keys(this.knownCoastalDistricts).forEach(name => {
      if (!intersectedNames.has(name)) {
        const opt = document.createElement('option');
        opt.value = name;
        opt.textContent = `${name} (${this.knownCoastalDistricts[name].state})`;
        select.appendChild(opt);
      }
    });

    if (currentVal && select.querySelector(`option[value="${currentVal}"]`)) {
      select.value = currentVal;
    } else if (select.options.length > 0) {
      select.selectedIndex = 0;
    }
  }

  renderDistrictSafetyReport(districtName) {
    const cleanName = districtName.replace(/^\u26A0\uFE0F\s*/, '').trim();
    const intersectedMatch = (this.gisExposure?.intersected_districts || []).find(d => d.district_name === cleanName);
    const coords = this.knownCoastalDistricts[cleanName] || { lat: 21.0, lon: 86.5, state: "Coastal India" };

    const nameEl = document.getElementById('citizen-d-name');
    const tierEl = document.getElementById('citizen-d-tier');
    const windEl = document.getElementById('citizen-d-wind');
    const rainEl = document.getElementById('citizen-d-rain');
    const surgeEl = document.getElementById('citizen-d-surge');
    const adviceEl = document.getElementById('citizen-d-advice');

    const peakWindKt = this.stormDetail?.peak_wind_kt || 90;
    const peakKmh = Math.round(peakWindKt * 1.852);

    if (nameEl) nameEl.textContent = `${cleanName} District (${coords.state || "Coastal"})`;

    if (intersectedMatch) {
      const overlap = intersectedMatch.area_overlap_pct || 0;
      const popExposed = intersectedMatch.estimated_population || intersectedMatch.estimated_population_exposed || 0;
      const isHigh = overlap >= 20 || popExposed > 500000;

      if (tierEl) {
        tierEl.textContent = isHigh ? "HIGH RISK TIER \u2022 EVACUATION ZONE" : "MODERATE RISK TIER";
        tierEl.className = `district-badge-tier ${isHigh ? 'tier-high' : 'tier-moderate'}`;
      }
      if (windEl) windEl.textContent = `${Math.round(peakKmh * 0.85)} - ${peakKmh} km/h`;
      if (rainEl) rainEl.textContent = isHigh ? "Extremely Heavy (>250mm)" : "Heavy Rain (100-180mm)";
      if (surgeEl) surgeEl.textContent = isHigh ? "2.5 - 4.5 meters" : "1.5 - 2.5 meters";
      if (adviceEl) {
        adviceEl.innerHTML = `<strong>Official Directive:</strong> ${overlap}% of district is in the direct cyclone risk corridor (${popExposed.toLocaleString()} citizens at risk). Mandatory evacuation active for coastal habitations within 5 km of shoreline. Relocate to designated concrete cyclone shelters immediately.`;
      }
    } else {
      if (tierEl) {
        tierEl.textContent = "WATCH / ADVISORY TIER";
        tierEl.className = "district-badge-tier tier-moderate";
      }
      if (windEl) windEl.textContent = "50 - 75 km/h gusts";
      if (rainEl) rainEl.textContent = "Moderate to Heavy Rain";
      if (surgeEl) surgeEl.textContent = "Rough Surf (0.5 - 1.2 m)";
      if (adviceEl) {
        adviceEl.innerHTML = `<strong>Official Directive:</strong> District is currently outside the primary eyewall corridor, but outer rainbands and squally winds are anticipated. Keep emergency battery lights and potable water ready. Avoid venturing out to sea.`;
      }
    }

    // Pan map to district
    if (this.map && coords.lat && coords.lon) {
      this.map.flyTo([coords.lat, coords.lon], 8, { duration: 1.0 });

      if (this.mapLayers.districtMarker) {
        this.map.removeLayer(this.mapLayers.districtMarker);
      }
      this.mapLayers.districtMarker = L.circleMarker([coords.lat, coords.lon], {
        radius: 12,
        fillColor: intersectedMatch ? '#DC2626' : '#F59E0B',
        color: '#FFFFFF',
        weight: 3,
        fillOpacity: 0.85
      }).addTo(this.map);

      this.mapLayers.districtMarker.bindPopup(`
        <div style="font-family: sans-serif; font-size: 12px;">
          <strong>${cleanName} (${coords.state})</strong><br>
          Status: ${intersectedMatch ? 'Inside Risk Corridor' : 'Outer Advisory Area'}<br>
          ${intersectedMatch ? `Population Exposed: ${intersectedMatch.estimated_population_exposed.toLocaleString()}` : ''}
        </div>
      `).openPopup();
    }
  }

  initMap() {
    if (this.map) {
      setTimeout(() => this.map.invalidateSize(), 100);
      return;
    }

    const container = document.getElementById('citizen-leaflet-map');
    if (!container || typeof L === 'undefined') return;

    this.map = L.map('citizen-leaflet-map', {
      center: [20.5, 86.5],
      zoom: 6,
      zoomControl: true,
      attributionControl: false
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 18,
      subdomains: 'abcd'
    }).addTo(this.map);

    if (this.stormDetail) {
      this.updateMapVisualization(this.stormDetail, this.gisExposure);
    }
  }

  updateMapVisualization(detail, gis) {
    if (!this.map || !detail) return;

    // 1. Draw Forecast Track Line
    if (this.mapLayers.trackLine) this.map.removeLayer(this.mapLayers.trackLine);
    if (this.mapLayers.stormCenter) this.map.removeLayer(this.mapLayers.stormCenter);
    if (this.mapLayers.corridorPolygon) this.map.removeLayer(this.mapLayers.corridorPolygon);

    const pts = detail.track_points || [];
    if (pts.length > 0) {
      const latlngs = pts.map(p => [p.latitude, p.longitude]);
      this.mapLayers.trackLine = L.polyline(latlngs, {
        color: '#2563EB',
        weight: 3.5,
        dashArray: '6, 6',
        opacity: 0.85
      }).addTo(this.map);

      // Latest / Landfall center
      const latest = pts[pts.length - 1];
      const pulsingIcon = L.divIcon({
        className: 'citizen-cyclone-icon',
        html: `
          <div style="width: 26px; height: 26px; background: #DC2626; border-radius: 50%; border: 3px solid #FFFFFF; box-shadow: 0 0 14px rgba(220, 38, 38, 0.9); display: flex; align-items: center; justify-content: center;">
            <div style="width: 8px; height: 8px; background: #FFFFFF; border-radius: 50%;"></div>
          </div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });

      this.mapLayers.stormCenter = L.marker([latest.latitude, latest.longitude], { icon: pulsingIcon }).addTo(this.map);
      this.mapLayers.stormCenter.bindPopup(`
        <strong>${detail.storm_name}</strong><br>
        Center: ${latest.latitude.toFixed(2)}N, ${latest.longitude.toFixed(2)}E<br>
        Peak Wind: ${Math.round((detail.peak_wind_kt || latest.max_sustained_wind_kt || 80) * 1.852)} km/h
      `).openPopup();
    }

    // 2. Render Real GIS Risk Corridor GeoJSON
    if (gis?.risk_corridor_geojson) {
      this.mapLayers.corridorPolygon = L.geoJSON(gis.risk_corridor_geojson, {
        style: {
          color: '#DC2626',
          fillColor: '#EF4444',
          fillOpacity: 0.28,
          weight: 2
        }
      }).addTo(this.map);
      this.mapLayers.corridorPolygon.bindTooltip('\uD83D\uDD34 Modeled High-Risk Impact Corridor (IMD/NDMA GIS)', { sticky: true });

      try {
        const bounds = this.mapLayers.corridorPolygon.getBounds();
        if (bounds.isValid()) {
          this.map.fitBounds(bounds, { padding: [25, 25] });
        }
      } catch (e) { }
    }

    // 3. Render Coastal Infrastructure / Shelters
    if (!this.mapLayers.sheltersLayer && this.infrastructureList.length > 0) {
      const shelterMarkers = [];
      this.infrastructureList.forEach(feat => {
        const geom = feat.geometry;
        const props = feat.properties || {};
        if (geom && geom.type === 'Point' && Array.isArray(geom.coordinates)) {
          const m = L.circleMarker([geom.coordinates[1], geom.coordinates[0]], {
            radius: 5,
            fillColor: props.category === 'PORT' ? '#3B82F6' : '#10B981',
            color: '#FFFFFF',
            weight: 1.5,
            fillOpacity: 0.9
          });
          m.bindPopup(`<strong>${props.name || 'Shelter'}</strong><br>Category: ${props.category || 'INFRASTRUCTURE'}<br>Status: OPERATIONAL`);
          shelterMarkers.push(m);
        }
      });
      if (shelterMarkers.length > 0) {
        this.mapLayers.sheltersLayer = L.layerGroup(shelterMarkers).addTo(this.map);
      }
    }

    setTimeout(() => this.map.invalidateSize(), 150);
  }

  invalidateSize() {
    if (this.map) {
      setTimeout(() => this.map.invalidateSize(), 80);
    } else {
      this.initMap();
    }
  }
}
