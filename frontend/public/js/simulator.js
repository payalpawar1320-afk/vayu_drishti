/**
 * Impact Shift Simulator UI Controller
 * Implements interactive Scenario Map and parametric simulation per Section 31 of SPEC.md.
 */

import { API } from './api.js';

export class SimulatorController {
  constructor(mapManager, onSimulationResult) {
    this.mapManager = mapManager;
    this.onSimulationResult = onSimulationResult || (() => {});
    this.currentStormId = 'AMPHAN';
    this.debounceTimer = null;
    this.simMap = null;
    this.containerId = 'sim-map';
    this.lastBounds = null;

    this.layers = {
      baseCorridor: L.layerGroup(),
      simCorridor: L.layerGroup(),
      track: L.layerGroup()
    };

    this.initSimMap();
  }

  initSimMap() {
    const el = document.getElementById(this.containerId);
    if (!el) return;

    // Clear placeholder text
    el.innerHTML = '';

    this.simMap = L.map(this.containerId, {
      center: [20.0, 86.5],
      zoom: 6,
      minZoom: 3,
      maxZoom: 14,
      zoomControl: true,
      attributionControl: false
    });

    // Clean Esri Canvas Light Gray Basemap (Free, zero watermark)
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 16 }
    ).addTo(this.simMap);

    // Coastlines & place labels overlay
    L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
      { maxZoom: 16, opacity: 0.85 }
    ).addTo(this.simMap);

    // Add feature layer groups
    Object.values(this.layers).forEach(l => l.addTo(this.simMap));
  }

  invalidateSize() {
    if (this.simMap) {
      setTimeout(() => {
        this.simMap.invalidateSize();
        if (this.lastBounds && this.lastBounds.isValid()) {
          this.simMap.fitBounds(this.lastBounds, { padding: [24, 24], maxZoom: 8 });
        }
      }, 100);
    }
  }

  setStorm(stormId) {
    if (!stormId) return;
    this.currentStormId = stormId;
    const sel = document.getElementById('sim-storm-select');
    if (sel && sel.value !== stormId) {
      const opt = Array.from(sel.options).find(o => o.value === stormId);
      if (opt) sel.value = stormId;
    }
    this.runDefaultScenario();
  }

  runDefaultScenario() {
    const shiftInput = document.getElementById('input-shift-km');
    const intensityInput = document.getElementById('select-intensity-scenario');
    const multInput = document.getElementById('input-corridor-mult');

    const shiftKm = shiftInput ? parseInt(shiftInput.value || '0') : 0;
    const intensity = intensityInput ? intensityInput.value : 'CURRENT';
    const mult = multInput ? parseFloat(multInput.value || '1.0') : 1.0;
    const dir = shiftKm < 0 ? 'WEST' : shiftKm > 0 ? 'EAST' : 'EAST';

    this.runSimulation(dir, Math.abs(shiftKm), intensity, mult);
  }

  resetSimulation() {
    if (this.mapManager) this.mapManager.clearSimulatedCorridor();
    this.layers.simCorridor.clearLayers();
  }

  formatPop(num) {
    if (!num || num === 0) return '0';
    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(0) + 'k';
    return num.toLocaleString();
  }

  async runSimulation(direction, shiftKm, intensity, corridorMultiplier) {
    const stormId = this.currentStormId || 'AMPHAN';

    const payload = {
      storm_id: stormId,
      track_shift_direction: direction || 'EAST',
      track_shift_km: parseFloat(shiftKm) || 0.0,
      intensity_modifier: intensity || 'CURRENT',
      corridor_width_multiplier: parseFloat(corridorMultiplier) || 1.0
    };

    const runBtn = document.getElementById('btn-run-scenario');
    const prevText = runBtn ? runBtn.textContent : '';
    if (runBtn) {
      runBtn.textContent = 'Simulating...';
      runBtn.disabled = true;
    }

    try {
      const res = await API.simulateScenario(payload);
      if (!res) return;

      // 1. Update Scenario Map (#sim-map)
      this.renderScenarioMap(res);

      // 2. Update Main Monitor Map if present
      if (this.mapManager && res.corridor_geojson) {
        this.mapManager.renderSimulatedCorridor(res.corridor_geojson);
      }

      // 3. Update Metrics Grid
      this.updateMetricsUI(res, payload);

      // 4. Notify UI callback
      this.onSimulationResult(res);
    } catch (err) {
      console.error('Simulation error:', err);
    } finally {
      if (runBtn) {
        runBtn.textContent = prevText || 'Run scenario';
        runBtn.disabled = false;
      }
    }
  }

  renderScenarioMap(res) {
    if (!this.simMap) return;

    this.layers.baseCorridor.clearLayers();
    this.layers.simCorridor.clearLayers();

    let allBounds = null;

    // Render Baseline Corridor (Blue dashed)
    if (res.base_corridor_geojson) {
      const baseLayer = L.geoJSON(res.base_corridor_geojson, {
        style: {
          color: '#2563eb',
          weight: 2,
          dashArray: '6, 6',
          fillColor: '#3b82f6',
          fillOpacity: 0.22
        }
      });
      this.layers.baseCorridor.addLayer(baseLayer);
      allBounds = baseLayer.getBounds();
    }

    // Render Shifted Scenario Corridor (Rose / Red dashed)
    if (res.corridor_geojson) {
      const simLayer = L.geoJSON(res.corridor_geojson, {
        style: {
          color: '#e11d48',
          weight: 2.5,
          dashArray: '4, 4',
          fillColor: '#f43f5e',
          fillOpacity: 0.32
        }
      });
      this.layers.simCorridor.addLayer(simLayer);
      if (allBounds) {
        allBounds.extend(simLayer.getBounds());
      } else {
        allBounds = simLayer.getBounds();
      }
    }

    // Center scenario map on affected corridor
    this.lastBounds = allBounds;
    if (allBounds && allBounds.isValid()) {
      this.simMap.fitBounds(allBounds, { padding: [24, 24], maxZoom: 8 });
    }
  }

  updateMetricsUI(res, payload) {
    const baseExp = res.base_exposure || {};
    const simExp = res.simulated_exposure || {};
    const delta = res.exposure_delta || {};

    const basePop = baseExp.estimated_population_exposed || 0;
    const simPop = simExp.estimated_population_exposed || 0;
    const baseDist = baseExp.total_districts_intersected || 0;
    const simDist = simExp.total_districts_intersected || 0;

    const baseInfra = baseExp.critical_infrastructure_counts || {};
    const simInfra = simExp.critical_infrastructure_counts || {};

    // Base values
    const elBaseDist = document.getElementById('base-districts');
    if (elBaseDist) elBaseDist.textContent = `${baseDist} districts`;

    const elBasePop = document.getElementById('base-population');
    if (elBasePop) elBasePop.textContent = `${this.formatPop(basePop)} people`;

    const elBaseInfra = document.getElementById('base-infra');
    if (elBaseInfra) {
      elBaseInfra.textContent = `${baseInfra.major_ports || 0} ports, ${baseInfra.hospitals || 0} hospitals`;
    }

    // Scenario values & deltas
    const distDelta = (delta.districts_count_delta !== undefined)
      ? (delta.districts_count_delta >= 0 ? `+${delta.districts_count_delta}` : `${delta.districts_count_delta}`)
      : '+0';

    const popDeltaPct = (delta.population_percent_change !== undefined)
      ? (delta.population_percent_change >= 0 ? `+${delta.population_percent_change}%` : `${delta.population_percent_change}%`)
      : '+0%';

    const elDeltaDist = document.getElementById('delta-districts');
    if (elDeltaDist) elDeltaDist.textContent = `${simDist} (${distDelta})`;

    const elDeltaPop = document.getElementById('delta-pop');
    if (elDeltaPop) elDeltaPop.textContent = `${this.formatPop(simPop)} (${popDeltaPct})`;

    const elDeltaPorts = document.getElementById('delta-ports');
    if (elDeltaPorts) {
      const portDelta = delta.ports_delta >= 0 ? `+${delta.ports_delta}` : `${delta.ports_delta}`;
      elDeltaPorts.textContent = `${simInfra.major_ports || 0} ports (${portDelta})`;
    }

    // Narrative explanation
    const elExpl = document.getElementById('sim-explanation-text');
    if (elExpl) {
      const added = res.districts_added || [];
      const dropped = res.districts_dropped || [];
      let narrative = '';

      if (payload.track_shift_km === 0) {
        narrative = `Baseline modeled track passes through ${baseDist} coastal districts with ~${this.formatPop(basePop)} population within the immediate risk envelope. Adjust the sliders to simulate path perturbations.`;
      } else {
        narrative = `A simulated track shift of ${payload.track_shift_km} km ${payload.track_shift_direction} `;
        if (added.length > 0) {
          narrative += `brings ${added.length} additional districts into the exposure corridor: <strong>${added.slice(0, 4).join(', ')}${added.length > 4 ? '...' : ''}</strong>. `;
        }
        if (dropped.length > 0) {
          narrative += `${dropped.length} districts (${dropped.slice(0, 3).join(', ')}) fall outside the shifted corridor. `;
        }
        narrative += `Estimated population exposure shifts by <strong>${popDeltaPct}</strong> (${distDelta} districts).`;
      }
      elExpl.innerHTML = narrative;
    }
  }

  debounceRun(direction, shiftKm, intensity, corridorMultiplier) {
    if (this.debounceTimer) clearTimeout(this.debounceTimer);
    this.debounceTimer = setTimeout(() => {
      this.runSimulation(direction, shiftKm, intensity, corridorMultiplier);
    }, 200);
  }
}
