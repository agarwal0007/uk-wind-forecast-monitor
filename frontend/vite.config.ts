import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { "/api": process.env.VITE_PROXY_TARGET ?? "http://localhost:8000" },
  },
  build: {
    // recharts is ~560 kB minified (~155 kB gzip) in its own cacheable chunk
    chunkSizeWarningLimit: 650,
    rollupOptions: {
      output: { manualChunks: { recharts: ["recharts"] } },
    },
  },
  test: { environment: "node" },
});
