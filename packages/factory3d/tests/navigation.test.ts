import assert from "node:assert/strict";
import { PerspectiveCamera, Vector3 } from "three";
import { OFFICE_IDS, createScenarioSnapshot, scenarioProvider } from "../src/data";
import {
  clampZoom,
  cycleOffice,
  isTap,
  OFFICE_POSITIONS,
  inspectorAnimationTransition,
  overviewCameraDistance,
  routeBetween,
  routeLength,
  sampleRoute,
  START_POINT,
} from "../src/navigation";

async function run(): Promise<void> {
  assert.deepEqual(OFFICE_IDS, ["growth", "directories", "product", "design", "media", "engineering", "pipeline", "creator"]);
  const snapshot = createScenarioSnapshot();
  assert.equal(snapshot.mode, "scenario");
  assert.equal(snapshot.label, "Scenario — not live operations");
  assert.equal(snapshot.offices.length, 8);
  assert.equal(snapshot.stageId, "rights-review");
  assert.equal(snapshot.offices.some((office) => office.id === "pipeline"), true);
  assert.equal(JSON.stringify(snapshot).includes("task_id"), false);
  assert.equal(JSON.stringify(snapshot).includes("private"), false);

  const providerSnapshot = await scenarioProvider.getSnapshot();
  assert.deepEqual(providerSnapshot, snapshot);

  const route = routeBetween(START_POINT, "growth");
  assert.equal(route[0].x, START_POINT.x);
  assert.equal(route.at(-1)?.x, OFFICE_POSITIONS.growth.x);
  assert.equal(route.at(-1)?.z, OFFICE_POSITIONS.growth.z);
  assert.ok(routeLength(route) > 0);
  assert.deepEqual(sampleRoute(route, 0), route[0]);
  assert.deepEqual(sampleRoute(route, 1), route.at(-1));
  const halfway = sampleRoute(route, 0.5);
  assert.ok(Number.isFinite(halfway.x) && Number.isFinite(halfway.z));

  assert.equal(isTap({ x: 10, z: 10 }, { x: 14, z: 13 }), true);
  assert.equal(isTap({ x: 10, z: 10 }, { x: 18, z: 10 }), false);
  assert.equal(clampZoom(1), 14);
  assert.equal(clampZoom(100), 36);
  assert.equal(cycleOffice("growth", -1), "creator");
  assert.equal(cycleOffice("creator", 1), "growth");

  const desktopFit = overviewCameraDistance(16 / 10);
  const portraitFit = overviewCameraDistance(9 / 16);
  assert.ok(Number.isFinite(desktopFit) && desktopFit > 0);
  assert.ok(portraitFit > desktopFit, "portrait overview needs more camera distance");
  for (const aspect of [899 / 622, 390 / 520, 9 / 16]) {
    const camera = new PerspectiveCamera(38, aspect, 0.1, 500);
    camera.position.set(26, 23, 28).setLength(overviewCameraDistance(aspect));
    camera.lookAt(0, 0, 0);
    camera.updateMatrixWorld(true);
    let widest = 0;
    for (const x of [-21.5, 21.5]) for (const y of [0, 4.2]) for (const z of [-13, 13]) {
      const projected = new Vector3(x, y, z).project(camera);
      assert.ok(Math.abs(projected.x) < 0.94 && Math.abs(projected.y) < 0.94, "all world corners fit with a visible margin");
      widest = Math.max(widest, Math.abs(projected.x), Math.abs(projected.y));
    }
    assert.ok(widest > 0.8, "the overview uses its canvas without excessive empty space");
  }
  assert.deepEqual(inspectorAnimationTransition("idle", false), { state: "idle", changed: false });
  assert.deepEqual(inspectorAnimationTransition("idle", true), { state: "walk", changed: true });
  assert.deepEqual(inspectorAnimationTransition("walk", true), { state: "walk", changed: false });
  assert.deepEqual(inspectorAnimationTransition("walk", false), { state: "idle", changed: true });

  process.stdout.write("navigation, camera projection and data contract checks passed\n");
}

void run();
