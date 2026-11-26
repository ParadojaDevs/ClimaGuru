// Politica de visualizacion del overlay de radar en el mapa.
//
// El backend es la fuente de verdad: envia `georef` con `state`,
// `visualization`, `render_allowed`, `warning` y `bounds`. Este modulo solo
// traduce esa decision a algo que Leaflet pueda consumir, sin recalcular
// bounds ni elevar estados de confianza.

export const VISUALIZATION_EXACT = "exact";
export const VISUALIZATION_APPROXIMATE = "approximate_with_warning";
export const VISUALIZATION_BLOCKED = "blocked";

// Ventana de frescura: un frame mas viejo no se dibuja sobre el mapa para no
// presentarlo como dato actual. IDEAM publica cada 5 min.
export const OVERLAY_MAX_AGE_MINUTES = 60;
export const DEFAULT_OVERLAY_OPACITY = 0.65;

export function clampOpacity(value, fallback = DEFAULT_OVERLAY_OPACITY) {
  if (value === null || value === undefined) return fallback;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return fallback;
  return Math.min(1, Math.max(0, numeric));
}

// Convierte {west, south, east, north} a [[south, west], [north, east]].
// Devuelve null si faltan numeros o los limites son imposibles.
export function toLeafletBounds(bounds) {
  if (!bounds || typeof bounds !== "object") return null;
  const { west, south, east, north } = bounds;
  const values = [west, south, east, north];
  if (!values.every((value) => typeof value === "number" && Number.isFinite(value))) {
    return null;
  }
  if (!(west < east) || !(south < north)) return null;
  if (south < -90 || north > 90 || west < -180 || east > 180) return null;
  return [
    [south, west],
    [north, east],
  ];
}

// Decide si el overlay puede dibujarse y con que advertencia.
// Reglas (en orden):
//   1. sin `georef` -> bloqueado;
//   2. `render_allowed !== true`, `visualization="blocked"` o `state="assumed"`
//      -> bloqueado (BAR/CAR y cualquier respuesta incoherente);
//   3. visualizacion aproximada sin aviso -> bloqueado (nunca sin aviso);
//   4. edad desconocida o invalida -> bloqueado (no se asume que sea fresca);
//   5. frame fuera de la ventana de frescura -> no se dibuja;
//   6. en cualquier otro caso -> permitido (con aviso si es aproximado).
export function overlayDecision({
  georef,
  ageMinutes,
  maxAgeMinutes = OVERLAY_MAX_AGE_MINUTES,
} = {}) {
  const blocked = {
    renderAllowed: false,
    approximate: false,
    warning: null,
    stale: false,
    reason: "",
  };

  if (!georef || typeof georef !== "object") {
    return { ...blocked, reason: "missing_georef" };
  }

  const warning =
    typeof georef.warning === "string" && georef.warning.trim()
      ? georef.warning.trim()
      : null;
  const approximate =
    georef.visualization === VISUALIZATION_APPROXIMATE || georef.state === "derived";

  if (
    georef.render_allowed !== true ||
    georef.visualization === VISUALIZATION_BLOCKED ||
    georef.state === "assumed"
  ) {
    return { ...blocked, approximate, reason: "blocked" };
  }
  if (approximate && !warning) {
    return { ...blocked, approximate, reason: "missing_warning" };
  }

  const ageKnown =
    typeof ageMinutes === "number" &&
    Number.isFinite(ageMinutes) &&
    ageMinutes >= 0;

  if (!ageKnown) {
    return { ...blocked, approximate, warning, reason: "unknown_age" };
  }

  const maxAge =
    typeof maxAgeMinutes === "number" &&
    Number.isFinite(maxAgeMinutes) &&
    maxAgeMinutes >= 0
      ? maxAgeMinutes
      : OVERLAY_MAX_AGE_MINUTES;
  const stale = ageMinutes > maxAge;

  if (stale) {
    return { ...blocked, approximate, warning, stale: true, reason: "stale" };
  }

  return {
    renderAllowed: true,
    approximate,
    warning,
    stale: false,
    reason: "",
  };
}
