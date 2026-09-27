/**
 * Cyclone Intelligence System - REST API Client
 * Interfaces with FastAPI endpoints at /api/v1/
 */

const API_BASE = '/api/v1';

export const AuthState = {
  TOKEN_KEY: 'vd_authority_token',
  USER_KEY: 'vd_authority_user',

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  setSession(token, user) {
    if (token) localStorage.setItem(this.TOKEN_KEY, token);
    if (user) localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },

  clearSession() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  },

  getUser() {
    const raw = localStorage.getItem(this.USER_KEY);
    try {
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  isAuthority() {
    const user = this.getUser();
    const token = this.getToken();
    return Boolean(token && user && (user.is_authority || user.role?.includes('AUTHORITY') || user.role?.includes('COLLECTOR')));
  },

  getAuthHeaders() {
    const token = this.getToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }
};

export const API = {
  // Auth Endpoints
  async login(email, password) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Authentication failed' }));
      throw new Error(err.detail || 'Authority login failed');
    }
    const data = await res.json();
    AuthState.setSession(data.access_token, data.user);
    return data;
  },

  async getMe() {
    const token = AuthState.getToken();
    if (!token) return null;
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: AuthState.getAuthHeaders()
      });
      if (res.ok) {
        const user = await res.json();
        AuthState.setSession(token, user);
        return user;
      }
      AuthState.clearSession();
      return null;
    } catch {
      return null;
    }
  },

  async logout() {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: AuthState.getAuthHeaders()
      });
    } catch (e) {
      // Ignore network errors on logout
    }
    AuthState.clearSession();
  },

  async getAuthoritiesCatalog() {
    const res = await fetch(`${API_BASE}/auth/authorities-catalog`);
    return await res.json();
  },
  async getSystemStatus() {
    const res = await fetch(`${API_BASE}/system/status`);
    return await res.json();
  },

  async getDataSources() {
    const res = await fetch(`${API_BASE}/system/sources`);
    return await res.json();
  },

  async getLiveStorms() {
    const res = await fetch(`${API_BASE}/storms/live`);
    return await res.json();
  },

  async getStorms(year = null) {
    const url = year ? `${API_BASE}/storms?year=${year}` : `${API_BASE}/storms`;
    const res = await fetch(url);
    return await res.json();
  },

  async getStormDetail(stormId) {
    const res = await fetch(`${API_BASE}/storms/${encodeURIComponent(stormId)}`);
    return await res.json();
  },

  async getStormTimeline(stormId) {
    const res = await fetch(`${API_BASE}/storms/${encodeURIComponent(stormId)}/timeline`);
    return await res.json();
  },

  async getSatelliteSnapshotMeta(date, lat, lon, spanDeg = 8.0, layer = 'MODIS_Terra_CorrectedReflectance_TrueColor') {
    const url = `${API_BASE}/observations/satellite/snapshot?date=${encodeURIComponent(date)}&lat=${lat}&lon=${lon}&span_deg=${spanDeg}&layer=${encodeURIComponent(layer)}`;
    const res = await fetch(url);
    return await res.json();
  },

  getSatelliteImageUrl(date, lat, lon, spanDeg = 8.0, layer = 'MODIS_Terra_CorrectedReflectance_TrueColor') {
    return `${API_BASE}/observations/satellite/image?date=${encodeURIComponent(date)}&lat=${lat}&lon=${lon}&span_deg=${spanDeg}&layer=${encodeURIComponent(layer)}`;
  },

  async getObservation(stormId, timestamp = null) {
    const url = timestamp 
      ? `${API_BASE}/observations/${encodeURIComponent(stormId)}?timestamp=${encodeURIComponent(timestamp)}`
      : `${API_BASE}/observations/${encodeURIComponent(stormId)}`;
    const res = await fetch(url);
    return await res.json();
  },

  async getCalibratedSatellite(stormId, stepIndex = 0) {
    const res = await fetch(`${API_BASE}/observations/${encodeURIComponent(stormId)}/calibrated_satellite?step_index=${stepIndex}`);
    return await res.json();
  },

  async getEvolutionFingerprint(stormId, endStep = null) {
    const url = endStep !== null
      ? `${API_BASE}/evolution/${encodeURIComponent(stormId)}?end_step=${endStep}`
      : `${API_BASE}/evolution/${encodeURIComponent(stormId)}`;
    const res = await fetch(url);
    return await res.json();
  },

  async getEvolutionProgression(stormId) {
    const res = await fetch(`${API_BASE}/evolution/${encodeURIComponent(stormId)}/progression`);
    return await res.json();
  },

  async getEyeStructure(stormId, stepIndex = null) {
    const url = stepIndex !== null
      ? `${API_BASE}/evolution/${encodeURIComponent(stormId)}/eye_structure?step_index=${stepIndex}`
      : `${API_BASE}/evolution/${encodeURIComponent(stormId)}/eye_structure`;
    const res = await fetch(url);
    return await res.json();
  },


  async getPrediction(stormId, forecastInitStep = null) {
    const url = forecastInitStep !== null
      ? `${API_BASE}/prediction/${encodeURIComponent(stormId)}?forecast_init_step=${forecastInitStep}`
      : `${API_BASE}/prediction/${encodeURIComponent(stormId)}`;
    const res = await fetch(url);
    return await res.json();
  },

  async getGISExposure(stormId, forecastStep = null, corridorMultiplier = 1.0) {
    let url = `${API_BASE}/gis/exposure/${encodeURIComponent(stormId)}?corridor_multiplier=${corridorMultiplier}`;
    if (forecastStep !== null) {
      url += `&forecast_step=${forecastStep}`;
    }
    const res = await fetch(url);
    return await res.json();
  },

  async getDistrictsGeoJSON() {
    const res = await fetch(`${API_BASE}/gis/districts`);
    return await res.json();
  },

  async getInfrastructureGeoJSON() {
    const res = await fetch(`${API_BASE}/gis/infrastructure`);
    return await res.json();
  },

  async simulateScenario(payload) {
    const res = await fetch(`${API_BASE}/scenario/simulate`, {
      method: 'POST',
      headers: AuthState.getAuthHeaders(),
      body: JSON.stringify(payload)
    });
    return await res.json();
  },

  async getModelBenchmarks() {
    const res = await fetch(`${API_BASE}/models/benchmarks`);
    return await res.json();
  }
};
