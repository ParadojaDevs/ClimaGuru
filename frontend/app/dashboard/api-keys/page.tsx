"use client";

import React from "react"

import { useEffect, useState } from "react";
import {
  Key,
  Plus,
  Trash2,
  Eye,
  EyeOff,
  ShieldCheck,
  ShieldOff,
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
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api-client";
import type { ApiKey } from "@/lib/types";

const PROVIDERS = [
  { value: "openweathermap", label: "OpenWeatherMap" },
  { value: "weatherapi", label: "WeatherAPI" },
  { value: "visualcrossing", label: "Visual Crossing" },
  { value: "otro", label: "Otro proveedor" },
];

// Demo data
const DEMO_KEYS: ApiKey[] = [
  {
    id: 1,
    usuario_id: 1,
    proveedor: "openweathermap",
    api_key: "sk-demo-abc123def456ghi789",
    activa: true,
    creada_en: "2026-01-15T10:30:00",
  },
  {
    id: 2,
    usuario_id: 1,
    proveedor: "weatherapi",
    api_key: "wa-demo-xyz987uvw654rst321",
    activa: true,
    creada_en: "2026-01-20T14:15:00",
  },
  {
    id: 3,
    usuario_id: 1,
    proveedor: "visualcrossing",
    api_key: "vc-demo-mnop456qrst789",
    activa: false,
    creada_en: "2025-12-10T08:00:00",
  },
];

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKey[]>(DEMO_KEYS);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [proveedor, setProveedor] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [visibleKeys, setVisibleKeys] = useState<Set<number>>(new Set());
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get<{ api_keys: ApiKey[] }>("/api-keys")
      .then((res) => setKeys(res.api_keys))
      .catch(() => setKeys(DEMO_KEYS))
      .finally(() => setLoading(false));
  }, []);

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const newKey = await api.post<ApiKey>("/api-keys", {
        proveedor,
        api_key: apiKey,
      });
      setKeys((prev) => [...prev, newKey]);
      setShowForm(false);
      setProveedor("");
      setApiKey("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  }

  async function handleToggle(id: number, activa: boolean) {
    try {
      await api.put(`/api-keys/${id}`, { activa: !activa });
      setKeys((prev) =>
        prev.map((k) => (k.id === id ? { ...k, activa: !activa } : k)),
      );
    } catch {
      // silently fail for demo
    }
  }

  async function handleDelete(id: number) {
    try {
      await api.delete(`/api-keys/${id}`);
      setKeys((prev) => prev.filter((k) => k.id !== id));
    } catch {
      // silently fail for demo
    }
  }

  function toggleVisibility(id: number) {
    setVisibleKeys((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function maskKey(key: string) {
    if (key.length <= 8) return "********";
    return key.slice(0, 4) + "****" + key.slice(-4);
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            API Keys
          </h1>
          <p className="text-sm text-muted-foreground">
            Administra las claves de tus proveedores de clima
          </p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>
          <Plus className="mr-2 h-4 w-4" />
          Nueva Key
        </Button>
      </div>

      {/* Add form */}
      {showForm && (
        <Card className="border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-card-foreground">
              Agregar API Key
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form
              onSubmit={handleAdd}
              className="flex flex-col gap-4 sm:flex-row sm:items-end"
            >
              <div className="flex flex-col gap-2 sm:w-48">
                <Label>Proveedor</Label>
                <Select value={proveedor} onValueChange={setProveedor}>
                  <SelectTrigger>
                    <SelectValue placeholder="Seleccionar..." />
                  </SelectTrigger>
                  <SelectContent>
                    {PROVIDERS.map((p) => (
                      <SelectItem key={p.value} value={p.value}>
                        {p.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex flex-1 flex-col gap-2">
                <Label>API Key</Label>
                <Input
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Pega tu clave de API aqui"
                  required
                />
              </div>
              <Button type="submit" disabled={saving || !proveedor}>
                {saving ? "Guardando..." : "Guardar"}
              </Button>
            </form>
            {error && (
              <p className="mt-2 text-sm text-destructive">{error}</p>
            )}
          </CardContent>
        </Card>
      )}

      {/* Keys list */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
        </div>
      ) : keys.length === 0 ? (
        <Card className="border-border/50">
          <CardContent className="flex flex-col items-center gap-3 py-12">
            <Key className="h-10 w-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              No tienes API keys configuradas
            </p>
            <Button variant="outline" onClick={() => setShowForm(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Agregar primera key
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {keys.map((k) => (
            <Card key={k.id} className="border-border/50">
              <CardContent className="flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <Key className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-semibold text-card-foreground capitalize">
                        {k.proveedor}
                      </p>
                      <Badge
                        variant={k.activa ? "default" : "secondary"}
                        className="text-xs"
                      >
                        {k.activa ? "Activa" : "Inactiva"}
                      </Badge>
                    </div>
                    <p className="font-mono text-xs text-muted-foreground">
                      {visibleKeys.has(k.id) ? k.api_key : maskKey(k.api_key)}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => toggleVisibility(k.id)}
                    aria-label={
                      visibleKeys.has(k.id) ? "Ocultar key" : "Mostrar key"
                    }
                  >
                    {visibleKeys.has(k.id) ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleToggle(k.id, k.activa)}
                    aria-label={k.activa ? "Desactivar" : "Activar"}
                  >
                    {k.activa ? (
                      <ShieldCheck className="h-4 w-4 text-chart-4" />
                    ) : (
                      <ShieldOff className="h-4 w-4 text-muted-foreground" />
                    )}
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDelete(k.id)}
                    aria-label="Eliminar key"
                  >
                    <Trash2 className="h-4 w-4 text-destructive" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
