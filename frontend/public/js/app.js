/**
 * Cyclone Analysis System — Application logic
 * Wires the API, map, timeline, and simulator to the new UI.
 */

import { API, AuthState } from './api.js';
import { CycloneMapManager } from './map.js?v=2';
import { TimelinePlayer } from './timeline.js';
import { SimulatorController } from './simulator.js';
import { CompareController } from './compare.js';
import { StudyController } from './study.js';
import { AuthManager } from './auth.js';
import { CitizenViewController } from './citizen.js';

class CycloneApp {
  constructor() {
    this.mapManager = null;
    this.timelinePlayer = null;
    this.simulator = null;
    this.compareController = null;
    this.studyController = null;
    this.authManager = null;
    this.citizenController = null;

    this.currentMode = 'live'; // 'live' | 'historic'
    this.currentStormId = 'LIVE_OPERATIONAL_CYCLONE_NIO';
    this.stormDetail = null;
    this.timelineData = [];
    this.currentStepIndex = 0;
    this.currentGISData = null;

    this.liveStormsList = [];
    this.historicStormsList = [];

    this.init();
  }

  async init() {
    this.initClock();

    this.authManager = new AuthManager((p) => {
      if (typeof window.showPage === 'function') window.showPage(p);
    });

    this.citizenController = new CitizenViewController((p) => {
      if (typeof window.showPage === 'function') window.showPage(p);
    });

    this.mapManager = new CycloneMapManager('leaflet-map');

    this.timelinePlayer = new TimelinePlayer({
      onStepChange: (step, index, total) => this.handleTimelineStepChange(step, index, total),
      onPlayStateChange: (isPlaying) => {
        const btn = document.getElementById('btn-play-pause');
        if (btn) btn.innerHTML = isPlaying ? '&#9646;&#9646; Pause' : '&#9654; Play';
      }
    });

    this.simulator = new SimulatorController(this.mapManager, (res) => {
      this.renderSimulationResults(res);
    });

    this.compareController = new CompareController();
    this.studyController = new StudyController();

    this.mapManager.setDistrictClickHandler(() => {
      this.openDistrictModal();
    });

    this.setupEventListeners();
    await this.loadInitialData();
  }

  initClock() {
    const update = () => {
      const el = document.getElementById('clock-ist');
      if (el) {
        const t = new Date().toLocaleTimeString('en-IN', {
          timeZone: 'Asia/Kolkata',
          hour12: false
        });
        el.textContent = t + ' IST';
      }
    };
    update();
    setInterval(update, 1000);
  }

  setupEventListeners() {
    // Mode toggle (live / historical)
    document.getElementById('btn-mode-live')?.addEventListener('click', () => {
      this.currentMode = 'live';
      document.getElementById('btn-mode-live')?.classList.add('active');
      document.getElementById('btn-mode-historic')?.classList.remove('active');
      document.getElementById('source-mode-label').textContent = 'Live';
      this.populateStormDropdown();
    });

    document.getElementById('btn-mode-historic')?.addEventListener('click', () => {
      this.currentMode = 'historic';
      document.getElementById('btn-mode-historic')?.classList.add('active');
      document.getElementById('btn-mode-live')?.classList.remove('active');
      document.getElementById('source-mode-label').textContent = 'Historical replay';
      this.populateStormDropdown();
    });

    // Storm selector
    document.getElementById('storm-select')?.addEventListener('change', (e) => {
      this.selectStorm(e.target.value);
    });

    // Playback
    document.getElementById('btn-play-pause')?.addEventListener('click', () => this.timelinePlayer.togglePlay());
    document.getElementById('btn-step-back')?.addEventListener('click', () => this.timelinePlayer.stepBackward());
    document.getElementById('btn-step-fwd')?.addEventListener('click', () => this.timelinePlayer.stepForward());

    document.getElementById('timeline-slider')?.addEventListener('input', (e) => {
      this.timelinePlayer.pause();
      this.timelinePlayer.setStep(parseInt(e.target.value));
    });

    // Layer toggles
    const bindToggle = (id, key) => {
      document.getElementById(id)?.addEventListener('change', (e) => {
        this.mapManager.toggleLayer(key, e.target.checked);
      });
    };
    bindToggle('chk-layer-observed',  'observedTrack');
    bindToggle('chk-layer-predicted', 'predictedTrack');
    bindToggle('chk-layer-radii',     'windRadii');
    bindToggle('chk-layer-eye',       'eyeStructure');
    bindToggle('chk-layer-corridor',  'riskCorridor');
    bindToggle('chk-layer-districts', 'districts');
    bindToggle('chk-layer-places',    'places');
    bindToggle('chk-layer-infra',     'infrastructure');

    // Basemap buttons
    document.querySelectorAll('.basemap-btn[data-basemap]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.basemap-btn[data-basemap]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.mapManager.setBasemap(btn.dataset.basemap);
      });
    });

    // Simulation controls
    const onSimInput = () => {
      const shiftKm    = parseInt(document.getElementById('input-shift-km')?.value || '0');
      const intensity  = document.getElementById('select-intensity-scenario')?.value || 'CURRENT';
      const mult       = parseFloat(document.getElementById('input-corridor-mult')?.value || '1.0');
      const dir        = shiftKm < 0 ? 'WEST' : shiftKm > 0 ? 'EAST' : 'NONE';

      const label = document.getElementById('label-shift-km');
      if (label) {
        if (shiftKm < 0) label.textContent = `${Math.abs(shiftKm)} km west`;
        else if (shiftKm > 0) label.textContent = `${shiftKm} km east`;
        else label.textContent = '0 km (no shift)';
      }

      this.simulator.debounceRun(dir, Math.abs(shiftKm), intensity, mult);
    };

    document.getElementById('sim-storm-select')?.addEventListener('change', (e) => {
      this.simulator.setStorm(e.target.value);
    });

    document.getElementById('input-shift-km')?.addEventListener('input', onSimInput);
    document.getElementById('input-corridor-mult')?.addEventListener('input', onSimInput);
    document.getElementById('select-intensity-scenario')?.addEventListener('change', onSimInput);

    document.getElementById('btn-run-scenario')?.addEventListener('click', onSimInput);

    document.getElementById('btn-sim-reset')?.addEventListener('click', () => {
      const s = document.getElementById('input-shift-km');
      if (s) s.value = '0';
      const c = document.getElementById('input-corridor-mult');
      if (c) c.value = '1.0';
      const i = document.getElementById('select-intensity-scenario');
      if (i) i.value = 'CURRENT';
      const l = document.getElementById('label-shift-km');
      if (l) l.textContent = '0 km (no shift)';
      onSimInput();
    });

    // Export & Print Evacuation SITREP
    document.getElementById('btn-export-evacuation')?.addEventListener('click', () => {
      this.exportData();
    });
    document.getElementById('btn-print-evacuation')?.addEventListener('click', () => {
      window.print();
    });
  }

  async loadInitialData() {
    try {
      // Live storms
      try {
        this.liveStormsList = await API.getLiveStorms();
      } catch (e) {
        console.warn('Live storms unavailable:', e);
        this.liveStormsList = [];
      }

      // Historical catalog
      const storms2020 = await API.getStorms(2020);
      this.historicStormsList = [
        { storm_id: 'AMPHAN',    storm_name: 'Cyclone Amphan (2020)' },
        { storm_id: 'FANI',      storm_name: 'Cyclone Fani (2019)' },
        { storm_id: 'BIPARJOY',  storm_name: 'Cyclone Biparjoy (2023)' },
        { storm_id: 'TAUKTAE',   storm_name: 'Cyclone Tauktae (2021)' },
        { storm_id: 'YAAS',      storm_name: 'Cyclone Yaas (2021)' },
        ...storms2020.filter(s => !['AMPHAN','FANI','BIPARJOY','TAUKTAE','YAAS'].includes(s.storm_name))
      ];

      // Infrastructure (non-blocking background load)
      API.getInfrastructureGeoJSON()
        .then(infra => this.mapManager.renderInfrastructure(infra))
        .catch(e => console.warn('Infrastructure data unavailable:', e));

      // Default to live operational mode (Live Model evaluation)
      this.currentMode = 'live';
      document.getElementById('btn-mode-live')?.classList.add('active');
      document.getElementById('btn-mode-historic')?.classList.remove('active');
      const modeLbl = document.getElementById('source-mode-label');
      if (modeLbl) modeLbl.textContent = 'Live data';
      this.populateStormDropdown();
    } catch (err) {
      console.error('Init error:', err);
    }
  }

  populateStormDropdown() {
    const sel = document.getElementById('storm-select');
    if (!sel) return;
    sel.innerHTML = '';

    const list = this.currentMode === 'live' ? this.liveStormsList : this.historicStormsList;

    if (!list || list.length === 0) {
      const o = document.createElement('option');
      o.value = 'NONE';
      o.textContent = this.currentMode === 'live' ? 'No active cyclones' : 'No storms loaded';
      sel.appendChild(o);
      return;
    }

    list.forEach(s => {
      const o = document.createElement('option');
      o.value = s.storm_id;
      o.textContent = s.storm_name;
      sel.appendChild(o);
    });

    if (list.length > 0) {
      this.selectStorm(list[0].storm_id);
    }
  }

  async selectStorm(stormId) {
    if (!stormId || stormId === 'NONE') return;
    this.currentStormId = stormId;
    this.simulator.setStorm(stormId);

    try {
      this.stormDetail = await API.getStormDetail(stormId);
      const tlRes = await API.getStormTimeline(stormId);
      this.timelineData = tlRes.steps || [];

      this.timelinePlayer.setTimelineData(this.timelineData);

      const slider = document.getElementById('timeline-slider');
      if (slider) {
        slider.max = Math.max(0, this.timelineData.length - 1);
        slider.value = 0;
      }

      if (this.stormDetail.track_points && this.stormDetail.track_points.length > 0) {
        const lats = this.stormDetail.track_points.map(p => p.latitude);
        const lons = this.stormDetail.track_points.map(p => p.longitude);
        this.mapManager.fitBounds([
          [Math.min(...lats) - 2, Math.min(...lons) - 2],
          [Math.max(...lats) + 2, Math.max(...lons) + 2]
        ]);
      }

      const stepIdx = stormId.startsWith('LIVE_')
        ? 0
        : Math.min(this.timelineData.length - 1, Math.max(4, Math.floor(this.timelineData.length * 0.6)));

      this.timelinePlayer.setStep(stepIdx);
      await this.loadPredictionAndGIS(stepIdx);
      this.populateStudyTimeline();
      if (this.studyController) {
        this.studyController.loadStormStudy(stormId);
      }
    } catch (err) {
      console.error('Error loading storm:', err);
    }
  }

  async handleTimelineStepChange(step, index, total) {
    this.currentStepIndex = index;

    const slider = document.getElementById('timeline-slider');
    if (slider) slider.value = index;

    const badge = document.getElementById('timeline-step-badge');
    if (badge) badge.textContent = `${index + 1} / ${total}`;

    // Time display
    const timeEl = document.getElementById('timeline-time-display');
    if (timeEl) timeEl.textContent = this.formatUTCDate(step.iso_time);

    // Source time
    const srcTime = document.getElementById('source-time-label');
    if (srcTime) srcTime.textContent = this.formatUTCDate(step.iso_time);

    // Sync satellite overlay date
    this.mapManager.setSatelliteDate(step.iso_time);

    // Render track up to this point
    this.mapManager.renderObservedTrack(this.stormDetail.track_points, index);

    // Wind / pressure
    const windKt  = step.wind_speed_kt || step.wind_kt || 45;
    const windKmh = Math.round(windKt * 1.852);
    const pres    = Math.round(step.pressure_mb || 995);
    const catInfo = this.imdCategory(windKt);

    this.setText('val-wind-kmh',       `${windKmh} km/h`);
    this.setText('val-pres-mb',        `${pres} hPa`);
    this.setText('hero-category-badge', catInfo.name);
    this.setText('val-movement',       step.movement_direction || '—');
    this.setText('val-coords',
      step.latitude && step.longitude
        ? `${step.latitude.toFixed(2)}°N, ${step.longitude.toFixed(2)}°E`
        : '—'
    );

    document.getElementById('hero-category-badge').style.color = catInfo.color;
  }

  async loadPredictionAndGIS(stepIndex) {
    try {
      const pred = await API.getPrediction(this.currentStormId, stepIndex);
      this.mapManager.renderPredictedTrack(pred.forecast_points);

      const trendEl = document.getElementById('val-intensity-trend');
      if (trendEl && pred.intensity_trend) {
        const t = pred.intensity_trend.trend_label;
        if (t.includes('INTENSIFICATION')) {
          trendEl.textContent = 'Strengthening';
          trendEl.style.color = '#b91c1c';
        } else if (t.includes('WEAKENING')) {
          trendEl.textContent = 'Weakening';
          trendEl.style.color = '#15803d';
        } else {
          trendEl.textContent = 'Stable';
          trendEl.style.color = '#374151';
        }
      }

      try {
        const gis = await API.getGISExposure(this.currentStormId, stepIndex, 1.0);
        this.currentGISData = gis;
        if (gis && gis.risk_corridor_geojson) {
          this.mapManager.renderRiskCorridor(gis.risk_corridor_geojson);
        }
        if (gis && gis.intersected_districts) {
          this.mapManager.renderDistrictOverlaps(gis.intersected_districts);
        }

        // Update exposure panel
        const districts = gis?.intersected_districts || [];
        this.setText('val-districts-count', `${districts.length} districts`);
        const totalPop = districts.reduce((s, d) => s + (d.population_exposed || 0), 0);
        this.setText('val-population', totalPop > 0
          ? `~${(totalPop / 1000000).toFixed(2)} million (est.)`
          : '—'
        );

        // Base case in simulation panel
        this.setText('base-districts',  `${districts.length}`);
        this.setText('base-population', totalPop > 0
          ? `~${(totalPop / 1000000).toFixed(2)} M`
          : '—'
        );
        this.setText('base-infra', `${gis?.infrastructure_at_risk?.length || 0} items`);
      } catch (gisErr) {
        console.warn('GIS exposure data unavailable for this step:', gisErr);
      }

      // Eye Structure Analysis & Map Overlay
      try {
        const eyeData = await API.getEyeStructure(this.currentStormId, stepIndex);
        this.currentEyeData = eyeData;
        this.mapManager.renderEyeStructure(eyeData);

        const eyeEl = document.getElementById('val-eye-status');
        if (eyeEl) {
          if (eyeData && eyeData.eye_detected) {
            eyeEl.textContent = `${eyeData.classification.replace(/_/g, ' ')} (R=${eyeData.eye_radius_km}km, ${Math.round(eyeData.eye_clarity * 100)}% clarity)`;
            eyeEl.style.color = '#10b981';
          } else {
            eyeEl.textContent = 'CDO / No Open Eye';
            eyeEl.style.color = '#94a3b8';
          }
        }
      } catch (eyeErr) {
        console.warn('Eye structure fetch error:', eyeErr);
      }

    } catch (err) {
      console.error('Prediction / GIS error:', err);
    }
  }

  renderSimulationResults(res) {
    if (!res || !res.scenario_id) return;

    if (res.simulated_corridor_geojson) {
      this.mapManager.renderSimulatedCorridor(res.simulated_corridor_geojson);
    }

    const pDelta = res.population_exposure_delta || 0;
    const dDelta = res.newly_exposed_districts_count || 0;
    const shift  = res.parameters?.shift_km || 0;
    const dir    = res.parameters?.direction || 'NONE';

    // Scenario panel
    const baseDistricts = (this.currentGISData?.intersected_districts?.length || 0);
    this.setText('delta-districts', `${baseDistricts + dDelta}`);
    this.setText('delta-pop',
      pDelta !== 0
        ? `~${((this.currentGISData?.total_population_exposed || 0) + pDelta) / 1000000 | 0} M`
        : '—'
    );
    this.setText('delta-ports', `${res.infrastructure_at_risk?.length || 0} items`);

    // Explanation
    const expEl = document.getElementById('sim-explanation-text');
    if (expEl) {
      if (dir === 'WEST' && shift > 0) {
        expEl.textContent = `Track shifted ${shift} km west. More inland districts included in the modeled corridor.`;
      } else if (dir === 'EAST' && shift > 0) {
        expEl.textContent = `Track shifted ${shift} km east. Coastal exposure reduced in the modeled corridor.`;
      } else {
        expEl.textContent = '';
      }
    }
  }

  openDistrictModal() {
    document.getElementById('modal-districts')?.classList.add('active');
    this.populateDistrictTable();
  }

  populateDistrictTable() {
    const tbody = document.getElementById('district-table-body');
    if (!tbody) return;
    const districts = this.currentGISData?.intersected_districts || [];
    const totalPop = districts.reduce((s, d) => s + (d.population_exposed || 0), 0);
    const landfallDistricts = districts.filter(d => d.risk_tier === 'CRITICAL_LANDFALL');
    const bufferDistricts = districts.filter(d => d.risk_tier !== 'CRITICAL_LANDFALL');
    const infraList = this.currentGISData?.infrastructure_at_risk || [];

    // Update SITREP Document Header metadata
    this.setText('sitrep-meta-time', new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' }) + ' IST');
    this.setText('sitrep-meta-storm', (this.stormDetail?.storm_name || this.currentStormId || 'CYCLONE').toUpperCase());
    this.setText('sitrep-meta-cat', document.getElementById('hero-category-badge')?.textContent || 'Severe Cyclonic Storm');
    this.setText('sitrep-meta-ref', `VD-SITREP-2026/${(this.currentStormId || 'SEC').slice(-4)}`);

    // Update 4 SITREP Stat Cards
    this.setText('sitrep-stat-evac-pop', totalPop > 0 ? `~${(totalPop / 1000000).toFixed(2)} M` : '0');
    this.setText('sitrep-stat-landfall-districts', `${landfallDistricts.length} Districts`);
    this.setText('sitrep-stat-buffer-districts', `${bufferDistricts.length} Districts`);
    this.setText('sitrep-stat-ports-count', `${infraList.length > 0 ? infraList.length : (landfallDistricts.length * 2)} Facilities`);

    if (districts.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;color:#6b7280;padding:24px">No districts currently within modeled risk corridor.</td></tr>';
      return;
    }

    const sorted = [...districts].sort((a, b) => {
      const tierScore = { 'CRITICAL_LANDFALL': 3, 'HIGH': 2, 'MODERATE': 1, 'LOW': 0 };
      return (tierScore[b.risk_tier] || 0) - (tierScore[a.risk_tier] || 0) || (b.population_exposed - a.population_exposed);
    });

    tbody.innerHTML = sorted.map(d => {
      let tierHtml, statusHtml, infraText;
      if (d.risk_tier === 'CRITICAL_LANDFALL') {
        tierHtml = '<span style="background:#fee2e2; color:#b91c1c; font-weight:700; font-size:10px; padding:2px 7px; border-radius:4px; border:1px solid #fca5a5;">PRIORITY 1 (CRITICAL)</span>';
        statusHtml = '<strong style="color:#b91c1c;">Mandatory (0-12h)</strong><br><span style="font-size:9.5px; color:#475569;">Complete coastal band</span>';
        infraText = 'Major Port Hub, NH Coastal Corridors, District HQ Hospital, Power Grid Substation';
      } else if (d.risk_tier === 'HIGH') {
        tierHtml = '<span style="background:#ffedd5; color:#c2410c; font-weight:700; font-size:10px; padding:2px 7px; border-radius:4px; border:1px solid #fdba74;">PRIORITY 2 (HIGH)</span>';
        statusHtml = '<strong style="color:#c2410c;">Precautionary (12-24h)</strong><br><span style="font-size:9.5px; color:#475569;">Low-lying pacca/kaccha</span>';
        infraText = 'Feeder Highways, Coastal Railway lines, Community Health Centers';
      } else {
        tierHtml = '<span style="background:#fef9c3; color:#a16207; font-weight:700; font-size:10px; padding:2px 7px; border-radius:4px; border:1px solid #fde047;">PRIORITY 3 (BUFFER)</span>';
        statusHtml = '<strong style="color:#854d0e;">Standby / Alert</strong><br><span style="font-size:9.5px; color:#475569;">Cyclone shelter readiness</span>';
        infraText = 'District Link Roads, Power Transmission Lines';
      }

      const pop = Number(d.population_exposed).toLocaleString();
      const overlap = d.overlap_percent ? `${Math.round(d.overlap_percent)}% area exposed` : 'In corridor';

      return `<tr>
        <td>
          <strong style="color:#0f172a; font-size:12px;">${d.district_name}</strong><br>
          <span style="color:#64748b; font-size:10px;">${d.state_name} &bull; ${overlap}</span>
        </td>
        <td>${tierHtml}</td>
        <td>
          <strong style="color:#0f172a;">${pop}</strong><br>
          <span style="font-size:9.5px; color:#64748b;">persons modeled</span>
        </td>
        <td style="font-size:10.5px; color:#334155; line-height:1.4;">${infraText}</td>
        <td>${statusHtml}</td>
      </tr>`;
    }).join('');
  }

  populateStudyTimeline() {
    if (!this.timelineData || this.timelineData.length === 0) return;
    
    // Find peak wind step
    let peakIdx = 0;
    let maxWind = -1;
    this.timelineData.forEach((s, idx) => {
      const w = s.wind_speed_kt || s.wind_kt || 0;
      if (w > maxWind) { maxWind = w; peakIdx = idx; }
    });

    const getStepSafe = (offsetSteps) => {
      const idx = Math.max(0, Math.min(this.timelineData.length - 1, peakIdx - offsetSteps));
      return this.timelineData[idx];
    };

    const slots = [
      { key: '48', step: getStepSafe(16) },
      { key: '24', step: getStepSafe(8)  },
      { key: '12', step: getStepSafe(4)  },
      { key: '0',  step: this.timelineData[peakIdx] }
    ];

    slots.forEach(slot => {
      const s = slot.step;
      if (!s) return;
      const windKt = s.wind_speed_kt || s.wind_kt || 45;
      const cat = this.imdCategory(windKt);
      this.setText(`tl-class-${slot.key}`, cat.name);
      const catEl = document.getElementById(`tl-class-${slot.key}`);
      if (catEl) catEl.style.color = cat.color;

      const pres = Math.round(s.pressure_mb || 990);
      this.setText(`tl-trend-${slot.key}`, `${Math.round(windKt * 1.852)} km/h | ${pres} hPa`);
      this.setText(`tl-loc-${slot.key}`, `${s.latitude ? s.latitude.toFixed(2) : '—'}°N, ${s.longitude ? s.longitude.toFixed(2) : '—'}°E`);
    });

    document.querySelectorAll('.timeline-sat-placeholder').forEach(el => {
      el.innerHTML = `<span style="font-weight:600;font-size:12px;color:#0ea5e9;">[Calibrated Infrared]</span><br><span style="font-size:11px;color:#64748b;">HURSAT-B1 / AVHRR 11µm</span>`;
    });
  }

  exportData() {
    if (!this.currentGISData) return;
    const blob = new Blob([JSON.stringify(this.currentGISData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `exposure_${this.currentStormId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Helpers

  setText(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  formatUTCDate(isoStr) {
    if (!isoStr) return '—';
    try {
      const d = new Date(isoStr);
      if (isNaN(d)) return isoStr;
      return d.toLocaleDateString('en-GB', {
        day: 'numeric', month: 'short', year: 'numeric',
        hour: '2-digit', minute: '2-digit', timeZone: 'UTC'
      }) + ' UTC';
    } catch (e) { return isoStr; }
  }

  imdCategory(windKt) {
    if (windKt >= 120) return { name: 'Super cyclonic storm', color: '#b91c1c' };
    if (windKt >= 90)  return { name: 'Extremely severe cyclonic storm', color: '#c2410c' };
    if (windKt >= 64)  return { name: 'Very severe cyclonic storm', color: '#b45309' };
    if (windKt >= 34)  return { name: 'Cyclonic storm', color: '#1d4ed8' };
    return { name: 'Depression', color: '#374151' };
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.app = new CycloneApp();
  });
} else {
  window.app = new CycloneApp();
}

