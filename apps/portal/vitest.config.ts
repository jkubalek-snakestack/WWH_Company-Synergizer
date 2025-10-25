import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["tests/**/*.test.ts"],
  },
  resolve: {
    alias: {
      "@/lib": new URL("./lib", import.meta.url).pathname,
      "@/server": new URL("./server", import.meta.url).pathname,
    },
  },
});
