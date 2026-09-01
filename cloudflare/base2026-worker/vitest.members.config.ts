import { defineConfig } from "vitest/config";
import { cloudflareTest } from "@cloudflare/vitest-pool-workers";

export default defineConfig({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: "./wrangler.members-local.jsonc" },
    }),
  ],
  test: {
    include: ["tests/member-*.test.ts"],
  },
});
