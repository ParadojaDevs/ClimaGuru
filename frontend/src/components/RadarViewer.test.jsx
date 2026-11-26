import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../services/api", () => ({
  fetchRadarLatest: vi.fn(),
  fetchRadarOverlay: vi.fn(),
  fetchRadarFrames: vi.fn(),
}));

import {
  fetchRadarFrames,
  fetchRadarLatest,
  fetchRadarOverlay,
} from "../../services/api";
import RadarViewer from "./RadarViewer";

const GUA_WARNING =
  "Posición aproximada: bounds derivados de GeoTIFF histórico, sin validación temporal con el PNG.";
const MUN_WARNING =
  "Posición aproximada: bounds derivados de GeoTIFF histórico; discrepancia aproximada de 10,5 km respecto a la estación.";

const guaGeoref = {
  state: "derived",
  visualization: "approximate_with_warning",
  render_allowed: true,
  overlay_enabled: false,
  warning: GUA_WARNING,
  bounds: { west: -73.95, south: 1.75, east: -71.05, north: 3.45 },
};

const munGeoref = {
  ...guaGeoref,
  warning: MUN_WARNING,
  bounds: { west: -78.25, south: 1.35, east: -75.35, north: 3.85 },
};

const barGeoref = {
  state: "assumed",
  visualization: "blocked",
  render_allowed: false,
  overlay_enabled: false,
  warning: null,
  bounds: { west: -75.5, south: 6.5, east: -73.5, north: 8.5 },
};

const carGeoref = {
  ...barGeoref,
  bounds: { west: -72.5, south: 3.5, east: -70.5, north: 5.5 },
};

const stations = [
  { id: "barrancabermeja", code: "BAR", name: "Barrancabermeja", lat: 7.03, lon: -73.85, georef: barGeoref },
  { id: "carimagua", code: "CAR", name: "Carimagua", lat: 4.52, lon: -71.58, georef: carGeoref },
  { id: "guaviare", code: "GUA", name: "Guaviare", lat: 2.53, lon: -72.63, georef: guaGeoref },
  { id: "munchique", code: "MUN", name: "Munchique", lat: 2.61, lon: -76.96, georef: munGeoref },
];

const byId = Object.fromEntries(stations.map((station) => [station.id, station]));

// Sello YYMMDDHHMM en hora local Colombia para "ahora + offset".
function cotStamp(offsetMinutes = 0) {
  const cot = new Date(Date.now() + offsetMinutes * 60000 - 5 * 3600 * 1000);
  const pad = (value) => String(value).padStart(2, "0");
  return `${pad(cot.getUTCFullYear() % 100)}${pad(cot.getUTCMonth() + 1)}${pad(
    cot.getUTCDate()
  )}${pad(cot.getUTCHours())}${pad(cot.getUTCMinutes())}`;
}

function mockOverlay(radarId, offsetMinutes = -2) {
  const station = byId[radarId];
  const stamp = cotStamp(offsetMinutes);
  const url = `https://bart.ideam.gov.co/ospa/${station.code}${stamp}_z_Transp.png`;
  vi.mocked(fetchRadarOverlay).mockResolvedValue({
    kind: `overlay:${radarId}`,
    stamp,
    url,
    station: { code: station.code, name: station.name },
    georef: station.georef,
  });
  return { stamp, url };
}

function lastOverlay(onChange) {
  const calls = onChange.mock.calls;
  return calls.length ? calls[calls.length - 1][0] : undefined;
}

beforeEach(() => {
  vi.mocked(fetchRadarLatest).mockReset();
  vi.mocked(fetchRadarOverlay).mockReset();
  vi.mocked(fetchRadarFrames).mockReset();
  vi.mocked(fetchRadarFrames).mockResolvedValue({ frames: [] });
});

describe("RadarViewer — overlay geografico", () => {
  it("publica el overlay de GUA con bounds y advertencia", async () => {
    const onChange = vi.fn();
    const { url } = mockOverlay("guaviare");

    render(
      <RadarViewer stations={stations} focusId="guaviare" onOverlayChange={onChange} />
    );

    expect(await screen.findByText(GUA_WARNING)).toBeInTheDocument();
    await waitFor(() => {
      expect(lastOverlay(onChange)).toMatchObject({
        radarId: "guaviare",
        code: "GUA",
        url,
        bounds: guaGeoref.bounds,
        warning: GUA_WARNING,
        visible: true,
        opacity: 0.65,
      });
    });
  });

  it("muestra la advertencia especifica de Munchique", async () => {
    const onChange = vi.fn();
    mockOverlay("munchique");

    render(
      <RadarViewer stations={stations} focusId="munchique" onOverlayChange={onChange} />
    );

    expect(await screen.findByText(/10,5 km respecto a la estación/)).toBeInTheDocument();
    await waitFor(() => {
      expect(lastOverlay(onChange)?.warning).toBe(MUN_WARNING);
    });
  });

  it("bloquea BAR y CAR: no publica overlay ni ofrece controles", async () => {
    for (const radarId of ["barrancabermeja", "carimagua"]) {
      const onChange = vi.fn();
      mockOverlay(radarId);

      const { unmount } = render(
        <RadarViewer stations={stations} focusId={radarId} onOverlayChange={onChange} />
      );

      expect(
        await screen.findByText(/no tiene georreferenciación suficiente/)
      ).toBeInTheDocument();
      expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
      expect(screen.queryByRole("slider")).not.toBeInTheDocument();
      expect(lastOverlay(onChange)).toBeNull();

      unmount();
    }
  });

  it("permite ocultar el overlay y ajustar la opacidad", async () => {
    const onChange = vi.fn();
    mockOverlay("guaviare");

    render(
      <RadarViewer stations={stations} focusId="guaviare" onOverlayChange={onChange} />
    );

    const checkbox = await screen.findByRole("checkbox", {
      name: /Mostrar en el mapa/,
    });
    await waitFor(() => expect(lastOverlay(onChange)?.visible).toBe(true));

    fireEvent.click(checkbox);
    await waitFor(() => expect(lastOverlay(onChange)?.visible).toBe(false));

    fireEvent.click(checkbox);
    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: "0.3" } });

    await waitFor(() => expect(lastOverlay(onChange)?.opacity).toBe(0.3));
    expect(screen.getByText("30%")).toBeInTheDocument();
  });

  it("cambia de radar sin dejar el overlay anterior", async () => {
    const onChange = vi.fn();
    mockOverlay("guaviare");

    render(
      <RadarViewer stations={stations} focusId="guaviare" onOverlayChange={onChange} />
    );
    await waitFor(() => expect(lastOverlay(onChange)?.radarId).toBe("guaviare"));

    mockOverlay("munchique");
    fireEvent.click(screen.getByRole("button", { name: "MUN" }));

    await waitFor(() => expect(lastOverlay(onChange)?.radarId).toBe("munchique"));
    expect(lastOverlay(onChange)?.url).toContain("MUN");
  });

  it("no publica el overlay anterior mientras carga el radar nuevo", async () => {
    const onChange = vi.fn();
    const gua = mockOverlay("guaviare");
    const munStamp = cotStamp(-2);
    const munUrl = `https://bart.ideam.gov.co/ospa/MUN${munStamp}_z_Transp.png`;
    let resolveMun;

    vi.mocked(fetchRadarOverlay).mockImplementation((radarId) => {
      if (radarId === "guaviare") {
        return Promise.resolve({
          kind: "overlay:guaviare",
          stamp: gua.stamp,
          url: gua.url,
          station: { code: "GUA", name: "Guaviare" },
          georef: guaGeoref,
        });
      }
      return new Promise((resolve) => {
        resolveMun = () =>
          resolve({
            kind: "overlay:munchique",
            stamp: munStamp,
            url: munUrl,
            station: { code: "MUN", name: "Munchique" },
            georef: munGeoref,
          });
      });
    });

    render(
      <RadarViewer stations={stations} focusId="guaviare" onOverlayChange={onChange} />
    );
    await waitFor(() => expect(lastOverlay(onChange)?.radarId).toBe("guaviare"));

    const callsBefore = onChange.mock.calls.length;
    fireEvent.click(screen.getByRole("button", { name: "MUN" }));

    await waitFor(() => expect(lastOverlay(onChange)).toBeNull());
    const afterClick = onChange.mock.calls.slice(callsBefore).map(([value]) => value);
    expect(afterClick.some((value) => value?.url?.includes("GUA"))).toBe(false);

    resolveMun();
    await waitFor(() => expect(lastOverlay(onChange)?.radarId).toBe("munchique"));
    expect(lastOverlay(onChange)?.url).toBe(munUrl);
  });

  it("limpia el overlay al desmontar", async () => {
    const onChange = vi.fn();
    mockOverlay("guaviare");

    const { unmount } = render(
      <RadarViewer stations={stations} focusId="guaviare" onOverlayChange={onChange} />
    );
    await waitFor(() => expect(lastOverlay(onChange)).not.toBeNull());

    unmount();
    expect(lastOverlay(onChange)).toBeNull();
  });

  it("usa el frame mas reciente como fallback y no dibuja frames antiguos", async () => {
    const onChange = vi.fn();
    const recent = { stamp: cotStamp(-10), url: "https://x/GUA-recent.png" };
    const older = { stamp: cotStamp(-20), url: "https://x/GUA-older.png" };
    vi.mocked(fetchRadarOverlay).mockRejectedValue(new Error("502"));
    vi.mocked(fetchRadarFrames).mockResolvedValue({ frames: [older, recent] });

    render(
      <RadarViewer stations={stations} focusId="guaviare" onOverlayChange={onChange} />
    );

    expect(await screen.findByText(/frame del manifiesto/)).toBeInTheDocument();
    await waitFor(() => expect(lastOverlay(onChange)?.url).toBe(recent.url));

    const stale = { stamp: cotStamp(-120), url: "https://x/GUA-stale.png" };
    vi.mocked(fetchRadarOverlay).mockResolvedValue({
      kind: "overlay:guaviare",
      stamp: stale.stamp,
      url: stale.url,
      station: { code: "GUA", name: "Guaviare" },
      georef: guaGeoref,
    });
    fireEvent.click(screen.getByRole("button", { name: "Actualizar" }));

    expect(
      await screen.findByText(/fuera de la ventana de frescura/)
    ).toBeInTheDocument();
    await waitFor(() => expect(lastOverlay(onChange)).toBeNull());
  });

  it("no dibuja ni atribuye georreferencia faltante cuando la edad es desconocida", async () => {
    const onChange = vi.fn();
    vi.mocked(fetchRadarOverlay).mockResolvedValue({
      kind: "overlay:guaviare",
      stamp: "invalido",
      url: "https://x/GUA-invalid.png",
      station: { code: "GUA", name: "Guaviare" },
      georef: guaGeoref,
    });

    render(
      <RadarViewer stations={stations} focusId="guaviare" onOverlayChange={onChange} />
    );

    expect(
      await screen.findByText(/No se pudo verificar la antigüedad/)
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/no tiene georreferenciación suficiente/)
    ).not.toBeInTheDocument();
    await waitFor(() => expect(lastOverlay(onChange)).toBeNull());
  });
});
