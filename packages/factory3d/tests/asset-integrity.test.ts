import { strict as assert } from "node:assert";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

const packageRoot = resolve(import.meta.dirname, "..");
const runtimeRoot = join(packageRoot, "public", "assets", "kenney");
const stagingRoot = join(packageRoot, "assets", "glb");

function referencedUris(filePath: string): string[] {
  const bytes = readFileSync(filePath);
  assert.equal(bytes.toString("ascii", 0, 4), "glTF", filePath + " must be a GLB");
  let offset = 12;
  while (offset + 8 <= bytes.length) {
    const length = bytes.readUInt32LE(offset);
    const type = bytes.readUInt32LE(offset + 4);
    offset += 8;
    const chunk = bytes.subarray(offset, offset + length);
    offset += length;
    if (type !== 0x4e4f534a) continue;
    const json = JSON.parse(chunk.toString("utf8").replace(/\0+$/g, "").trim()) as {
      images?: Array<{ uri?: string }>;
    };
    return (json.images ?? []).flatMap((image) => image.uri ? [image.uri] : []);
  }
  return [];
}

const glbFiles = readdirSync(runtimeRoot).filter((name) => name.endsWith(".glb")).sort();
assert.equal(glbFiles.length, 9, "the first-play allowlist should contain nine GLBs");
const uris = new Set<string>();

for (const file of glbFiles) {
  for (const uri of referencedUris(join(runtimeRoot, file))) {
    assert.match(uri, /^Textures\/[A-Za-z0-9._-]+\.png$/, file + " has an unsafe texture URI");
    uris.add(uri);
    assert.ok(existsSync(join(runtimeRoot, uri)), file + " runtime texture missing: " + uri);
    assert.ok(existsSync(join(stagingRoot, uri)), file + " staging texture missing: " + uri);
    assert.ok(statSync(join(runtimeRoot, uri)).size > 0, file + " runtime texture is empty: " + uri);
  }
}

assert.deepEqual([...uris].sort(), ["Textures/colormap.png", "Textures/texture-a.png", "Textures/texture-b.png"]);
console.log("asset integrity: " + glbFiles.length + " GLBs and " + uris.size + " external textures passed");
