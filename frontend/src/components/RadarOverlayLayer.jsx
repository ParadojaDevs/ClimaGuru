// Capa de overlay de radar sobre el mapa Leaflet.
//
// Recibe bounds explicitos del backend (nunca se calculan por tamano de
// pantalla ni se comparten entre radares). La capa se desmonta si no es
// visible, si los bounds son invalidos o si la imagen falla, y se vuelve a
// montar (por `key`) cuando cambia la URL, evitando capas duplicadas.

import { useEffect, useState } from "react";
import { ImageOverlay } from "react-leaflet";

import { clampOpacity, toLeafletBounds } from "./radarOverlayPolicy";

const OVERLAY_Z_INDEX = 350;

export default function RadarOverlayLayer({
  url,
  bounds,
  opacity = 0.65,
  visible = true,
  zIndex = OVERLAY_Z_INDEX,
  onError,
}) {
  const [failedUrl, setFailedUrl] = useState(null);
  const position = toLeafletBounds(bounds);

  // Un cambio de URL habilita un nuevo intento de carga.
  useEffect(() => {
    if (failedUrl && failedUrl !== url) {
      setFailedUrl(null);
    }
  }, [url, failedUrl]);

  if (!url || !visible || !position || failedUrl === url) {
    return null;
  }

  return (
    <ImageOverlay
      key={url}
      url={url}
      bounds={position}
      opacity={clampOpacity(opacity)}
      zIndex={zIndex}
      className="radar-overlay-image"
      alt="Reflectividad de radar IDEAM"
      eventHandlers={{
        error: () => {
          setFailedUrl(url);
          if (onError) onError(url);
        },
      }}
    />
  );
}
