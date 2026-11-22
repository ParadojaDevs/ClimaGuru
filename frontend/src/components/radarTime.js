// Utilidades de tiempo para el radar IDEAM.
//
// Los sellos IDEAM usan hora local Colombia (UTC-5), formato YYMMDDHHMM.
// Se mantienen aqui (y no dentro del componente) para poder probarlas sin
// montar React ni Leaflet.

const STAMP_PATTERN = /^\d{10}$/;
const COT_OFFSET_MS = 5 * 60 * 60 * 1000;

// Devuelve el instante UTC (ms) de un sello COT, o null si no es valido.
export function parseStamp(stamp) {
  if (typeof stamp !== "string" || !STAMP_PATTERN.test(stamp)) return null;
  const yy = Number(stamp.slice(0, 2));
  const mo = Number(stamp.slice(2, 4));
  const dd = Number(stamp.slice(4, 6));
  const hh = Number(stamp.slice(6, 8));
  const mi = Number(stamp.slice(8, 10));
  if (mo < 1 || mo > 12 || dd < 1 || dd > 31 || hh > 23 || mi > 59) {
    return null;
  }
  const utcMs = Date.UTC(2000 + yy, mo - 1, dd, hh + 5, mi);
  const date = new Date(utcMs);
  if (Number.isNaN(date.getTime())) return null;
  // Verificacion de ida y vuelta: descarta fechas imposibles (31/02, etc.).
  const back = new Date(utcMs - COT_OFFSET_MS);
  if (
    back.getUTCFullYear() !== 2000 + yy ||
    back.getUTCMonth() !== mo - 1 ||
    back.getUTCDate() !== dd ||
    back.getUTCHours() !== hh ||
    back.getUTCMinutes() !== mi
  ) {
    return null;
  }
  return utcMs;
}

// Etiqueta legible + edad en minutos. `nowMs` se inyecta en pruebas.
export function stampInfo(stamp, nowMs = Date.now()) {
  const utcMs = parseStamp(stamp);
  if (utcMs === null) return null;
  const yy = stamp.slice(0, 2);
  const mo = stamp.slice(2, 4);
  const dd = stamp.slice(4, 6);
  const hh = stamp.slice(6, 8);
  const mi = stamp.slice(8, 10);
  const ageMin = Math.round((nowMs - utcMs) / 60000);
  return {
    label: `${dd}/${mo} ${hh}:${mi} COT`,
    ageMin,
    ageMinutes: ageMin,
    iso: new Date(utcMs).toISOString(),
    stamp: `${yy}${mo}${dd}${hh}${mi}`,
  };
}

export function ageText(ageMin) {
  if (typeof ageMin !== "number" || !Number.isFinite(ageMin)) return "";
  if (ageMin < 1) return "hace segundos";
  if (ageMin < 90) return `hace ${ageMin} min`;
  return `hace ${Math.round(ageMin / 60)} h`;
}

// Una imagen se considera antigua cuando supera la ventana de frescura.
export function isStale(ageMin, maxAgeMinutes) {
  return (
    typeof ageMin === "number" &&
    Number.isFinite(ageMin) &&
    typeof maxAgeMinutes === "number" &&
    ageMin > maxAgeMinutes
  );
}
