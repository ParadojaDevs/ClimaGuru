import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  MapContainer,
  TileLayer,
  Circle,
  Marker,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

import {
  fetchCities,
  fetchRadarStations,
  fetchWeather,
} from "../../services/api";
import WeatherPanel from "../components/WeatherPanel";
import RadarViewer from "../components/RadarViewer";

const MAP_TILES_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";

// Centro de Colombia.
const MAP_CENTER = [4.6, -74.1];
const MAP_ZOOM = 5.5;

// Icono de radar: chip con el codigo IDEAM de 3 letras.
function radarIcon(code, active) {
  const html = `
    <div class="radar-chip ${active ? "radar-chip--active" : ""}">
      <span class="radar-chip__dot"></span>${code}
    </div>`;
  return L.divIcon({
    html,
    className: "radar-chip-wrapper",
    iconSize: [64, 26],
    iconAnchor: [32, 13],
  });
}

// Marcador de ciudad seleccionada: punto con halo pulsante.
function cityIcon() {
  const html = `<div class="city-pin"><span class="city-pin__core"></span></div>`;
  return L.divIcon({
    html,
    className: "city-pin-wrapper",
    iconSize: [20, 20],
    iconAnchor: [10, 10],
  });
}

// Mueve el mapa de forma programatica cuando cambia el objetivo.
function MapController({ target }) {
  const map = useMap();
  useEffect(() => {
    if (target) {
      map.flyTo(target.center, target.zoom, { duration: 0.8 });
    }
  }, [target, map]);
  return null;
}

export default function PublicMap() {
  const [cities, setCities] = useState([]);
  const [stations, setStations] = useState([]);
  const [selectedCity, setSelectedCity] = useState(null);
  const [weather, setWeather] = useState(null);
  const [weatherLoading, setWeatherLoading] = useState(false);
  const [weatherError, setWeatherError] = useState("");
  const [mapTarget, setMapTarget] = useState(null);
  const [panelTab, setPanelTab] = useState("clima");
  const [radarFocus, setRadarFocus] = useState(null); // id de radar al hacer click en el mapa
  const [panelHidden, setPanelHidden] = useState(false);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const [cityData, radarData] = await Promise.all([
          fetchCities(),
          fetchRadarStations(),
        ]);
        if (!alive) return;
        setCities(cityData.cities || []);
        setStations(radarData.stations || []);
        const initial =
          (cityData.cities || []).find((c) => c.default) ||
          (cityData.cities || [])[0];
        if (initial) {
          setSelectedCity(initial);
          setMapTarget({ center: [initial.lat, initial.lon], zoom: 6.5 });
        }
      } catch (err) {
        if (alive) {
          setWeatherError(
            `No se pudo cargar el catalogo inicial: ${err.message}`
          );
        }
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  const loadWeather = useCallback(async (city) => {
    if (!city) return;
    setWeatherLoading(true);
    setWeatherError("");
    try {
      const data = await fetchWeather(city.lat, city.lon);
      setWeather(data);
    } catch (err) {
      setWeather(null);
      setWeatherError(err.message);
    } finally {
      setWeatherLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedCity) {
      loadWeather(selectedCity);
    }
  }, [selectedCity, loadWeather]);

  function selectCity(city) {
    setSelectedCity(city);
    setPanelTab("clima");
    setMapTarget({ center: [city.lat, city.lon], zoom: 6.5 });
  }

  function focusRadar(station) {
    setRadarFocus(station.id);
    setPanelTab("radar");
    setPanelHidden(false);
    setMapTarget({
      center: [station.lat, station.lon],
      zoom: 6.5,
    });
  }

  const radarByActive = useMemo(
    () => stations.find((s) => s.id === radarFocus) || null,
    [stations, radarFocus]
  );

  return (
    <div className="public-shell page-enter">
      <div className="public-map">
        <MapContainer
          center={MAP_CENTER}
          zoom={MAP_ZOOM}
          className="public-leaflet"
          zoomControl={false}
          preferCanvas
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url={MAP_TILES_URL}
          />
          <MapController target={mapTarget} />

          {/* Anillos de cobertura de los 4 radares IDEAM */}
          {stations.map((station) => (
            <Circle
              key={`ring-${station.id}`}
              center={[station.lat, station.lon]}
              radius={station.range_km * 1000}
              pathOptions={{
                color: "var(--radar-active)",
                weight: 1,
                opacity: 0.25,
                fillColor: "var(--radar-active)",
                fillOpacity: 0.03,
              }}
              interactive={false}
            />
          ))}

          {/* Marcadores de radar */}
          {stations.map((station) => (
            <Marker
              key={station.id}
              position={[station.lat, station.lon]}
              icon={radarIcon(station.code, radarFocus === station.id)}
              eventHandlers={{ click: () => focusRadar(station) }}
              zIndexOffset={400}
            />
          ))}

          {/* Ciudad seleccionada */}
          {selectedCity && (
            <Marker
              position={[selectedCity.lat, selectedCity.lon]}
              icon={cityIcon()}
              interactive={false}
              zIndexOffset={500}
            />
          )}
        </MapContainer>
      </div>

      {/* Barra superior: marca + acceso a la estacion autenticada */}
      <header className="public-topbar">
        <div className="public-brand">
          <span className="public-brand__logo">CLIMAGURU</span>
          <span className="public-brand__sub">RADAR · COLOMBIA</span>
        </div>
        <nav className="public-nav">
          <Link className="btn btn-ghost" to="/dashboard">
            Panel de estación
          </Link>
          <Link className="btn btn-primary" to="/login">
            Iniciar sesión
          </Link>
        </nav>
      </header>

      {/* Chips de ciudades */}
      <div className="city-strip" role="tablist" aria-label="Ciudades">
        {cities.map((city) => (
          <button
            key={city.name}
            className={`city-chip ${
              selectedCity?.name === city.name ? "city-chip--active" : ""
            }`}
            onClick={() => selectCity(city)}
          >
            {city.name}
          </button>
        ))}
      </div>

      {/* Boton para ocultar/mostrar el panel lateral */}
      <button
        className={`public-panel-toggle ${panelHidden ? "is-collapsed" : ""}`}
        onClick={() => setPanelHidden((v) => !v)}
        aria-label={panelHidden ? "Mostrar panel" : "Ocultar panel"}
      >
        {panelHidden ? "◀" : "▶"}
      </button>

      {/* Panel lateral: clima / radar */}
      <aside className={`public-panel ${panelHidden ? "public-panel--hidden" : ""}`}>
        <div className="public-panel__tabs" role="tablist">
          <button
            role="tab"
            aria-selected={panelTab === "clima"}
            className={`public-tab ${panelTab === "clima" ? "public-tab--active" : ""}`}
            onClick={() => setPanelTab("clima")}
          >
            Clima
          </button>
          <button
            role="tab"
            aria-selected={panelTab === "radar"}
            className={`public-tab ${panelTab === "radar" ? "public-tab--active" : ""}`}
            onClick={() => setPanelTab("radar")}
          >
            Radar
          </button>
        </div>

        <div className="public-panel__body">
          {panelTab === "clima" ? (
            <WeatherPanel
              city={selectedCity}
              weather={weather}
              loading={weatherLoading}
              error={weatherError}
              onRetry={() => loadWeather(selectedCity)}
            />
          ) : (
            <RadarViewer
              stations={stations}
              focusId={radarFocus}
            />
          )}
        </div>
      </aside>

      {/* Atribucion obligatoria de fuentes */}
      <footer className="public-attribution">
        Datos: <a href="https://open-meteo.com/" target="_blank" rel="noreferrer">Open-Meteo</a>
        {" · "}
        <a href="https://www.ideam.gov.co/" target="_blank" rel="noreferrer">IDEAM</a> radar (CC BY 4.0)
        {" · Mapa © OpenStreetMap © CARTO"}
      </footer>
    </div>
  );
}
