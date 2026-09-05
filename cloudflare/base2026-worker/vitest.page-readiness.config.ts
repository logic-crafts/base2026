import { defineConfig } from "vitest/config";
import { cloudflareTest } from "@cloudflare/vitest-pool-workers";

export default defineConfig({
  plugins: [cloudflareTest({ miniflare: { compatibilityDate: "2026-08-19", compatibilityFlags: ["nodejs_compat"] } })],
  test: { include: ["tests/page-readiness.spec.ts"], testTimeout: 10000 },
});
