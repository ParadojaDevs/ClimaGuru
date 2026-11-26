// Visor de radar IDEAM.
// - Compuesto nacional: PNG opaco (con basemap), imagen mas reciente.
// - Por radar: PNG transparente de reflectividad (z). Puede fallar con 502 si
//   el radar no tiene scans recientes (estado honesto por radar).
// - Navegacion temporal: frames del manifiesto IDEAM (ultimos ~3 h).
//
// El visor tambien publica el overlay activo al mapa (via onOverlayChange)
// solo cuando la politica geografica del backend lo autoriza.

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  fetchRadarLatest,
  fetchRadarOverlay,
  fetchRadarFrames,
} from "../../services/api";
import {
  DEFAULT_OVERLAY_OPACITY,
  clampOpacity,
  overlayDecision,
} from "./radarOverlayPolicy";
import { ageText, stampInfo } from "./radarTime";

const COMPOSITE = "composite";

function Spinner() {
  return <div className="loading-spinner loading-spinner--inline" />;
}

export default function RadarViewer({ stations, focusId, onOverlayChange, overlayError }) {
  const [source, setSource] = useState(focusId || COMPOSITE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [composite, setComposite] = useState(null);
  const [overlay, setOverlay] = useState(null); // {source,stamp,url,station,georef}
  const [frames, setFrames] = useState([]);
  const [frameIndex, setFrameIndex] = useState(0);
  const [overlayVisible, setOverlayVisible] = useState(true);
  const [overlayOpacity, setOverlayOpacity] = useState(DEFAULT_OVERLAY_OPACITY);

  // Si el usuario hace click en un radar del mapa, saltar a ese radar.
  useEffect(() => {
    if (focusId) {
      setSource(focusId);
    }
  }, [focusId]);

  const load = useCallback(async (src) => {
    setLoading(true);
    setError("");
    setOverlay(null);
    setFrames([]);
    setFrameIndex(0);

    try {
      if (src === COMPOSITE) {
        const data = await fetchRadarLatest();
        setComposite(data);
      } else {
        // Overlay y frames en paralelo; si el overlay esta sin datos
        // recientes (502) el manifiesto puede salvar la vista.
        const [ov, fr] = await Promise.allSettled([
          fetchRadarOverlay(src),
          fetchRadarFrames(src),
        ]);
        const okOverlay = ov.status === "fulfilled" ? ov.value : null;
        const okFrames = fr.status === "fulfilled" ? fr.value.frames || [] : [];

        if (!okOverlay && okFrames.length === 0) {
          const detail =
            ov.status === "rejected" ? ov.reason?.message : "sin datos";
          throw new Error(detail);
        }

        if (okOverlay) {
          setOverlay({ ...okOverlay, source: src, fromFrames: false });
        } else {
          // Fallback honesto: el frame mas reciente del manifiesto
          // (los frames vienen en orden ascendente).
          const latest = okFrames[okFrames.length - 1];
          setOverlay({
            kind: `overlay:${src}`,
            source: src,
            stamp: latest.stamp,
            url: latest.url,
            fromFrames: true,
          });
        }
        setFrames(okFrames);
        // Los frames llegan en orden ascendente: el indice inicial es el mas
        // reciente para que la etiqueta coincida con la imagen mostrada.
        setFrameIndex(Math.max(0, okFrames.length - 1));
      }
    } catch (err) {
      setError(err.message || "Radar no disponible");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load(source);
  }, [source, load]);

  // Recarga al recibir foco desde el mapa (permite ver el estado fresco).
  useEffect(() => {
    if (focusId && focusId !== source) {
      setSource(focusId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focusId]);

  const isStation = source !== COMPOSITE;
  // El overlay debe pertenecer al radar seleccionado. Al cambiar de fuente, el
  // estado anterior queda invisible hasta que llegue la respuesta nueva.
  const active = isStation
    ? overlay?.source === source
      ? overlay
      : null
    : composite;
  const station = isStation ? stations.find((s) => s.id === source) || null : null;
  // `georef` viaja en la respuesta del overlay y, como respaldo, en /stations.
  const georef = active?.georef || station?.georef || null;
  const info = stampInfo(active?.stamp);
  const currentFrame = frames[frameIndex] || null;

  const decision = useMemo(
    () =>
      isStation && active?.url
        ? overlayDecision({ georef, ageMinutes: info?.ageMinutes })
        : null,
    [isStation, active?.url, georef, info?.ageMinutes]
  );

  // Publica el overlay al mapa solo si la politica lo autoriza.
  useEffect(() => {
    if (!onOverlayChange) return;
    if (!isStation || !active?.url || !decision?.renderAllowed) {
      onOverlayChange(null);
      return;
    }
    onOverlayChange({
      key: `${source}:${active.stamp}:${active.url}`,
      radarId: source,
      code: station?.code || active?.station?.code || "",
      url: active.url,
      stamp: active.stamp,
      bounds: georef?.bounds || null,
      warning: decision.warning,
      approximate: decision.approximate,
      opacity: overlayOpacity,
      visible: overlayVisible,
    });
  }, [
    onOverlayChange,
    isStation,
    source,
    active?.url,
    active?.stamp,
    active?.station?.code,
    station?.code,
    georef,
    decision,
    overlayOpacity,
    overlayVisible,
  ]);

  // Al desmontar (p. ej. cambiar a la pestana Clima) se retira la capa.
  useEffect(() => {
    return () => {
      if (onOverlayChange) onOverlayChange(null);
    };
  }, [onOverlayChange]);

  function stepFrame(delta) {
    setFrameIndex((i) => Math.min(Math.max(i + delta, 0), frames.length - 1));
  }

  return (
    <div className="radar-viewer">
      <div className="radar-source-row" role="tablist" aria-label="Fuente radar">
        <button
          className={`radar-source ${source === COMPOSITE ? "radar-source--active" : ""}`}
          onClick={() => setSource(COMPOSITE)}
        >
          Compuesto
        </button>
        {stations.map((s) => (
          <button
            key={s.id}
            className={`radar-source ${source === s.id ? "radar-source--active" : ""}`}
            onClick={() => setSource(s.id)}
          >
            {s.code}
          </button>
        ))}
      </div>

      <div className="radar-stage">
        {loading && (
          <div className="radar-stage__loading">
            <Spinner />
            <span>Consultando IDEAM…</span>
          </div>
        )}

        {!loading && error && (
          <div className="radar-stage__error">
            <p className="radar-stage__error-title">Sin imagen disponible</p>
            <p className="radar-stage__error-detail">{error}</p>
            <button className="btn btn-secondary" onClick={() => load(source)}>
              Reintentar
            </button>
          </div>
        )}

        {!loading && !error && active?.url && (
          <a
            className="radar-image-link"
            href={active.url}
            target="_blank"
            rel="noreferrer"
            title="Abrir imagen original de IDEAM"
          >
            <img
              className="radar-image"
              src={active.url}
              alt={
                isStation
                  ? `Reflectividad radar ${active.station?.name || station?.name || source}`
                  : "Compuesto radar nacional IDEAM"
              }
            />
          </a>
        )}

        {!loading && !error && !active?.url && (
          <div className="radar-stage__empty">Sin datos todavía.</div>
        )}
      </div>

      <div className="radar-meta">
        {info ? (
          <>
            <span className="radar-stamp">{info.label}</span>
            <span className="radar-age">{ageText(info.ageMin)}</span>
          </>
        ) : (
          <span className="radar-stamp">—</span>
        )}
        {isStation && active?.fromFrames && (
          <span className="radar-note">overlay sin datos · frame del manifiesto</span>
        )}
        <button className="btn btn-ghost radar-refresh" onClick={() => load(source)}>
          Actualizar
        </button>
      </div>

      {isStation && decision?.renderAllowed && (
        <div className="radar-overlay-controls">
          <label className="radar-overlay-toggle">
            <input
              type="checkbox"
              checked={overlayVisible}
              onChange={(event) => setOverlayVisible(event.target.checked)}
            />
            Mostrar en el mapa
          </label>
          <label className="radar-overlay-opacity">
            <span>Opacidad</span>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={overlayOpacity}
              disabled={!overlayVisible}
              onChange={(event) =>
                setOverlayOpacity(clampOpacity(event.target.value))
              }
            />
            <span>{Math.round(overlayOpacity * 100)}%</span>
          </label>
        </div>
      )}

      {isStation && decision?.renderAllowed && decision.warning && (
        <p className="radar-geo-warning" role="note">
          {decision.warning}
        </p>
      )}

      {isStation && decision?.stale && (
        <p className="radar-note radar-note--warning">
          Frame fuera de la ventana de frescura: se muestra como referencia,
          no como dato actual. No se dibuja sobre el mapa.
        </p>
      )}

      {isStation && decision?.reason === "unknown_age" && (
        <p className="radar-note radar-note--warning">
          No se pudo verificar la antigüedad del frame; no se dibuja sobre el
          mapa.
        </p>
      )}

      {isStation &&
        decision &&
        !decision.renderAllowed &&
        !decision.stale &&
        decision.reason !== "unknown_age" && (
          <p className="radar-note radar-note--warning">
            Este radar no tiene georreferenciación suficiente; su imagen no se
            dibuja sobre el mapa.
          </p>
        )}

      {overlayError && (
        <p className="radar-note radar-note--warning">
          No se pudo cargar la imagen del overlay en el mapa.
        </p>
      )}

      {isStation && frames.length > 0 && (
        <div className="radar-frames">
          <button
            className="btn btn-secondary"
            onClick={() => stepFrame(-1)}
            disabled={frameIndex <= 0}
            aria-label="Frame anterior"
          >
            ‹
          </button>
          <span className="radar-frames__label">
            frame {frameIndex + 1}/{frames.length}
            {currentFrame ? ` · ${stampInfo(currentFrame.stamp)?.label}` : ""}
          </span>
          <button
            className="btn btn-secondary"
            onClick={() => stepFrame(1)}
            disabled={frameIndex >= frames.length - 1}
            aria-label="Frame más reciente"
          >
            ›
          </button>
        </div>
      )}
    </div>
  );
}
