import { createFactoryApp } from "./main";

/**
 * Public entrypoint: the authored scenario is the only automatic bootstrap.
 * Private pages import createFactoryApp from main.ts and inject their own
 * read-only provider instead.
 */
void createFactoryApp().catch((error: unknown) => {
  console.error("Factory startup failed", error);
  const fallback = document.getElementById("webgl-fallback");
  if (fallback) fallback.hidden = false;
});
