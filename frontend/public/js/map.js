/**
 * Leaflet GIS Mapping Manager - Professional Tactical Weather Platform
 * Supports NASA GIBS real satellite imagery, multi-tier risk corridors,
 * live cyclone tracking, and scenario simulation.
 */

export class CycloneMapManager {
  constructor(mapContainerId = 'leaflet-map') {
    this.containerId = mapContainerId;
    this.map = null;
    this.currentDate = '2020-05-18';
    this.activeBasemapMode = 'nasa-truecolor'; // Default to real NASA satellite
    
    // Basemap tile layers
    this.basemaps = {};

    // Feature Layer Groups
    this.layers = {
      observedTrack: L.layerGroup(),
      predictedTrack: L.layerGroup(),
      riskCorridor: L.layerGroup(),
      simulatedCorridor: L.layerGroup(),
      districts: L.layerGroup(),
      infrastructure: L.layerGroup(),
      stormMarker: L.layerGroup(),
      windRadii: L.layerGroup(),
      places: L.layerGroup(),
      eyeStructure: L.layerGroup()
    };

    this.onDistrictClickCallback = null;
    this.initMap();
  }

  initMap() {
    this.map = L.map(this.containerId, {
      center: [17.5, 85.0],
      zoom: 5,
      minZoom: 3,
      maxZoom: 14,
      zoomControl: false, // We'll position custom zoom control
      attributionControl: true
    });

    // Custom top-right zoom control
    L.control.zoom({ position: 'bottomright' }).addTo(this.map);

    this.satelliteTileLayers = {};

    // 1. Esri High-Resolution World Imagery (Full planetary textures, deep blue oceans, zero blank gaps)
    const makeSatelliteCanvas = () => L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      {
        maxZoom: 18,
        attribution: 'Source: Esri, Maxar, Earthstar Geographics'
      }
    );
    this.basemaps['esri-sat'] = makeSatelliteCanvas();

    // 2. Carto Voyager (Vivid, crystal-clear geographical map with oceans, cities & terrain)
    this.basemaps['voyager'] = L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
      {
        maxZoom: 18,
        subdomains: 'abcd',
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; OpenStreetMap'
      }
    );

    // 3. Clean Light Grey Basemap
    this.basemaps['light-grey'] = this.basemaps['voyager'];

    // 4. NASA GIBS MODIS True-Color Real Satellite Layer (backed by Esri Imagery so never blackout)
    this.satelliteTileLayers['nasa-truecolor'] = L.tileLayer(
      'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg',
      {
        date: this.currentDate,
        maxNativeZoom: 9,
        maxZoom: 16,
        attribution: 'Real Satellite: NASA EOSDIS GIBS (MODIS Terra 250m)'
      }
    );
    this.basemaps['nasa-truecolor'] = L.layerGroup([makeSatelliteCanvas(), this.satelliteTileLayers['nasa-truecolor']]);

    // 5. NASA GIBS VIIRS True-Color
    this.satelliteTileLayers['nasa-viirs'] = L.tileLayer(
      'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/{date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg',
      {
        date: this.currentDate,
        maxNativeZoom: 9,
        maxZoom: 16,
        attribution: 'Real Satellite: NASA EOSDIS GIBS (Suomi NPP VIIRS)'
      }
    );
    this.basemaps['nasa-viirs'] = L.layerGroup([makeSatelliteCanvas(), this.satelliteTileLayers['nasa-viirs']]);

    // 6. NASA Shortwave Infrared / False Color
    this.satelliteTileLayers['nasa-ir'] = L.tileLayer(
      'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_Bands721/default/{date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg',
      {
        date: this.currentDate,
        maxNativeZoom: 9,
        maxZoom: 16,
        opacity: 0.95,
        attribution: 'NASA GIBS Infrared / False Color (MODIS Bands 7-2-1)'
      }
    );
    this.basemaps['nasa-ir'] = L.layerGroup([makeSatelliteCanvas(), this.satelliteTileLayers['nasa-ir']]);

    // 7. Tactical Dark Canvas Basemap
    this.basemaps['dark'] = L.tileLayer(
      'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
      { maxZoom: 18, subdomains: 'abcd', attribution: '&copy; CARTO' }
    );

    // Reference boundary overlay (countries & coastlines) - crisp, no watermark
    this.bordersLayer = L.tileLayer(
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}',
      {
        maxZoom: 16,
        opacity: 0.9,
        zIndex: 500
      }
    ).addTo(this.map);

    // Default to clean, beautiful Carto Voyager / Light Grey basemap
    this.activeBasemapMode = 'light-grey';
    this.basemaps[this.activeBasemapMode].addTo(this.map);

    // Add feature layer groups
    Object.values(this.layers).forEach(layer => layer.addTo(this.map));

    // Render prominent coastal city and place names
    this.initCoastalPlaceMarkers();
  }

  setBasemap(mode) {
    if (!this.basemaps[mode] || mode === this.activeBasemapMode) return;
    this.map.removeLayer(this.basemaps[this.activeBasemapMode]);
    this.activeBasemapMode = mode;
    this.basemaps[mode].addTo(this.map);
    this.basemaps[mode].bringToBack();
  }

  setSatelliteDate(dateIso) {
    if (!dateIso) return;
    // Extract YYYY-MM-DD
    const match = dateIso.match(/\d{4}-\d{2}-\d{2}/);
    const dateStr = match ? match[0] : new Date().toISOString().slice(0, 10);
    this.currentDate = dateStr;

    const templates = {
      'nasa-truecolor': 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/{date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg',
      'nasa-viirs': 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/VIIRS_SNPP_CorrectedReflectance_TrueColor/default/{date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg',
      'nasa-ir': 'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_Bands721/default/{date}/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg'
    };

    Object.keys(templates).forEach(key => {
      const tileLayer = this.satelliteTileLayers[key];
      if (tileLayer) {
        tileLayer.options.date = dateStr;
        tileLayer.setUrl(templates[key].replace('{date}', dateStr));
      }
    });
  }

  setDistrictClickHandler(cb) {
    this.onDistrictClickCallback = cb;
  }

  /**
   * Renders the observed historical or live track.
   */
  renderObservedTrack(trackPoints, currentStepIndex = null) {
    this.layers.observedTrack.clearLayers();
    this.layers.windRadii.clearLayers();
    if (!trackPoints || trackPoints.length === 0) return;

    const visiblePoints = currentStepIndex !== null 
      ? trackPoints.slice(0, currentStepIndex + 1)
      : trackPoints;

    const latlngs = visiblePoints.map(p => [p.latitude, p.longitude]);

    // Outer glow polyline
    const glowLine = L.polyline(latlngs, {
      color: '#00f2fe',
      weight: 6,
      opacity: 0.35,
      lineCap: 'round'
    });
    this.layers.observedTrack.addLayer(glowLine);

    // Core solid polyline
    const polyline = L.polyline(latlngs, {
      color: '#38bdf8',
      weight: 3.5,
      opacity: 0.95,
      lineCap: 'round'
    });
    this.layers.observedTrack.addLayer(polyline);

    // Track points
    visiblePoints.forEach((p, idx) => {
      const isLatest = idx === visiblePoints.length - 1;
      const marker = L.circleMarker([p.latitude, p.longitude], {
        radius: isLatest ? 7 : 4,
        color: isLatest ? '#ffffff' : '#0284c7',
        fillColor: isLatest ? '#38bdf8' : '#0369a1',
        fillOpacity: 0.95,
        weight: isLatest ? 2.5 : 1
      });

      marker.bindTooltip(`
        <div style="font-family: inherit; font-size: 11px;">
          <strong style="color: #38bdf8;">CYCLONE OBSERVATION</strong><br>
          <span style="color: #94a3b8;">Time:</span> ${p.iso_time}<br>
          <span style="color: #fbbf24;">Wind:</span> ${p.max_sustained_wind_kt || 'N/A'} kt &nbsp;|&nbsp; 
          <span style="color: #94a3b8;">Pres:</span> ${p.min_central_pressure_mb || 'N/A'} mb<br>
          <span style="color: #e2e8f0;">Coords:</span> ${p.latitude.toFixed(2)}°N, ${p.longitude.toFixed(2)}°E
        </div>
      `, { className: 'custom-leaflet-tooltip' });

      this.layers.observedTrack.addLayer(marker);
    });

    const activePoint = visiblePoints[visiblePoints.length - 1];
    this.updateCurrentPositionMarker(activePoint);
    this.renderWindRadii(activePoint);
  }

  /**
   * Renders simulated 34kt, 50kt, and 64kt gale/storm wind radius rings around the eye.
   */
  renderWindRadii(point) {
    this.layers.windRadii.clearLayers();
    if (!point || !point.max_sustained_wind_kt) return;

    const wind = point.max_sustained_wind_kt;
    
    // Scale radii in meters based on wind intensity
    const r34 = Math.min(320000, Math.max(100000, wind * 2400));
    const r50 = wind >= 50 ? Math.min(220000, Math.max(60000, wind * 1600)) : 0;
    const r64 = wind >= 64 ? Math.min(130000, Math.max(30000, wind * 1000)) : 0;

    // 34-knot Gale Radius ring
    const ring34 = L.circle([point.latitude, point.longitude], {
      radius: r34,
      color: '#38bdf8',
      weight: 1.5,
      dashArray: '3, 4',
      fillColor: '#38bdf8',
      fillOpacity: 0.06
    });
    ring34.bindTooltip(`34-kt Gale Wind Radius (${Math.round(r34/1000)} km)`);
    this.layers.windRadii.addLayer(ring34);

    // 50-knot Storm Radius ring
    if (r50 > 0) {
      const ring50 = L.circle([point.latitude, point.longitude], {
        radius: r50,
        color: '#fbbf24',
        weight: 1.5,
        dashArray: '3, 4',
        fillColor: '#fbbf24',
        fillOpacity: 0.08
      });
      ring50.bindTooltip(`50-kt Storm Wind Radius (${Math.round(r50/1000)} km)`);
      this.layers.windRadii.addLayer(ring50);
    }

    // 64-knot Hurricane Radius ring
    if (r64 > 0) {
      const ring64 = L.circle([point.latitude, point.longitude], {
        radius: r64,
        color: '#ef4444',
        weight: 2,
        fillColor: '#ef4444',
        fillOpacity: 0.12
      });
      ring64.bindTooltip(`64-kt Hurricane Core Radius (${Math.round(r64/1000)} km)`);
      this.layers.windRadii.addLayer(ring64);
    }
  }

  /**
   * Renders high-precision vortex eye, convective eyewall ring, and CDO cloud shield.
   */
  renderEyeStructure(eyeData) {
    this.layers.eyeStructure.clearLayers();
    if (!eyeData || !eyeData.eye_center) return;

    const { eye_center, eye_radius_km, eyewall_radius_km, cdo_radius_km, eye_detected, eye_clarity, cdo_min_temp_c, classification, description, eyewall_intensity_kt } = eyeData;
    const center = [eye_center.lat, eye_center.lon];

    // 1. Central Dense Overcast (CDO) Cloud Shield
    if (cdo_radius_km > 0) {
      const cdoCircle = L.circle(center, {
        radius: cdo_radius_km * 1000,
        color: '#6366f1',
        weight: 1.5,
        dashArray: '4, 4',
        fillColor: '#818cf8',
        fillOpacity: 0.10
      });
      cdoCircle.bindTooltip(`
        <div style="font-size:11px;">
          <strong style="color:#818cf8;">CDO Cloud Shield Envelope</strong><br>
          Radius: ~${cdo_radius_km} km | Cloud-top Min: ${cdo_min_temp_c}°C
        </div>
      `, { className: 'custom-leaflet-tooltip' });
      this.layers.eyeStructure.addLayer(cdoCircle);
    }

    // 2. Convective Eyewall Ring (Radius of Maximum Wind - RMW)
    if (eyewall_radius_km > 0) {
      const eyewallCircle = L.circle(center, {
        radius: eyewall_radius_km * 1000,
        color: '#f43f5e',
        weight: 2.5,
        dashArray: eye_detected ? '3, 4' : '6, 6',
        fillColor: '#fb7185',
        fillOpacity: 0.18
      });
      eyewallCircle.bindTooltip(`
        <div style="font-size:11px;">
          <strong style="color:#f43f5e;">Convective Eyewall (RMW)</strong><br>
          Radius: ~${eyewall_radius_km} km | Peak Winds: ${eyewall_intensity_kt} kt
        </div>
      `, { className: 'custom-leaflet-tooltip' });
      this.layers.eyeStructure.addLayer(eyewallCircle);
    }

    // 3. Inner Vortex Calm Eye Cavity (if eye detected)
    if (eye_detected && eye_radius_km > 0) {
      const eyeCircle = L.circle(center, {
        radius: eye_radius_km * 1000,
        color: '#10b981',
        weight: 2.2,
        fillColor: '#10b981',
        fillOpacity: 0.28
      });

      // Distinct vortex eye center reticle marker
      const eyeReticle = L.circleMarker(center, {
        radius: 6,
        color: '#10b981',
        fillColor: '#ffffff',
        fillOpacity: 1.0,
        weight: 3
      });

      const eyeTooltipHtml = `
        <div style="font-family: inherit; font-size: 11px; min-width: 220px; line-height: 1.5;">
          <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid rgba(255,255,255,0.15); padding-bottom: 4px; margin-bottom: 6px;">
            <strong style="color: #10b981; font-size: 12px;">👁️ VORTEX EYE STRUCTURE</strong>
            <span style="font-size: 10px; background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 1px 6px; border-radius: 4px; font-weight: bold;">${classification}</span>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 10.5px;">
            <div><span style="color: #94a3b8;">Eye Radius:</span> <strong>${eye_radius_km} km</strong></div>
            <div><span style="color: #94a3b8;">Eyewall (RMW):</span> <strong>${eyewall_radius_km} km</strong></div>
            <div><span style="color: #94a3b8;">Eye Clarity:</span> <strong>${Math.round(eye_clarity * 100)}%</strong></div>
            <div><span style="color: #94a3b8;">CDO Cold Core:</span> <strong>${cdo_min_temp_c}°C</strong></div>
          </div>
          <p style="margin: 6px 0 0 0; font-size: 10px; color: #cbd5e1; font-style: italic;">${description}</p>
        </div>
      `;

      eyeCircle.bindTooltip(eyeTooltipHtml, { className: 'custom-leaflet-tooltip' });
      eyeReticle.bindTooltip(eyeTooltipHtml, { className: 'custom-leaflet-tooltip' });

      this.layers.eyeStructure.addLayer(eyeCircle);
      this.layers.eyeStructure.addLayer(eyeReticle);
    }
  }

  clearEyeStructure() {
    this.layers.eyeStructure.clearLayers();
  }


  /**
   * Renders the forecasted track with AI uncertainty halos.
   */
  renderPredictedTrack(forecastPoints) {
    this.layers.predictedTrack.clearLayers();
    if (!forecastPoints || forecastPoints.length === 0) return;

    const latlngs = forecastPoints.map(p => [p.latitude, p.longitude]);

    // Dashed predicted track line
    const polyline = L.polyline(latlngs, {
      color: '#fbbf24',
      weight: 3.5,
      opacity: 0.95,
      dashArray: '6, 6'
    });
    this.layers.predictedTrack.addLayer(polyline);

    // Forecast positions markers & uncertainty disks
    forecastPoints.forEach(p => {
      // Uncertainty circle
      if (p.uncertainty_radius_km) {
        const uCircle = L.circle([p.latitude, p.longitude], {
          radius: p.uncertainty_radius_km * 1000,
          color: '#fbbf24',
          weight: 1,
          dashArray: '2, 3',
          fillColor: '#f59e0b',
          fillOpacity: 0.08
        });
        this.layers.predictedTrack.addLayer(uCircle);
      }

      const marker = L.circleMarker([p.latitude, p.longitude], {
        radius: 6,
        color: '#ffffff',
        fillColor: '#fbbf24',
        fillOpacity: 1.0,
        weight: 2
      });

      marker.bindTooltip(`
        <div style="font-family: inherit; font-size: 11px;">
          <strong style="color: #fbbf24;">AI MULTI-HORIZON FORECAST (+${p.horizon_hours}h)</strong><br>
          <span style="color: #94a3b8;">Valid:</span> ${p.forecast_time}<br>
          <span style="color: #e2e8f0;">Lat/Lon:</span> ${p.latitude.toFixed(2)}°N, ${p.longitude.toFixed(2)}°E<br>
          <span style="color: #a855f7;">Uncertainty:</span> ±${p.uncertainty_radius_km} km (95% CI)
        </div>
      `, { className: 'custom-leaflet-tooltip' });

      this.layers.predictedTrack.addLayer(marker);
    });
  }

  /**
   * Renders Modeled Risk Corridor GeoJSON Polygon.
   */
  renderRiskCorridor(corridorGeoJson) {
    this.layers.riskCorridor.clearLayers();
    if (!corridorGeoJson) return;

    const layer = L.geoJSON(corridorGeoJson, {
      style: {
        color: '#818cf8',
        weight: 2.5,
        dashArray: '5, 5',
        fillColor: '#6366f1',
        fillOpacity: 0.22
      },
      onEachFeature: (feature, l) => {
        l.bindTooltip(`
          <div style="font-size: 11px;">
            <strong style="color: #818cf8;">MODELED RISK CORRIDOR</strong><br>
            <span>Envelope Area: ${Number(feature.properties?.corridor_area_sq_km || 0).toLocaleString()} km²</span>
          </div>
        `, { className: 'custom-leaflet-tooltip' });
      }
    });

    this.layers.riskCorridor.addLayer(layer);
  }

  /**
   * Renders Simulated Scenario Corridor (Rose polygon).
   */
  renderSimulatedCorridor(simulatedCorridorGeoJson) {
    this.layers.simulatedCorridor.clearLayers();
    if (!simulatedCorridorGeoJson) return;

    const layer = L.geoJSON(simulatedCorridorGeoJson, {
      style: {
        color: '#f43f5e',
        weight: 3,
        dashArray: '6, 6',
        fillColor: '#e11d48',
        fillOpacity: 0.28
      },
      onEachFeature: (feature, l) => {
        l.bindTooltip(`
          <div style="font-size: 11px;">
            <strong style="color: #f43f5e;">SIMULATED WHAT-IF CORRIDOR</strong><br>
            <span>Shift: ${feature.properties?.shift_km || 0} km ${feature.properties?.direction || ''}</span>
          </div>
        `, { className: 'custom-leaflet-tooltip' });
      }
    });

    this.layers.simulatedCorridor.addLayer(layer);
  }

  clearSimulatedCorridor() {
    this.layers.simulatedCorridor.clearLayers();
  }

  /**
   * Highlights districts overlapping with the modeled corridor.
   */
  renderDistrictOverlaps(intersectedDistricts) {
    this.layers.districts.clearLayers();
    if (!intersectedDistricts || intersectedDistricts.length === 0) return;

    const overlapMap = new Map();
    intersectedDistricts.forEach(d => overlapMap.set(d.district_name, d));

    fetch('/api/v1/gis/districts')
      .then(res => res.json())
      .then(geoJson => {
        const matchingFeatures = geoJson.features.filter(f => 
          overlapMap.has(f.properties.district_name)
        );

        const districtLayer = L.geoJSON({ type: 'FeatureCollection', features: matchingFeatures }, {
          style: (feature) => {
            const data = overlapMap.get(feature.properties.district_name);
            const tier = data ? data.risk_tier : 'LOW';
            let strokeColor = '#38bdf8';
            let fillColor = '#0284c7';
            let fillOpacity = 0.35;

            if (tier === 'CRITICAL_LANDFALL') {
              strokeColor = '#ef4444';
              fillColor = '#dc2626';
              fillOpacity = 0.55;
            } else if (tier === 'HIGH') {
              strokeColor = '#f97316';
              fillColor = '#ea580c';
              fillOpacity = 0.45;
            } else if (tier === 'MODERATE') {
              strokeColor = '#eab308';
              fillColor = '#ca8a04';
              fillOpacity = 0.35;
            }

            return {
              color: strokeColor,
              weight: 2,
              fillColor: fillColor,
              fillOpacity: fillOpacity
            };
          },
          onEachFeature: (feature, layer) => {
            const data = overlapMap.get(feature.properties.district_name);
            if (!data) return;

            layer.bindTooltip(`
              <div style="font-family: inherit; font-size: 11px; min-width: 170px;">
                <strong style="color: #fff; font-size: 13px;">${data.district_name}</strong> (${data.state_name})<br>
                <div style="margin: 4px 0; padding: 2px 6px; border-radius: 4px; display: inline-block; font-weight: 700; font-size: 10px; background: ${data.risk_tier === 'CRITICAL_LANDFALL' ? '#ef4444' : data.risk_tier === 'HIGH' ? '#f97316' : '#eab308'}; color: #fff;">
                  ${data.risk_tier}
                </div><br>
                <span>Estimated Exposed Pop: <strong>${Number(data.population_exposed).toLocaleString()}</strong></span><br>
                <span>Corridor Area Overlap: <strong>${data.overlap_percent.toFixed(1)}%</strong></span>
              </div>
            `, { className: 'custom-leaflet-tooltip' });

            layer.on('click', () => {
              if (this.onDistrictClickCallback) {
                this.onDistrictClickCallback(data);
              }
            });
          }
        });

        this.layers.districts.addLayer(districtLayer);
      })
      .catch(err => console.error('Error fetching district geojson for overlap rendering:', err));
  }

  /**
   * Renders critical coastal infrastructure on map.
   */
  renderInfrastructure(infraGeoJson) {
    this.layers.infrastructure.clearLayers();
    if (!infraGeoJson || !infraGeoJson.features) return;

    const infraLayer = L.geoJSON(infraGeoJson, {
      pointToLayer: (feature, latlng) => {
        const type = feature.properties.type;
        let color = '#38bdf8';
        let iconHtml = '⚓';
        if (type === 'AIRPORT') { color = '#a855f7'; iconHtml = '✈'; }
        if (type === 'HOSPITAL') { color = '#ef4444'; iconHtml = '+'; }

        const icon = L.divIcon({
          className: 'custom-infra-icon',
          html: `<div style="background: ${color}; width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: bold; color: #fff; border: 2px solid #fff; box-shadow: 0 0 8px ${color};">${iconHtml}</div>`,
          iconSize: [22, 22],
          iconAnchor: [11, 11]
        });

        const marker = L.marker(latlng, { icon });
        marker.bindTooltip(`
          <div style="font-size: 11px;">
            <strong style="color: ${color};">${feature.properties.name}</strong><br>
            <span>Type: ${type}</span><br>
            <span>Location: ${feature.properties.district}, ${feature.properties.state}</span>
          </div>
        `, { className: 'custom-leaflet-tooltip' });

        return marker;
      }
    });

    this.layers.infrastructure.addLayer(infraLayer);
  }

  /**
   * Updates the pulsating eye of the storm marker.
   */
  updateCurrentPositionMarker(point) {
    this.layers.stormMarker.clearLayers();
    if (!point) return;

    const pulsingIcon = L.divIcon({
      className: 'pulsing-cyclone-icon',
      html: `
        <div class="cyclone-beacon">
          <div class="cyclone-ring ring1"></div>
          <div class="cyclone-ring ring2"></div>
          <div class="cyclone-center-eye"></div>
        </div>
      `,
      iconSize: [44, 44],
      iconAnchor: [22, 22]
    });

    const marker = L.marker([point.latitude, point.longitude], { icon: pulsingIcon });
    marker.bindTooltip(`
      <div style="font-size: 12px; font-weight: 700; color: #38bdf8;">
        CURRENT POSITION (T₀)<br>
        <span style="font-size: 11px; font-weight: 400; color: #e2e8f0;">
          ${point.latitude.toFixed(2)}°N, ${point.longitude.toFixed(2)}°E<br>
          Wind: ${point.max_sustained_wind_kt || '--'} kt &nbsp;|&nbsp; Pres: ${point.min_central_pressure_mb || '--'} mb
        </span>
      </div>
    `, { className: 'custom-leaflet-tooltip' });

    this.layers.stormMarker.addLayer(marker);
  }

  fitBounds(bounds) {
    if (this.map && bounds) {
      this.map.fitBounds(bounds, { padding: [60, 60], maxZoom: 8, animate: true });
    }
  }

  initCoastalPlaceMarkers() {
    this.layers.places.clearLayers();

    const COASTAL_PLACES = [
      // Bay of Bengal: West Bengal & Odisha
      { name: 'Kolkata', lat: 22.5726, lon: 88.3639, state: 'West Bengal', icon: '🏙️' },
      { name: 'Haldia Port', lat: 22.0257, lon: 88.0583, state: 'West Bengal', icon: '⚓' },
      { name: 'Digha Coast', lat: 21.6266, lon: 87.5074, state: 'West Bengal', icon: '🏖️' },
      { name: 'Sundarbans', lat: 21.9497, lon: 88.8997, state: 'West Bengal', icon: '🌿' },
      { name: 'Balasore', lat: 21.4934, lon: 86.9135, state: 'Odisha', icon: '📍' },
      { name: 'Bhadrak', lat: 21.0544, lon: 86.4955, state: 'Odisha', icon: '📍' },
      { name: 'Kendrapara', lat: 20.5004, lon: 86.4230, state: 'Odisha', icon: '📍' },
      { name: 'Paradip Port', lat: 20.3165, lon: 86.6114, state: 'Odisha', icon: '⚓' },
      { name: 'Puri Coast', lat: 19.8135, lon: 85.8312, state: 'Odisha', icon: '🏖️' },
      { name: 'Bhubaneswar', lat: 20.2961, lon: 85.8245, state: 'Odisha', icon: '🏙️' },
      { name: 'Gopalpur Port', lat: 19.2608, lon: 84.9080, state: 'Odisha', icon: '⚓' },

      // Andhra Pradesh & Tamil Nadu
      { name: 'Srikakulam', lat: 18.2969, lon: 83.8967, state: 'Andhra Pradesh', icon: '📍' },
      { name: 'Visakhapatnam', lat: 17.6868, lon: 83.2185, state: 'Andhra Pradesh', icon: '⚓' },
      { name: 'Kakinada', lat: 16.9891, lon: 82.2475, state: 'Andhra Pradesh', icon: '⚓' },
      { name: 'Machilipatnam', lat: 16.1875, lon: 81.1389, state: 'Andhra Pradesh', icon: '📍' },
      { name: 'Nellore', lat: 14.4426, lon: 79.9865, state: 'Andhra Pradesh', icon: '📍' },
      { name: 'Chennai', lat: 13.0827, lon: 80.2707, state: 'Tamil Nadu', icon: '🏙️' },
      { name: 'Puducherry', lat: 11.9416, lon: 79.8083, state: 'Puducherry', icon: '🏖️' },
      { name: 'Cuddalore', lat: 11.7480, lon: 79.7714, state: 'Tamil Nadu', icon: '📍' },
      { name: 'Nagapattinam', lat: 10.7656, lon: 79.8424, state: 'Tamil Nadu', icon: '⚓' },

      // Arabian Sea: Gujarat & Maharashtra
      { name: 'Mumbai', lat: 18.9220, lon: 72.8347, state: 'Maharashtra', icon: '🏙️' },
      { name: 'Alibag', lat: 18.6414, lon: 72.8722, state: 'Maharashtra', icon: '🏖️' },
      { name: 'Ratnagiri', lat: 16.9902, lon: 73.3120, state: 'Maharashtra', icon: '⚓' },
      { name: 'Surat', lat: 21.1702, lon: 72.8311, state: 'Gujarat', icon: '🏙️' },
      { name: 'Bhavnagar', lat: 21.7645, lon: 72.1519, state: 'Gujarat', icon: '⚓' },
      { name: 'Veraval (Somnath)', lat: 20.9077, lon: 70.3679, state: 'Gujarat', icon: '📍' },
      { name: 'Porbandar', lat: 21.6417, lon: 69.6293, state: 'Gujarat', icon: '⚓' },
      { name: 'Dwarka', lat: 22.2442, lon: 68.9685, state: 'Gujarat', icon: '📍' },
      { name: 'Kandla Port', lat: 23.0041, lon: 70.2173, state: 'Gujarat', icon: '⚓' },
      { name: 'Mandvi', lat: 22.8333, lon: 69.3556, state: 'Gujarat', icon: '🏖️' },

      // South
      { name: 'Goa (Panaji)', lat: 15.4909, lon: 73.8278, state: 'Goa', icon: '🏖️' },
      { name: 'Mangaluru', lat: 12.9141, lon: 74.8560, state: 'Karnataka', icon: '⚓' },
      { name: 'Kochi Port', lat: 9.9312, lon: 76.2673, state: 'Kerala', icon: '⚓' },
      { name: 'Thiruvananthapuram', lat: 8.5241, lon: 76.9366, state: 'Kerala', icon: '🏙️' },

      // Neighboring Landfall Points
      { name: 'Chittagong', lat: 22.3569, lon: 91.7832, state: 'Bangladesh', icon: '⚓' },
      { name: 'Cox\'s Bazar', lat: 21.4272, lon: 92.0058, state: 'Bangladesh', icon: '🏖️' },
      { name: 'Khulna', lat: 22.8456, lon: 89.5403, state: 'Bangladesh', icon: '📍' },
      { name: 'Sittwe Port', lat: 20.1462, lon: 92.8983, state: 'Myanmar', icon: '⚓' },
      { name: 'Yangon', lat: 16.8661, lon: 96.1951, state: 'Myanmar', icon: '🏙️' },
      { name: 'Colombo', lat: 6.9271, lon: 79.8612, state: 'Sri Lanka', icon: '🏙️' },
      { name: 'Jaffna', lat: 9.6615, lon: 80.0255, state: 'Sri Lanka', icon: '📍' }
    ];

    COASTAL_PLACES.forEach(place => {
      const pinIcon = L.divIcon({
        className: 'city-pin-icon',
        html: `<div style="background: #0284c7; width: 8px; height: 8px; border-radius: 50%; border: 1.5px solid #ffffff; box-shadow: 0 0 4px rgba(0,0,0,0.4);"></div>`,
        iconSize: [8, 8],
        iconAnchor: [4, 4]
      });

      const marker = L.marker([place.lat, place.lon], { icon: pinIcon });

      marker.bindTooltip(`<strong>${place.name}</strong> (${place.state})`, {
        permanent: true,
        direction: 'top',
        offset: [0, -4],
        className: 'place-city-label'
      });

      this.layers.places.addLayer(marker);
    });
  }

  toggleLayer(layerKey, isVisible) {
    if (!this.layers[layerKey]) return;
    if (isVisible) {
      if (!this.map.hasLayer(this.layers[layerKey])) {
        this.map.addLayer(this.layers[layerKey]);
      }
    } else {
      if (this.map.hasLayer(this.layers[layerKey])) {
        this.map.removeLayer(this.layers[layerKey]);
      }
    }
  }
}
