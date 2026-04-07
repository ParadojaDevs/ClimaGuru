"use client";

import React from "react"

import { useState } from "react";
import {
  Cloud,
  Search,
  Thermometer,
  Droplets,
  Wind,
  Gauge,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { WeatherMap } from "@/components/weather-map";
import { api } from "@/lib/api-client";
import type { Consulta } from "@/lib/types";

interface WeatherResult {
  consulta: Consulta;
  datos_clima?: {
    temperatura: number | null;
    humedad: number | null;
    presion: number | null;
    viento_vel: number | null;
    viento_dir: string | null;
  };
}

export default function MapaPage() {
  const [ciudad, setCiudad] = useState("");
  const [lat, setLat] = useState<number | null>(null);
  const [lng, setLng] = useState<number | null>(null);
  const [tipo, setTipo] = useState("actual");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WeatherResult | null>(null);
  const [error, setError] = useState("");

  function handleMapClick(latitude: number, longitude: number) {
    setLat(latitude);
    setLng(longitude);
    setCiudad("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);

    try {
      const payload: Record<string, unknown> = {
        tipo_consulta: tipo,
        formato: "json",
      };

      if (ciudad.trim()) {
        payload.ciudad = ciudad.trim();
      } else if (lat !== null && lng !== null) {
        payload.latitud = lat;
        payload.longitud = lng;
      } else {
        setError("Selecciona una ubicacion en el mapa o escribe una ciudad");
        setLoading(false);
        return;
      }

      const data = await api.post<WeatherResult>("/consultas", payload);
      setResult(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Error al consultar el clima",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Mapa Interactivo
        </h1>
        <p className="text-sm text-muted-foreground">
          Haz clic en el mapa o ingresa una ciudad para consultar el clima
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {/* Map */}
        <Card className="border-border/50 lg:col-span-2">
          <CardContent className="p-0 overflow-hidden rounded-lg">
            <WeatherMap
              onLocationSelect={handleMapClick}
              selectedLat={lat}
              selectedLng={lng}
            />
          </CardContent>
        </Card>

        {/* Query form */}
        <div className="flex flex-col gap-4">
          <Card className="border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base text-card-foreground">
                <Search className="h-4 w-4" />
                Consulta de Clima
              </CardTitle>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <div className="flex flex-col gap-2">
                  <Label htmlFor="ciudad">Ciudad</Label>
                  <Input
                    id="ciudad"
                    value={ciudad}
                    onChange={(e) => {
                      setCiudad(e.target.value);
                      if (e.target.value) {
                        setLat(null);
                        setLng(null);
                      }
                    }}
                    placeholder="Ej: Ciudad de Mexico"
                  />
                </div>

                {lat !== null && lng !== null && (
                  <div className="rounded-lg bg-secondary px-3 py-2 text-xs text-secondary-foreground">
                    Coordenadas: {lat}, {lng}
                  </div>
                )}

                <div className="flex flex-col gap-2">
                  <Label>Tipo de consulta</Label>
                  <Select value={tipo} onValueChange={setTipo}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="actual">Clima actual</SelectItem>
                      <SelectItem value="pronostico">Pronostico 5 dias</SelectItem>
                      <SelectItem value="historico">Historico</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {error && (
                  <p className="text-sm text-destructive">{error}</p>
                )}

                <Button type="submit" disabled={loading} className="w-full">
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary-foreground border-t-transparent" />
                      Consultando...
                    </span>
                  ) : (
                    <span className="flex items-center gap-2">
                      <Cloud className="h-4 w-4" />
                      Consultar Clima
                    </span>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Results */}
          {result && result.datos_clima && (
            <Card className="border-border/50">
              <CardHeader className="pb-3">
                <CardTitle className="text-base text-card-foreground">
                  Resultado - {result.consulta.ciudad || "Coordenadas"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3">
                  {result.datos_clima.temperatura != null && (
                    <div className="flex items-center gap-2 rounded-lg bg-secondary p-3">
                      <Thermometer className="h-4 w-4 text-chart-3" />
                      <div>
                        <p className="text-xs text-muted-foreground">Temp.</p>
                        <p className="text-sm font-semibold text-secondary-foreground">
                          {result.datos_clima.temperatura}°C
                        </p>
                      </div>
                    </div>
                  )}
                  {result.datos_clima.humedad != null && (
                    <div className="flex items-center gap-2 rounded-lg bg-secondary p-3">
                      <Droplets className="h-4 w-4 text-primary" />
                      <div>
                        <p className="text-xs text-muted-foreground">Humedad</p>
                        <p className="text-sm font-semibold text-secondary-foreground">
                          {result.datos_clima.humedad}%
                        </p>
                      </div>
                    </div>
                  )}
                  {result.datos_clima.viento_vel != null && (
                    <div className="flex items-center gap-2 rounded-lg bg-secondary p-3">
                      <Wind className="h-4 w-4 text-accent" />
                      <div>
                        <p className="text-xs text-muted-foreground">Viento</p>
                        <p className="text-sm font-semibold text-secondary-foreground">
                          {result.datos_clima.viento_vel} km/h{" "}
                          {result.datos_clima.viento_dir ?? ""}
                        </p>
                      </div>
                    </div>
                  )}
                  {result.datos_clima.presion != null && (
                    <div className="flex items-center gap-2 rounded-lg bg-secondary p-3">
                      <Gauge className="h-4 w-4 text-chart-4" />
                      <div>
                        <p className="text-xs text-muted-foreground">Presion</p>
                        <p className="text-sm font-semibold text-secondary-foreground">
                          {result.datos_clima.presion} hPa
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
