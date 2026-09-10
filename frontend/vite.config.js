// SPDX-License-Identifier: MIT
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          "react-core": ["react", "react-dom", "react-router-dom"],
          "data-tools": ["@tanstack/react-query", "@tanstack/react-table"],
          charts: ["recharts"],
        },
      },
    },
  },
});
