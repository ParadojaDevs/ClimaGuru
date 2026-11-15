// Config temporal para smoke test: usa un cacheDir alterno porque
// node_modules/.vite esta bloqueado por otro proceso en esta maquina.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  cacheDir: "node_modules/.vite-smoke",
  server: {
    port: 5173,
    strictPort: true,
  },
});
