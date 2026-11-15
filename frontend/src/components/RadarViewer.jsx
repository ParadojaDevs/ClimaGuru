// Visor de radar IDEAM.
// - Compuesto nacional: PNG opaco (con basemap), imagen mas reciente.
// - Por radar: PNG transparente de reflectividad (z). Puede fallar con 502 si
//   el radar no tiene scans recientes (estado honesto por radar).
// - Navegacion temporal: frames del manifiesto IDEAM (ultimos ~3 h).

import { useCallback, useEffect, useState } from "react";
import {
  fetchRadarLatest,
  fetchRadarOverlay,
  fetchRadarFrames,
} from "../../services/api";

const COMPOSITE = "composite";

// Los sellos IDEAM usan hora local Colombia (UTC-5), formato YYMMDDHHMM.
function stampInfo(stamp) {
  if (!stamp || stamp.length !== 10) return null;
  const yy = stamp.slice(0, 2);
  const mo = stamp.slice(2, 4);
  const dd = stamp.slice(4, 6);
  const hh = stamp.slice(6, 8);
  const mi = stamp.slice(8, 10);
  const utcMs = Date.UTC(2000 + Number(yy), Number(mo) - 1, Number(dd), Number(hh) + 5, Number(mi));
  const ageMin = Math.round((Date.now() - utcMs) / 60000);
  return {
    label: `${dd}/${mo} ${hh}:${mi} COT`,
    ageMin,
  };
}

function ageText(ageMin) {
  if (Number.isNaN(ageMin)) return "";
  if (ageMin < 1) return "hace segundos";
  if (ageMin < 90) return `hace ${ageMin} min`;
  return `hace ${Math.round(ageMin / 60)} h`;
}

function Spinner() {
  return <div className="loading-spinner loading-spinner--inline" />;
}

export default function RadarViewer({ stations, focusId }) {
  const [source, setSource] = useState(focusId || COMPOSITE);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [composite, setComposite] = useState(null);
  const [overlay, setOverlay] = useState(null); // {stamp,url,station}
  const [frames, setFrames] = useState([]);
  const [frameIndex, setFrameIndex] = useState(0);

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
          setOverlay({ ...okOverlay, fromFrames: false });
        } else {
          // Fallback honesto: primer frame del manifiesto.
          setOverlay({
            kind: `overlay:${src}`,
            stamp: okFrames[0].stamp,
            url: okFrames[0].url,
            fromFrames: true,
          });
        }
        setFrames(okFrames);
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
  const active = isStation ? overlay : composite;
  const info = stampInfo(active?.stamp);
  const currentFrame = frames[frameIndex] || null;

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
                  ? `Reflectividad radar ${active.station?.name || source}`
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

      {isStation && frames.length > 0 && (
        <div className="radar-frames">
          <button
            className="btn btn-secondary"
            onClick={() => stepFrame(1)}
            disabled={frameIndex >= frames.length - 1}
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
            onClick={() => stepFrame(-1)}
            disabled={frameIndex <= 0}
            aria-label="Frame más reciente"
          >
            ›
          </button>
        </div>
      )}
    </div>
  );
}
