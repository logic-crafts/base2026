# Base2026 Factory

A separate English browser experience built with Three.js and selected Kenney Factory Kit / Blocky Characters assets. The public entry is `src/public.ts`; it loads a fixed authored scenario. Its character movement and workflow stages illustrate the product and do not report live operations.

Run `npm ci`, `npm test`, then `npm run build:factory`. The production release builder imports a reviewed, hash-pinned copy of the resulting `/factory/` files. Keep `dist/` out of Git. The reproducible source and selected model/texture files belong here; original archive provenance is in `assets/asset-provenance.json` and `assets/LICENSES.md`.

`src/main.ts` also exports `createFactoryApp(provider)` and generic current-snapshot types for a separately built private view. No private provider, endpoint, task IDs, database or snapshot payload belongs in this package or the public release.

Controls support room inspection, manual visits, zoom, rotation, finite scenario stages and reset. Motion pauses while the canvas is offscreen or the tab is hidden; reduced-motion users retain manual controls. WebGL failure leaves the room data usable. The `?qa=1` view displays actual renderer counts and frame samples for review.

Bundled asset and runtime licenses are included under `public/licenses/`.
