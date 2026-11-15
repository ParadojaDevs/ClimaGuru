const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";

function buildHeaders(token, hasBody = false) {
  const headers = {};
  if (hasBody) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
}

async function request(path, { method = "GET", token, body } = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers: buildHeaders(token, Boolean(body)),
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include",
  });

  let data = {};
  try {
    data = await response.json();
  } catch {
    // Respuesta sin JSON: se conserva {} para el manejo de error.
  }

  if (!response.ok) {
    throw new Error(data.error || data.message || `Error ${response.status}`);
  }
  return data;
}

// Token source priority: cookies > localStorage (for transition period)
const COOKIE_ACCESS_TOKEN_NAME = "climaguru_access_token";
const COOKIE_REFRESH_TOKEN_NAME = "climaguru_refresh_token";

export function getAccessTokenFromCookies() {
  if (typeof document !== "undefined") {
    const match = document.cookie.match(
      `(^|; )${COOKIE_ACCESS_TOKEN_NAME}=([^;]+)`
    );
    return match ? decodeURIComponent(match[2]) : null;
  }
  return null;
}

export function getRefreshTokenFromCookies() {
  if (typeof document !== "undefined") {
    const match = document.cookie.match(
      `(^|; )${COOKIE_REFRESH_TOKEN_NAME}=([^;]+)`
    );
    return match ? decodeURIComponent(match[2]) : null;
  }
  return null;
}

// Get token from cookies, with fallback to localStorage for transition
export function getAccessToken() {
  // Prioritize cookies (more secure - XSS resistant)
  const cookieToken = getAccessTokenFromCookies();
  if (cookieToken) return cookieToken;
  // Fallback to localStorage
  return localStorage.getItem("climaguru_access_token");
}

export function getRefreshToken() {
  const cookieToken = getRefreshTokenFromCookies();
  if (cookieToken) return cookieToken;
  return localStorage.getItem("climaguru_refresh_token");
}

// Set tokens - primarily set via cookies from backend response
export function setTokensFromCookies(accessToken, refreshToken) {
  // Store in localStorage as fallback/backup, but primary is cookies
  if (typeof window !== "undefined") {
    // Optionally store in localStorage for backup
    localStorage.setItem("climaguru_access_token", accessToken);
    localStorage.setItem("climaguru_refresh_token", refreshToken);
  }
}

// Manual cookie setting (used during transition/debug)
export function setTokens(accessToken, refreshToken) {
  if (typeof window !== "undefined") {
    // Set as httpOnly cookies would be set by backend
    // During transition, also store in localStorage for backward compat
    localStorage.setItem("climaguru_access_token", accessToken);
    localStorage.setItem("climaguru_refresh_token", refreshToken);
  }
}

export function clearTokens() {
  // Clear cookies
  if (typeof document !== "undefined") {
    // Clear access token cookie
    document.cookie = `
      climaguru_access_token=;
      Max-Age=0;
      path=/;
      ${location.protocol === "https:" ? "Secure;" : ""}
      SameSite=Lax;
    `;
    // Clear refresh token cookie
    document.cookie = `
      climaguru_refresh_token=;
      Max-Age=0;
      path=/;
      ${location.protocol === "https:" ? "Secure;" : ""}
      SameSite=Lax;
    `;
  }
  // Clear localStorage fallback
  localStorage.removeItem("climaguru_access_token");
  localStorage.removeItem("climaguru_refresh_token");
}

// Login - receives tokens via cookies from backend, stores fallback in localStorage
export function login(username, password) {
  return request("/login", {
    method: "POST",
    body: { username, password },
  }).then((data) => {
    // Tokens come back in JSON, but also set as cookies by backend
    // Store in localStorage as backup/transition mechanism
    setTokens(data.token, data.refresh_token);
    return data;
  });
}

export function getUsers(token) {
  return request("/users", { token });
}

export function createUser(token, data) {
  return request("/users", {
    method: "POST",
    token,
    body: data,
  });
}

export function updateUser(token, id, data) {
  return request(`/users/${id}`, {
    method: "PUT",
    token,
    body: data,
  });
}

export function deleteUser(token, id) {
  return request(`/users/${id}`, {
    method: "DELETE",
    token,
  });
}

// Logout - clear authentication tokens (cookies and localStorage fallback)
export function logout() {
  clearTokens();
}

// ---------- Zona publica (sin autenticacion) ----------

// Catalogo de ciudades sembradas por el backend.
export function fetchCities() {
  return request("/api/public/cities");
}

// Pronostico puntual Open-Meteo (lat/lon validados contra el bbox de Colombia).
export function fetchWeather(lat, lon) {
  return request(`/api/public/weather?lat=${lat}&lon=${lon}`);
}

// Catalogo de radares IDEAM (id, nombre, coords, alcance).
export function fetchRadarStations() {
  return request("/api/public/radar/stations");
}

// Imagen compuesta nacional mas reciente (PNG con basemap, para el visor).
export function fetchRadarLatest() {
  return request("/api/public/radar/latest");
}

// PNG transparente de reflectividad de un radar (puede responder 502 si no hay scan reciente).
export function fetchRadarOverlay(radar) {
  return request(`/api/public/radar/overlay?radar=${radar}`);
}

// Frames recientes de un radar segun el manifiesto IDEAM (navegacion temporal).
export function fetchRadarFrames(radar) {
  return request(`/api/public/radar/frames?radar=${radar}`);
}
