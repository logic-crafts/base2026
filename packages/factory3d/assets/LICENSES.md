# Factory asset record

The first playable uses only bundled GLB files from Kenney's official packs. The source archives were downloaded and inspected on **2026-09-06**. Both publishers' included `License.txt` files state **Creative Commons Zero (CC0)**. Kenney asks for credit as a courtesy; the footer and this record provide it.

| Pack | Publisher page | Download | Archive SHA-256 | License | Selected content |
|---|---|---|---|---|---|
| Factory Kit 3.0 | [kenney.nl/assets/factory-kit](https://kenney.nl/assets/factory-kit) | `kenney_factory-kit_3.0.zip` | `7e31fb2308e90304672bd15cd18fa9d9f02c03731a8cbc57a8e3e1c181dfb0a7` | CC0 1.0 (`License.txt`) | floor, structure wall, wide doorway, machine, conveyor, scanner, screen |
| Blocky Characters 2.0 | [kenney.nl/assets/blocky-characters](https://kenney.nl/assets/blocky-characters) | `kenney_blocky-characters_20.zip` | `5e123859aa0c1598342b600c6db197024a1d63eb9ec531398b310725f589887e` | CC0 1.0 (`License.txt`) | `character-a.glb` inspector, `character-b.glb` worker |

The exact download URLs recorded during inspection were:

- `https://kenney.nl/media/pages/assets/factory-kit/edaac9d4f6-1777639602/kenney_factory-kit_3.0.zip`
- `https://kenney.nl/media/pages/assets/blocky-characters/8369c0cf30-1749547469/kenney_blocky-characters_20.zip`

## Inspection notes

- The selected files are native GLB exports. Their JSON chunks reference exact relative PNGs (Textures/colormap.png, Textures/texture-a.png, and Textures/texture-b.png) from the same official archives; those PNGs are bundled unchanged under both assets/glb/Textures/ and the runtime public/assets/kenney/Textures/ path.
- The external texture bytes and SHA-256 values are recorded in manifest.json, and tests/asset-integrity.test.ts parses every selected GLB to verify the referenced files exist before build.
- The character files contain the clips `idle` and `walk` plus additional clips. The renderer uses only `idle` and `walk`, with one inspector and one ambient worker active.
- The selected files were copied out of their archives and renamed for stable local paths. Mesh data, materials, textures and animation clips were not edited.
- The Factory Kit archive contains many more models; only the allowlisted subset in [`manifest.json`](./asset-provenance.json) enters the first-play build.
- Quaternius was not imported because the native GLB Blocky Characters exports satisfy the worker and inspection loop without adding conversion dependencies.

The visual factory is an authored scenario. Asset animation is illustrative and never establishes that a live AgencyOS process is running.
