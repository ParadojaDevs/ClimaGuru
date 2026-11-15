// Panel de condiciones actuales para la ciudad seleccionada.
// Fuente: /api/public/weather (Open-Meteo via backend con cache SQLite).

const WMO_CODES = {
  0: "Despejado",
  1: "Mayormente despejado",
  2: "Parcialmente nuboso",
  3: "Nublado",
  45: "Niebla",
  48: "Niebla con escarcha",
  51: "Llovizna ligera",
  53: "Llovizna",
  55: "Llovizna intensa",
  56: "Llovizna helada",
  57: "Llovizna helada intensa",
  61: "Lluvia ligera",
  63: "Lluvia",
  65: "Lluvia intensa",
  66: "Lluvia helada",
  67: "Lluvia helada intensa",
  71: "Nieve ligera",
  73: "Nieve",
  75: "Nieve intensa",
  77: "Granos de nieve",
  80: "Chubascos ligeros",
  81: "Chubascos",
  82: "Chubascos violentos",
  85: "Chubascos de nieve",
  86: "Chubascos de nieve intensos",
  95: "Tormenta eléctrica",
  96: "Tormenta con granizo",
  99: "Tormenta con granizo fuerte",
};

function weatherDescription(code) {
  return WMO_CODES[code] ?? "Sin datos";
}

function fmtTime(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleTimeString("es-CO", {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: "America/Bogota",
    });
  } catch {
    return "";
  }
}

function fmtFetchedAt(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString("es-CO", {
      dateStyle: "short",
      timeStyle: "short",
      timeZone: "America/Bogota",
    });
  } catch {
    return "";
  }
}

function Metric({ label, value }) {
  return (
    <div className="weather-metric">
      <span className="weather-metric__label">{label}</span>
      <span className="weather-metric__value">{value}</span>
    </div>
  );
}

export default function WeatherPanel({ city, weather, loading, error, onRetry }) {
  if (!city) {
    return <div className="panel-empty">Cargando catálogo de ciudades…</div>;
  }

  if (loading && !weather) {
    return (
      <div className="panel-empty">
        <div className="loading-spinner loading-spinner--inline" />
        Consultando condiciones para {city.name}…
      </div>
    );
  }

  if (error && !weather) {
    return (
      <div className="panel-empty panel-empty--error">
        <p>{error}</p>
        <button className="btn btn-secondary" onClick={onRetry}>
          Reintentar
        </button>
      </div>
    );
  }

  const current = weather?.current || {};
  const temp = current.temperature_2m;
  const feels = current.apparent_temperature;
  const humidity = current.relative_humidity_2m;
  const wind = current.wind_speed_10m;
  const precip = current.precipitation;
  const clouds = current.cloud_cover;
  const pressure = current.pressure_msl;
  const isDay = current.is_day !== 0;

  return (
    <div className="weather-panel" data-loading={loading ? "true" : "false"}>
      <header className="weather-head">
        <div>
          <h2 className="weather-city">{city.name}</h2>
          <p className="weather-dept">{city.department}</p>
        </div>
        <span className={`weather-dayflag ${isDay ? "" : "weather-dayflag--night"}`}>
          {isDay ? "DÍA" : "NOCHE"}
        </span>
      </header>

      <div className="weather-now">
        <span className="weather-temp">
          {temp != null ? `${Math.round(temp)}°` : "—"}
        </span>
        <span className="weather-desc">{weatherDescription(current.weather_code)}</span>
      </div>

      <div className="weather-grid">
        <Metric label="Sensación" value={feels != null ? `${Math.round(feels)}°C` : "—"} />
        <Metric label="Humedad" value={humidity != null ? `${humidity}%` : "—"} />
        <Metric label="Viento" value={wind != null ? `${Math.round(wind)} km/h` : "—"} />
        <Metric label="Precip." value={precip != null ? `${precip} mm` : "—"} />
        <Metric label="Nubosidad" value={clouds != null ? `${clouds}%` : "—"} />
        <Metric label="Presión" value={pressure != null ? `${Math.round(pressure)} hPa` : "—"} />
      </div>

      <footer className="weather-foot">
        <span className="weather-source">
          Open-Meteo · actualizado{" "}
          {fmtTime(weather?.current?.time) || fmtFetchedAt(weather?.fetched_at)}
        </span>
        {error && (
          <button className="btn btn-ghost weather-refresh" onClick={onRetry}>
            Actualizar
          </button>
        )}
      </footer>
    </div>
  );
}
