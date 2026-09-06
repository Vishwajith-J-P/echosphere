import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: loadEnv(mode, '.', '').ECHOSPHERE_API_PROXY ?? "http://127.0.0.1:8000",
        changeOrigin: false,
      },
    },
  },
}));
