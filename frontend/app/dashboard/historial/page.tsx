"use client";

import { useEffect, useState } from "react";
import {
  History,
  MapPin,
  ChevronDown,
  ChevronUp,
  RefreshCcw,
  Thermometer,
  Droplets,
  Wind,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";
import type { Consulta } from "@/lib/types";

const DEMO_HISTORY: Consulta[] = [
  {
    id: 1,
    usuario_id: 1,
    tipo_consulta: "actual",
    ciudad: "Ciudad de Mexico",
    latitud: 19.4326,
    longitud: -99.1332,
    fecha_inicio: null,
    fecha_fin: null,
    formato: "json",
    parametros: null,
    respuesta_api: null,
    promedios: null,
    estado: "completada",
    creada_en: "2026-02-08T14:30:00",
    datos_clima: {
      id: 1,
      consulta_id: 1,
      temperatura: 24.5,
      presion: 1015,
      humedad: 58,
      viento_vel: 14.2,
      viento_dir: "NE",
      fuentes: "OpenWeatherMap",
      guardado_en: "2026-02-08T14:30:05",
    },
  },
  {
    id: 2,
    usuario_id: 1,
    tipo_consulta: "pronostico",
    ciudad: "Guadalajara",
    latitud: 20.6597,
    longitud: -103.3496,
    fecha_inicio: "2026-02-08",
    fecha_fin: "2026-02-13",
    formato: "json",
    parametros: null,
    respuesta_api: null,
    promedios: null,
    estado: "completada",
    creada_en: "2026-02-07T09:15:00",
    datos_clima: {
      id: 2,
      consulta_id: 2,
      temperatura: 28.1,
      presion: 1012,
      humedad: 45,
      viento_vel: 8.5,
      viento_dir: "S",
      fuentes: "WeatherAPI",
      guardado_en: "2026-02-07T09:15:03",
    },
  },
  {
    id: 3,
    usuario_id: 1,
    tipo_consulta: "actual",
    ciudad: "Monterrey",
    latitud: 25.6866,
    longitud: -100.3161,
    fecha_inicio: null,
    fecha_fin: null,
    formato: "json",
    parametros: null,
    respuesta_api: null,
    promedios: null,
    estado: "completada",
    creada_en: "2026-02-06T16:45:00",
    datos_clima: {
      id: 3,
      consulta_id: 3,
      temperatura: 32.0,
      presion: 1008,
      humedad: 38,
      viento_vel: 20.1,
      viento_dir: "NO",
      fuentes: "OpenWeatherMap",
      guardado_en: "2026-02-06T16:45:02",
    },
  },
  {
    id: 4,
    usuario_id: 1,
    tipo_consulta: "historico",
    ciudad: "Bogota",
    latitud: 4.711,
    longitud: -74.0721,
    fecha_inicio: "2026-01-01",
    fecha_fin: "2026-01-31",
    formato: "json",
    parametros: null,
    respuesta_api: null,
    promedios: null,
    estado: "error",
    creada_en: "2026-02-05T11:20:00",
  },
];

const TYPE_LABELS: Record<string, string> = {
  actual: "Actual",
  pronostico: "Pronostico",
  historico: "Historico",
};

const STATUS_VARIANT: Record<string, "default" | "secondary" | "destructive"> =
  {
    completada: "default",
    pendiente: "secondary",
    error: "destructive",
  };

export default function HistorialPage() {
  const [consultas, setConsultas] = useState<Consulta[]>(DEMO_HISTORY);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  function loadHistory() {
    setLoading(true);
    api
      .get<{ consultas: Consulta[] }>("/consultas")
      .then((res) => setConsultas(res.consultas))
      .catch(() => setConsultas(DEMO_HISTORY))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    loadHistory();
  }, []);

  function toggleExpand(id: number) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function formatDate(iso: string) {
    return new Date(iso).toLocaleDateString("es-MX", {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Historial de Consultas
          </h1>
          <p className="text-sm text-muted-foreground">
            Revisa todas tus consultas climaticas anteriores
          </p>
        </div>
        <Button variant="outline" onClick={loadHistory} disabled={loading}>
          <RefreshCcw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Actualizar
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : consultas.length === 0 ? (
        <Card className="border-border/50">
          <CardContent className="flex flex-col items-center gap-3 py-12">
            <History className="h-10 w-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Aun no has realizado consultas
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {consultas.map((c) => {
            const isOpen = expanded.has(c.id);
            return (
              <Card key={c.id} className="border-border/50">
                <CardContent className="p-0">
                  <button
                    type="button"
                    onClick={() => toggleExpand(c.id)}
                    className="flex w-full items-center justify-between p-4 text-left"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                        <MapPin className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-card-foreground">
                          {c.ciudad || `${c.latitud}, ${c.longitud}`}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatDate(c.creada_en)}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary" className="text-xs">
                        {TYPE_LABELS[c.tipo_consulta] ?? c.tipo_consulta}
                      </Badge>
                      <Badge
                        variant={STATUS_VARIANT[c.estado] ?? "secondary"}
                        className="text-xs capitalize"
                      >
                        {c.estado}
                      </Badge>
                      {isOpen ? (
                        <ChevronUp className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      )}
                    </div>
                  </button>

                  {isOpen && c.datos_clima && (
                    <div className="border-t border-border px-4 pb-4 pt-3">
                      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                        {c.datos_clima.temperatura != null && (
                          <div className="flex items-center gap-2 rounded-lg bg-secondary p-3">
                            <Thermometer className="h-4 w-4 shrink-0 text-chart-3" />
                            <div>
                              <p className="text-xs text-muted-foreground">
                                Temp.
                              </p>
                              <p className="text-sm font-semibold text-secondary-foreground">
                                {c.datos_clima.temperatura}°C
                              </p>
                            </div>
                          </div>
                        )}
                        {c.datos_clima.humedad != null && (
                          <div className="flex items-center gap-2 rounded-lg bg-secondary p-3">
                            <Droplets className="h-4 w-4 shrink-0 text-primary" />
                            <div>
                              <p className="text-xs text-muted-foreground">
                                Humedad
                              </p>
                              <p className="text-sm font-semibold text-secondary-foreground">
                                {c.datos_clima.humedad}%
                              </p>
                            </div>
                          </div>
                        )}
                        {c.datos_clima.viento_vel != null && (
                          <div className="flex items-center gap-2 rounded-lg bg-secondary p-3">
                            <Wind className="h-4 w-4 shrink-0 text-accent" />
                            <div>
                              <p className="text-xs text-muted-foreground">
                                Viento
                              </p>
                              <p className="text-sm font-semibold text-secondary-foreground">
                                {c.datos_clima.viento_vel} km/h
                              </p>
                            </div>
                          </div>
                        )}
                        {c.datos_clima.fuentes && (
                          <div className="flex items-center gap-2 rounded-lg bg-secondary p-3">
                            <div>
                              <p className="text-xs text-muted-foreground">
                                Fuente
                              </p>
                              <p className="text-sm font-semibold text-secondary-foreground">
                                {c.datos_clima.fuentes}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {isOpen && !c.datos_clima && (
                    <div className="border-t border-border px-4 pb-4 pt-3">
                      <p className="text-sm text-muted-foreground">
                        Sin datos de clima disponibles para esta consulta.
                      </p>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
