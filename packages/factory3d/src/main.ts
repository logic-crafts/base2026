import * as THREE from "three";
import { GLTFLoader, type GLTF } from "three/addons/loaders/GLTFLoader.js";
import * as SkeletonUtils from "three/addons/utils/SkeletonUtils.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  createScenarioSnapshot,
  OFFICES,
  OFFICE_IDS,
  SCENARIO_STAGES,
  scenarioProvider,
  type FactoryDataProvider,
  type FactoryOffice,
  type CurrentOffice,
  type FactorySnapshot,
  type OfficeId,
} from "./data";
import {
  clampZoom,
  cycleOffice,
  inspectorAnimationTransition,
  isTap,
  OFFICE_POSITIONS,
  overviewCameraDistance,
  routeBetween,
  sampleRoute,
  START_POINT,
  type InspectorAnimationState,
  type Point3,
} from "./navigation";
import "./styles.css";

const ASSET_PATH = (name: string): string => `${import.meta.env.BASE_URL}assets/kenney/${name}`;

const ASSET_URLS = {
  floor: ASSET_PATH("factory-floor-large.glb"),
  wall: ASSET_PATH("factory-structure-wall.glb"),
  doorway: ASSET_PATH("factory-structure-doorway-wide.glb"),
  machine: ASSET_PATH("factory-machine.glb"),
  conveyor: ASSET_PATH("factory-conveyor-long.glb"),
  scanner: ASSET_PATH("factory-scanner-low.glb"),
  screen: ASSET_PATH("factory-screen-wide.glb"),
  inspector: ASSET_PATH("character-inspector.glb"),
  worker: ASSET_PATH("character-worker.glb"),
} as const;

type AssetKey = keyof typeof ASSET_URLS;
type LoadedAssets = Partial<Record<AssetKey, GLTF>>;
type PanelTab = "tasks" | "process" | "receipts";

interface Actor {
  root: THREE.Object3D;
  mixer: THREE.AnimationMixer;
  idle?: THREE.AnimationAction;
  walk?: THREE.AnimationAction;
  home: THREE.Vector3;
}

interface RoomVisual {
  group: THREE.Group;
  marker: THREE.Mesh;
  floor: THREE.Mesh;
}

type RendererStatus = "loading" | "ready" | "context-lost" | "recovering" | "unavailable" | "error";

interface TelemetryState {
  loadedAssets: number;
  totalAssets: number;
  renderedFrames: number;
  sampleStartedAt: number | null;
  fps: number | null;
  frameSample: number;
  status: RendererStatus;
}

const NAVY = 0x091b3d;

function byId<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) throw new Error(`Missing factory element #${id}`);
  return element as T;
}

function displayTime(value: string | undefined): string {
  if (!value || !Number.isFinite(Date.parse(value))) return "Unknown";
  return new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit", timeZone: "UTC", timeZoneName: "short" }).format(new Date(value));
}

function isInteractiveTarget(target: EventTarget | null): boolean {
  return target instanceof HTMLElement && Boolean(target.closest("button, a, input, textarea, select, [contenteditable='true']"));
}

function isFactoryKeyboardScope(target: EventTarget | null): boolean {
  if (!(target instanceof Element)) return target === document.body;
  return target === document.body || Boolean(target.closest("#canvas-root, #room-list"));
}

function disposeMaterial(material: THREE.Material): void {
  const candidate = material as THREE.Material & Record<string, unknown>;
  Object.values(candidate).forEach((value) => {
    if (value && typeof value === "object" && "isTexture" in value && typeof (value as THREE.Texture).dispose === "function") {
      (value as THREE.Texture).dispose();
    }
  });
  material.dispose();
}

function disposeObjectResources(object: THREE.Object3D): void {
  object.traverse((child) => {
    const resource = child as THREE.Object3D & {
      geometry?: THREE.BufferGeometry;
      material?: THREE.Material | THREE.Material[];
    };
    if (!resource.geometry || !resource.material) return;
    resource.geometry.dispose();
    const materials = Array.isArray(resource.material) ? resource.material : [resource.material];
    materials.forEach(disposeMaterial);
  });
}

function disposeLoadedAssets(assets: LoadedAssets): void {
  const disposed = new Set<THREE.BufferGeometry | THREE.Material>();
  Object.values(assets).forEach((gltf) => {
    gltf?.scene.traverse((child) => {
      if (!(child instanceof THREE.Mesh)) return;
      if (!disposed.has(child.geometry)) {
        child.geometry.dispose();
        disposed.add(child.geometry);
      }
      const materials = Array.isArray(child.material) ? child.material : [child.material];
      materials.forEach((material) => {
        if (!disposed.has(material)) {
          disposeMaterial(material);
          disposed.add(material);
        }
      });
    });
  });
}

function makeMaterial(color: number, roughness = 0.78, metalness = 0.04): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({ color, roughness, metalness });
}

function cloneAsset(assets: LoadedAssets, key: AssetKey): THREE.Object3D | null {
  const loaded = assets[key];
  return loaded ? loaded.scene.clone(true) : null;
}

function addAsset(
  parent: THREE.Object3D,
  assets: LoadedAssets,
  key: AssetKey,
  position: THREE.Vector3,
  scale: number | THREE.Vector3,
  rotationY = 0,
): THREE.Object3D | null {
  const object = cloneAsset(assets, key);
  if (!object) return null;
  object.position.copy(position);
  if (typeof scale === "number") object.scale.setScalar(scale);
  else object.scale.copy(scale);
  object.rotation.y = rotationY;
  parent.add(object);
  return object;
}

function createLabelSprite(text: string, accent: number): THREE.Sprite {
  const canvas = document.createElement("canvas");
  canvas.width = 720;
  canvas.height = 180;
  const context = canvas.getContext("2d");
  if (!context) throw new Error("Canvas text context unavailable");
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "rgba(8, 27, 61, 0.92)";
  context.roundRect(8, 8, canvas.width - 16, canvas.height - 16, 28);
  context.fill();
  context.fillStyle = `#${accent.toString(16).padStart(6, "0")}`;
  context.fillRect(25, 31, 12, canvas.height - 62);
  context.fillStyle = "#ffffff";
  context.font = "800 38px Avenir Next, sans-serif";
  context.fillText(text, 58, 82);
  context.fillStyle = "#b9c9e7";
  context.font = "600 22px Avenir Next, sans-serif";
  context.fillText("INSPECTION ROOM", 58, 122);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false }));
  sprite.scale.set(3.3, 0.83, 1);
  sprite.renderOrder = 8;
  return sprite;
}

function addBox(parent: THREE.Object3D, size: THREE.Vector3, position: THREE.Vector3, material: THREE.Material): THREE.Mesh {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(size.x, size.y, size.z), material);
  mesh.position.copy(position);
  parent.add(mesh);
  return mesh;
}

function addRoomShell(
  world: THREE.Group,
  office: FactoryOffice,
  assets: LoadedAssets,
  index: number,
): RoomVisual {
  const center = OFFICE_POSITIONS[office.id];
  const group = new THREE.Group();
  group.name = `room-${office.id}`;
  group.userData.officeId = office.id;
  group.position.set(center.x, 0, center.z);
  world.add(group);

  const floorMaterial = makeMaterial(office.color, 0.83, 0.02);
  const floorAsset = addAsset(group, assets, "floor", new THREE.Vector3(0, 0.08, 0), new THREE.Vector3(4.5, 1, 3.55));
  const floor = (floorAsset?.getObjectByProperty("isMesh", true) as THREE.Mesh | undefined)
    ?? addBox(group, new THREE.Vector3(9.1, 0.1, 7.2), new THREE.Vector3(0, 0.02, 0), floorMaterial);
  floor.userData.officeId = office.id;
  floor.name = `floor-${office.id}`;

  const border = new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.BoxGeometry(9.2, 0.15, 7.3)),
    new THREE.LineBasicMaterial({ color: office.color, transparent: true, opacity: 0.82 }),
  );
  border.position.y = 0.13;
  group.add(border);

  const entranceZ = center.z < 0 ? 3.35 : -3.35;
  const backZ = center.z < 0 ? -3.35 : 3.35;
  addAsset(group, assets, "doorway", new THREE.Vector3(0, 0, entranceZ), 1.3, center.z < 0 ? 0 : Math.PI);
  // One long modular wall keeps the world roofless and readable while staying
  // inside the first-play draw-call budget; the doorway remains open to the
  // shared walkway.
  addAsset(group, assets, "wall", new THREE.Vector3(0, 0, backZ), new THREE.Vector3(8, 1, 0.62));

  const marker = new THREE.Mesh(
    new THREE.CylinderGeometry(2.25, 2.25, 0.025, 32),
    new THREE.MeshBasicMaterial({ color: office.color, transparent: true, opacity: 0.18, depthWrite: false }),
  );
  marker.position.set(0, 0.16, 0);
  marker.visible = false;
  marker.userData.officeId = office.id;
  group.add(marker);

  const label = createLabelSprite(`${office.roomNumber}  ${office.name}`, office.color);
  label.position.set(0, 3.8, center.z < 0 ? -2.65 : 2.65);
  group.add(label);

  const machinePosition = new THREE.Vector3(index % 2 === 0 ? -1.45 : 1.45, 0, center.z < 0 ? -0.5 : 0.5);
  const machineKey: AssetKey = index % 4 === 0 ? "conveyor" : index % 4 === 1 ? "screen" : index % 4 === 2 ? "scanner" : "machine";
  addAsset(group, assets, machineKey, machinePosition, machineKey === "screen" ? 1.35 : 1.15, index % 2 === 0 ? 0 : Math.PI);
  return { group, marker, floor };
}

function createWorld(assets: LoadedAssets): { world: THREE.Group; rooms: Map<OfficeId, RoomVisual> } {
  const world = new THREE.Group();
  world.name = "factory-world";
  const rooms = new Map<OfficeId, RoomVisual>();

  addBox(world, new THREE.Vector3(43, 0.08, 26), new THREE.Vector3(0, -0.05, 0), makeMaterial(0xb5c5d8, 0.95));
  addBox(world, new THREE.Vector3(40, 0.12, 3.1), new THREE.Vector3(0, 0.05, 0), makeMaterial(0x294c86, 0.7, 0.06));
  addBox(world, new THREE.Vector3(39, 0.025, 0.13), new THREE.Vector3(0, 0.13, 0), makeMaterial(0xa9cdfd, 0.72));
  addBox(world, new THREE.Vector3(0.13, 0.025, 2.7), new THREE.Vector3(-10, 0.13, 0), makeMaterial(0xa9cdfd, 0.72));
  addBox(world, new THREE.Vector3(0.13, 0.025, 2.7), new THREE.Vector3(0, 0.13, 0), makeMaterial(0xa9cdfd, 0.72));
  addBox(world, new THREE.Vector3(0.13, 0.025, 2.7), new THREE.Vector3(10, 0.13, 0), makeMaterial(0xa9cdfd, 0.72));

  OFFICES.forEach((office, index) => rooms.set(office.id, addRoomShell(world, office, assets, index)));

  // The circulation route is visibly open between all eight roofless rooms.
  const routeLights = makeMaterial(0xf2b649, 0.38, 0.15);
  [-19, -12, -5, 2, 9, 16].forEach((x) => {
    const beacon = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.08, 0.35), routeLights);
    beacon.position.set(x, 0.18, 0);
    world.add(beacon);
  });
  addBox(world, new THREE.Vector3(43, 0.55, 0.35), new THREE.Vector3(0, 0.22, -12.7), makeMaterial(NAVY, 0.87));
  addBox(world, new THREE.Vector3(43, 0.55, 0.35), new THREE.Vector3(0, 0.22, 12.7), makeMaterial(NAVY, 0.87));
  addBox(world, new THREE.Vector3(0.35, 0.55, 26), new THREE.Vector3(-21.4, 0.22, 0), makeMaterial(NAVY, 0.87));
  addBox(world, new THREE.Vector3(0.35, 0.55, 26), new THREE.Vector3(21.4, 0.22, 0), makeMaterial(NAVY, 0.87));
  return { world, rooms };
}

function createActor(gltf: GLTF, position: Point3, scale = 0.7): Actor {
  const root = SkeletonUtils.clone(gltf.scene);
  root.position.set(position.x, position.y, position.z);
  root.scale.setScalar(scale);
  const mixer = new THREE.AnimationMixer(root);
  const idleClip = gltf.animations.find((clip) => clip.name.toLowerCase() === "idle");
  const walkClip = gltf.animations.find((clip) => clip.name.toLowerCase() === "walk");
  const actor: Actor = { root, mixer, home: new THREE.Vector3(position.x, position.y, position.z) };
  if (idleClip) {
    actor.idle = mixer.clipAction(idleClip);
    actor.idle.play();
  }
  if (walkClip) actor.walk = mixer.clipAction(walkClip);
  root.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.castShadow = false;
      child.receiveShadow = false;
    }
  });
  return actor;
}

function assetProgressLabel(key: AssetKey): string {
  return key === "inspector" || key === "worker" ? "Loading workers…" : "Loading factory kit…";
}

async function loadAssets(
  onProgress: (loaded: number, total: number, key: AssetKey) => void,
): Promise<LoadedAssets> {
  const loader = new GLTFLoader();
  const entries = Object.entries(ASSET_URLS) as [AssetKey, string][];
  const loaded: LoadedAssets = {};
  let completed = 0;
  try {
    await Promise.all(
      entries.map(async ([key, url]) => {
        const gltf = await loader.loadAsync(url);
        loaded[key] = gltf;
        completed += 1;
        onProgress(completed, entries.length, key);
      }),
    );
  } catch (error) {
    disposeLoadedAssets(loaded);
    throw error;
  }
  return loaded;
}

export class FactoryApp {
  private readonly provider: FactoryDataProvider;
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(38, 1, 0.1, 120);
  private readonly raycaster = new THREE.Raycaster();
  private readonly pointer = new THREE.Vector2();
  private readonly mixers: THREE.AnimationMixer[] = [];
  private readonly roomVisuals = new Map<OfficeId, RoomVisual>();
  private readonly clock = new THREE.Clock();
  private reducedMotion = false;
  private motionQuery: MediaQueryList | null = null;
  private renderer: THREE.WebGLRenderer | null = null;
  private controls: OrbitControls | null = null;
  private resizeObserver: ResizeObserver | null = null;
  private intersectionObserver: IntersectionObserver | null = null;
  private inspector: Actor | null = null;
  private worker: Actor | null = null;
  private selectedOffice: OfficeId = "pipeline";
  private activeTab: PanelTab = "tasks";
  private activeStageIndex = 1;
  private scenarioPlaying = false;
  private scenarioElapsed = 0;
  private visitRoute: Point3[] = [];
  private visitProgress = 0;
  private visitDuration = 2.4;
  private loopHandle: number | null = null;
  private lastRenderTimestamp: number | null = null;
  private frameIntervalMs = 1000 / 60;
  private hidden = false;
  private offscreen = false;
  private overviewCamera = true;
  private suppressCameraModeChange = false;
  private inspectorAnimationState: InspectorAnimationState = "idle";
  private pointerStart: { x: number; z: number } | null = null;
  private sceneRoot: THREE.Group | null = null;
  private assets: LoadedAssets = {};
  private snapshot: FactorySnapshot = createScenarioSnapshot();
  private offices: readonly FactoryOffice[] = OFFICES;
  private telemetry: TelemetryState = {
    loadedAssets: 0,
    totalAssets: Object.keys(ASSET_URLS).length,
    renderedFrames: 0,
    sampleStartedAt: null,
    fps: null,
    frameSample: 0,
    status: "loading",
  };
  private loadGeneration = 0;
  private controlsBound = false;
  private providerError = false;
  private snapshotReady = false;
  private pointerDownHandler = (event: PointerEvent): void => {
    this.pointerStart = { x: event.clientX, z: event.clientY };
  };
  private pointerUpHandler = (event: PointerEvent): void => {
    if (this.pointerStart && isTap(this.pointerStart, { x: event.clientX, z: event.clientY })) this.pick(event.clientX, event.clientY);
    this.pointerStart = null;
  };
  private contextLostHandler = (event: Event): void => {
    event.preventDefault();
    this.stopLoop();
    this.setTelemetryStatus("context-lost");
    this.showWebGLFallback(true, "3D preview paused", "The browser is restoring the graphics context. The room list remains usable.");
  };
  private contextRestoredHandler = (): void => {
    this.setTelemetryStatus("recovering");
    try {
      this.clearScene(false);
      this.buildScene();
      this.showWebGLFallback(false);
      this.setTelemetryStatus("ready");
      this.startLoop();
    } catch (error) {
      console.error("Factory WebGL context recovery failed", error);
      this.setTelemetryStatus("error");
      this.showWebGLFallback(true, "3D preview unavailable", "The graphics context could not be restored. Retry loading to rebuild the scene.");
    }
  };
  private resizeHandler = (): void => this.resize();
  private controlsChangeHandler = (): void => {
    if (!this.suppressCameraModeChange) this.overviewCamera = false;
  };
  private motionChangeHandler = (event: MediaQueryListEvent): void => {
    this.reducedMotion = event.matches;
    if (this.controls) this.controls.enableDamping = !this.reducedMotion;
  };

  constructor(provider: FactoryDataProvider = scenarioProvider) {
    this.provider = provider;
  }

  async start(): Promise<void> {
    this.bindStaticControls();
    this.renderRoomList();
    this.renderScenarioControls();
    this.renderPanel();
    this.updateStageCopy();
    await this.load();
  }

  private async load(): Promise<void> {
    const generation = ++this.loadGeneration;
    const overlay = byId<HTMLDivElement>("loading-overlay");
    const loadingLabel = byId<HTMLElement>("loading-label");
    const loadingDetail = byId<HTMLElement>("loading-detail");
    const progress = byId<HTMLElement>("loading-progress");
    const retry = byId<HTMLButtonElement>("retry-loading");
    this.stopLoop();
    this.clearScene(true);
    this.disposeRenderer();
    this.overviewCamera = true;
    this.offscreen = false;
    this.lastRenderTimestamp = null;
    this.assets = {};
    this.providerError = false;
    this.snapshotReady = false;
    this.renderRoomList();
    this.renderPanel();
    this.telemetry = {
      loadedAssets: 0,
      totalAssets: Object.keys(ASSET_URLS).length,
      renderedFrames: 0,
      sampleStartedAt: null,
      fps: null,
      frameSample: 0,
      status: "loading",
    };
    this.updateTelemetryDom();
    retry.hidden = true;
    overlay.hidden = false;
    this.showWebGLFallback(false);
    loadingLabel.textContent = "Preparing the factory";
    loadingDetail.textContent = "Reading the selected factory data and bundled scene assets.";
    progress.style.width = "0%";
    let nextSnapshot: FactorySnapshot;
    try {
      nextSnapshot = await this.provider.getSnapshot();
    } catch (error) {
      if (generation !== this.loadGeneration) return;
      console.error("Factory data provider failed", error);
      this.providerError = true;
      this.setTelemetryStatus("error");
      this.applySnapshotMode();
      this.renderRoomList();
      this.renderPanel();
      loadingLabel.textContent = "Current snapshot unavailable";
      loadingDetail.textContent = "The office snapshot could not be read. Retry when it is available again.";
      retry.hidden = false;
      retry.onclick = () => void this.load();
      return;
    }
    if (generation !== this.loadGeneration) return;
    this.snapshot = nextSnapshot;
    this.snapshotReady = true;
    this.offices = this.snapshot.offices;
      if (!this.offices.some((office) => office.id === this.selectedOffice)) this.selectedOffice = this.offices[0]?.id ?? "pipeline";
      const loadedSnapshot = this.snapshot;
      const providerStageIndex = loadedSnapshot.mode === "scenario"
        ? SCENARIO_STAGES.findIndex((stage) => stage.id === loadedSnapshot.stageId)
        : -1;
      if (providerStageIndex >= 0) this.activeStageIndex = providerStageIndex;
      this.applySnapshotMode();
      this.renderRoomList();
      this.renderPanel();
      try {
      this.assets = await loadAssets((loaded, total, key) => {
        if (generation !== this.loadGeneration) return;
        this.telemetry.loadedAssets = loaded;
        this.telemetry.totalAssets = total;
        this.updateTelemetryDom();
        progress.style.width = String(Math.round((loaded / total) * 100)) + "%";
        loadingLabel.textContent = assetProgressLabel(key);
        loadingDetail.textContent = String(loaded) + " of " + String(total) + " bundled modules ready";
      });
      } catch (error) {
        if (generation !== this.loadGeneration) return;
        console.error("Factory asset load failed", error);
        this.setTelemetryStatus("error");
        loadingLabel.textContent = "The factory needs another try";
        loadingDetail.textContent = "Bundled scene assets could not be loaded. The room data remains available below.";
        progress.style.width = "0%";
        retry.hidden = false;
        retry.onclick = () => void this.load();
        return;
      }
      if (generation !== this.loadGeneration) return;
      this.setupRenderer();
      if (!this.renderer) {
        this.setTelemetryStatus("unavailable");
        this.showWebGLFallback(false);
        loadingLabel.textContent = "3D preview unavailable";
        loadingDetail.textContent = "The room data remains available. Retry loading after enabling WebGL.";
        retry.hidden = false;
        retry.onclick = () => void this.load();
        return;
      }
      try {
      this.buildScene();
      overlay.hidden = true;
      this.showWebGLFallback(false);
      this.setTelemetryStatus("ready");
      this.startLoop();
      } catch (error) {
        console.error("Factory scene build failed", error);
        this.setTelemetryStatus("error");
        loadingLabel.textContent = "The factory needs another try";
        loadingDetail.textContent = "The room data remains available while the 3D scene is rebuilt.";
        retry.hidden = false;
        retry.onclick = () => void this.load();
      }
  }

  private disposeRenderer(): void {
    this.resizeObserver?.disconnect();
    this.resizeObserver = null;
    this.intersectionObserver?.disconnect();
    this.intersectionObserver = null;
    window.removeEventListener("resize", this.resizeHandler);
    if (!this.renderer) {
      this.controls?.removeEventListener("change", this.controlsChangeHandler);
      this.controls?.dispose();
      this.controls = null;
      return;
    }
    this.renderer.domElement.removeEventListener("webglcontextlost", this.contextLostHandler);
    this.renderer.domElement.removeEventListener("webglcontextrestored", this.contextRestoredHandler);
    this.renderer.domElement.removeEventListener("pointerdown", this.pointerDownHandler);
    this.renderer.domElement.removeEventListener("pointerup", this.pointerUpHandler);
    this.controls?.removeEventListener("change", this.controlsChangeHandler);
    this.controls?.dispose();
    this.controls = null;
    this.renderer.dispose();
    this.renderer.domElement.remove();
    this.renderer = null;
  }

  private clearScene(disposeResources: boolean): void {
    this.stopLoop();
    this.mixers.forEach((mixer) => mixer.stopAllAction());
    this.mixers.length = 0;
    while (this.scene.children.length > 0) {
      const child = this.scene.children[this.scene.children.length - 1];
      this.scene.remove(child);
      if (disposeResources) disposeObjectResources(child);
    }
    this.scene.background = null;
    this.scene.fog = null;
    this.roomVisuals.clear();
    this.sceneRoot = null;
    this.inspector = null;
    this.worker = null;
    this.visitRoute = [];
    this.visitProgress = 1;
    this.inspectorAnimationState = "idle";
  }

  private setTelemetryStatus(status: RendererStatus): void {
    this.telemetry.status = status;
    this.updateTelemetryDom();
  }

  private updateTelemetryDom(): void {
    const telemetry = document.getElementById("qa-telemetry");
    if (!telemetry) return;
    const qaEnabled = new URLSearchParams(window.location.search).get("qa") === "1";
    telemetry.hidden = !qaEnabled;
    telemetry.dataset.triangles = this.renderer ? String(this.renderer.info.render.triangles) : "0";
    telemetry.dataset.drawcalls = this.renderer ? String(this.renderer.info.render.calls) : "0";
    telemetry.dataset.assetprogress = String(this.telemetry.loadedAssets) + "/" + String(this.telemetry.totalAssets);
    telemetry.dataset.fps = this.telemetry.fps === null ? "0" : this.telemetry.fps.toFixed(1);
    telemetry.dataset.framesample = String(this.telemetry.frameSample);
    telemetry.dataset.rendererstatus = this.telemetry.status;
    telemetry.textContent = [
      "QA telemetry",
      "Triangles " + telemetry.dataset.triangles,
      "Draw calls " + telemetry.dataset.drawcalls,
      "Assets " + telemetry.dataset.assetprogress,
      "FPS " + telemetry.dataset.fps,
      "Frame sample " + telemetry.dataset.framesample,
      "Renderer " + this.telemetry.status,
    ].join(" · ");
  }

  private recordFrame(timestamp: number): void {
    this.telemetry.renderedFrames += 1;
    if (this.telemetry.sampleStartedAt === null) this.telemetry.sampleStartedAt = timestamp;
    const elapsed = timestamp - this.telemetry.sampleStartedAt;
    if (elapsed >= 500) {
      this.telemetry.fps = this.telemetry.renderedFrames * 1000 / elapsed;
      this.telemetry.frameSample = this.telemetry.renderedFrames;
      this.telemetry.renderedFrames = 0;
      this.telemetry.sampleStartedAt = timestamp;
    }
    this.updateTelemetryDom();
  }

  private setupRenderer(): void {
    const canvasRoot = byId<HTMLDivElement>("canvas-root");
    this.disposeRenderer();
    try {
      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
      this.renderer.outputColorSpace = THREE.SRGBColorSpace;
      this.renderer.setClearColor(0xc9d8e8, 1);
      this.renderer.domElement.setAttribute("aria-label", "Playable Base2026 Factory 3D scene");
      canvasRoot.replaceChildren(this.renderer.domElement);
      this.renderer.domElement.addEventListener("webglcontextlost", this.contextLostHandler);
      this.renderer.domElement.addEventListener("webglcontextrestored", this.contextRestoredHandler);
      this.controls = new OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enablePan = false;
      this.controls.enableDamping = !this.reducedMotion;
      this.controls.minDistance = 14;
      this.controls.maxDistance = 96;
      this.controls.minPolarAngle = 0.65;
      this.controls.maxPolarAngle = 1.32;
      this.controls.target.set(0, 0, 0);
      this.camera.position.set(26, 23, 28);
      this.camera.lookAt(this.controls.target);
      this.controls.addEventListener("change", this.controlsChangeHandler);
      this.renderer.domElement.addEventListener("pointerdown", this.pointerDownHandler);
      this.renderer.domElement.addEventListener("pointerup", this.pointerUpHandler);
      window.addEventListener("resize", this.resizeHandler);
      if (typeof ResizeObserver !== "undefined") {
        this.resizeObserver = new ResizeObserver(this.resizeHandler);
        this.resizeObserver.observe(canvasRoot);
      }
      if (typeof IntersectionObserver !== "undefined") {
        this.intersectionObserver = new IntersectionObserver((entries) => {
          const visible = entries.some((entry) => entry.isIntersecting && entry.intersectionRatio > 0);
          if (visible) {
            if (this.offscreen) {
              this.offscreen = false;
              this.startLoop();
            }
          } else {
            this.offscreen = true;
            this.stopLoop();
          }
        });
        this.intersectionObserver.observe(canvasRoot);
      }
      this.resize();
    } catch (error) {
      console.error("WebGL unavailable", error);
      this.disposeRenderer();
      this.setTelemetryStatus("unavailable");
      this.showWebGLFallback(true, "3D preview unavailable", "This browser could not start WebGL. The room data remains usable below.");
    }
  }

  private buildScene(): void {
    this.scene.background = new THREE.Color(0xc9d8e8);
    this.scene.fog = new THREE.Fog(0xc9d8e8, 72, 180);
    this.scene.add(new THREE.HemisphereLight(0xeaf3ff, 0x4b6284, 2.25));
    const sun = new THREE.DirectionalLight(0xffffff, 2.4);
    sun.position.set(-10, 26, 16);
    this.scene.add(sun);
    this.scene.add(new THREE.AmbientLight(0xaac3e8, 0.55));

    const { world, rooms } = createWorld(this.assets);
    this.sceneRoot = world;
    rooms.forEach((visual, id) => this.roomVisuals.set(id, visual));
    this.scene.add(world);
    const grid = new THREE.GridHelper(43, 43, 0x8aa2c2, 0xb2c5df);
    grid.position.y = 0.01;
    grid.material.transparent = true;
    grid.material.opacity = 0.12;
    this.scene.add(grid);

    const inspectorGltf = this.assets.inspector;
    const workerGltf = this.assets.worker;
    if (inspectorGltf) {
      this.inspector = createActor(inspectorGltf, START_POINT, 0.72);
      this.scene.add(this.inspector.root);
      this.mixers.push(this.inspector.mixer);
    }
    if (workerGltf) {
      const workerHome = OFFICE_POSITIONS.engineering;
      this.worker = createActor(workerGltf, { x: workerHome.x + 2, y: 0, z: workerHome.z - 1 }, 0.66);
      this.scene.add(this.worker.root);
      this.mixers.push(this.worker.mixer);
    }
    if (this.overviewCamera) this.fitOverviewCamera();
    this.selectOffice(this.selectedOffice);
    this.renderPanel();
  }

  private resize(): void {
    if (!this.renderer) return;
    const root = byId<HTMLDivElement>("canvas-root");
    const width = Math.max(1, root.clientWidth);
    const height = Math.max(1, root.clientHeight);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height, false);
    this.frameIntervalMs = width <= 720 || this.camera.aspect < 1 ? 1000 / 30 : 1000 / 60;
    if (this.overviewCamera) this.fitOverviewCamera();
  }

  private fitOverviewCamera(): void {
    if (!this.controls || !this.overviewCamera) return;
    const root = byId<HTMLDivElement>("canvas-root");
    const aspect = this.camera.aspect || Math.max(0.2, root.clientWidth / Math.max(1, root.clientHeight));
    const distance = overviewCameraDistance(aspect, this.camera.fov);
    this.controls.target.set(0, 0, 0);
    const offset = this.camera.position.clone().sub(this.controls.target);
    if (offset.lengthSq() < 0.001) offset.set(26, 23, 28);
    offset.setLength(distance);
    this.camera.position.copy(this.controls.target).add(offset);
    this.controls.minDistance = 14;
    this.controls.maxDistance = Math.max(distance * 1.45, distance + 12);
    this.camera.far = Math.max(240, distance * 2.8);
    this.camera.updateProjectionMatrix();
    this.suppressCameraModeChange = true;
    this.controls.update();
    this.suppressCameraModeChange = false;
    if (this.scene.fog instanceof THREE.Fog) {
      this.scene.fog.near = Math.max(48, distance * 0.78);
      this.scene.fog.far = Math.max(this.scene.fog.near + 40, distance * 2.2);
    }
  }

  private startLoop(): void {
    if (this.loopHandle !== null || this.hidden || this.offscreen || !this.renderer) return;
    this.clock.start();
    this.lastRenderTimestamp = null;
    const tick = (timestamp: number) => {
      if (!this.renderer || this.hidden || this.offscreen) {
        this.loopHandle = null;
        return;
      }
      this.loopHandle = window.requestAnimationFrame(tick);
      if (this.lastRenderTimestamp !== null && timestamp - this.lastRenderTimestamp < this.frameIntervalMs) return;
      this.lastRenderTimestamp = this.lastRenderTimestamp === null
        ? timestamp
        : timestamp - ((timestamp - this.lastRenderTimestamp) % this.frameIntervalMs);
      const delta = Math.min(0.05, this.clock.getDelta());
      this.update(delta);
      this.renderer.render(this.scene, this.camera);
      this.recordFrame(timestamp);
    };
    this.loopHandle = window.requestAnimationFrame(tick);
  }

  private stopLoop(): void {
    if (this.loopHandle !== null) window.cancelAnimationFrame(this.loopHandle);
    this.loopHandle = null;
    this.lastRenderTimestamp = null;
  }

  private update(delta: number): void {
    const visualDelta = this.reducedMotion ? 0 : delta;
    this.mixers.forEach((mixer) => mixer.update(visualDelta));
    this.updateVisit(delta);
    this.updateScenario(delta);
    if (this.controls && !this.reducedMotion) this.controls.update();
  }

  private updateVisit(delta: number): void {
    if (!this.inspector || this.visitRoute.length === 0) return;
    if (this.reducedMotion) this.visitProgress = 1;
    else if (this.visitProgress < 1) this.visitProgress = Math.min(1, this.visitProgress + delta / this.visitDuration);
    const current = sampleRoute(this.visitRoute, this.visitProgress);
    const previous = this.inspector.root.position.clone();
    this.inspector.root.position.set(current.x, current.y, current.z);
    const dx = current.x - previous.x;
    const dz = current.z - previous.z;
    if (Math.hypot(dx, dz) > 0.0001) this.inspector.root.rotation.y = Math.atan2(dx, dz);
    if (this.visitProgress > 0 && this.visitProgress < 1) {
      this.setInspectorWalking(true);
      byId<HTMLElement>("visit-status").textContent = `Visiting ${this.selectedOfficeDefinition().name}`;
      byId<HTMLButtonElement>("cancel-visit").hidden = false;
      if (this.controls && !this.reducedMotion) {
        this.controls.target.lerp(new THREE.Vector3(current.x, 0, current.z), 1 - Math.exp(-delta * 4));
      }
    } else {
      if (this.visitRoute.length > 0 && this.visitProgress >= 1) {
        this.setInspectorWalking(false);
        byId<HTMLElement>("visit-status").textContent = `Arrived at ${this.selectedOfficeDefinition().name}`;
        byId<HTMLButtonElement>("cancel-visit").hidden = true;
        this.visitRoute = [];
      }
    }
  }

  private setInspectorWalking(walking: boolean): void {
    if (!this.inspector) return;
    const transition = inspectorAnimationTransition(this.inspectorAnimationState, walking);
    if (!transition.changed) return;
    if (transition.state === "walk") {
      this.inspector.idle?.stop();
      this.inspector.walk?.reset().play();
    } else {
      this.inspector.walk?.stop();
      this.inspector.idle?.reset().play();
    }
    this.inspectorAnimationState = transition.state;
  }

  private updateScenario(delta: number): void {
    if (!this.scenarioPlaying || this.reducedMotion) return;
    const stage = SCENARIO_STAGES[this.activeStageIndex];
    this.scenarioElapsed += delta;
    if (stage.hold || this.scenarioElapsed >= 2.8) {
      this.scenarioPlaying = false;
      this.scenarioElapsed = 0;
      if (!stage.hold && this.activeStageIndex < SCENARIO_STAGES.length - 1) this.activeStageIndex += 1;
      this.updateStageCopy();
      this.renderScenarioControls();
    }
  }

  private selectedOfficeDefinition(): FactoryOffice {
    return this.offices.find((office) => office.id === this.selectedOffice)
      ?? OFFICES.find((office) => office.id === this.selectedOffice)
      ?? OFFICES[0];
  }

  private applySnapshotMode(): void {
    const badge = document.querySelector<HTMLElement>(".mode-badge");
    const unavailable = this.providerError;
    byId<HTMLElement>("app").dataset.mode = unavailable ? "unavailable" : this.snapshot.mode;
    let snapshotTime = document.getElementById("snapshot-read-time");
    if (!snapshotTime) {
      snapshotTime = document.createElement("p");
      snapshotTime.id = "snapshot-read-time";
      snapshotTime.className = "snapshot-read-time";
      document.querySelector(".brand-lockup > div")?.append(snapshotTime);
    }
    snapshotTime.hidden = unavailable || this.snapshot.mode !== "current";
    if (this.snapshot.mode === "current") snapshotTime.textContent = "Snapshot read " + displayTime(this.snapshot.fetchedAt);
    if (badge) {
      const label = unavailable ? "Current snapshot unavailable" : this.snapshot.label;
      badge.textContent = label;
      badge.setAttribute("aria-label", "Mode: " + label);
    }
    const scenarioCard = document.querySelector<HTMLElement>(".scenario-card");
    const scenarioControls = document.querySelector<HTMLElement>(".scenario-controls");
    const visitButton = byId<HTMLButtonElement>("visit-office");
    const scenarioMode = !unavailable && this.snapshot.mode === "scenario";
    if (scenarioCard) scenarioCard.hidden = !scenarioMode;
    if (scenarioControls) scenarioControls.hidden = !scenarioMode;
    visitButton.hidden = unavailable;
  }

  private selectOffice(id: OfficeId): void {
    this.selectedOffice = id;
    this.roomVisuals.forEach((visual, officeId) => {
      const active = officeId === id;
      visual.marker.visible = active;
      const material = visual.floor.material;
      if (material instanceof THREE.MeshStandardMaterial) {
        material.emissive.set(active ? 0x173e9f : 0x000000);
        material.emissiveIntensity = active ? 0.28 : 0;
      }
    });
    this.renderRoomList();
    this.renderPanel();
    byId<HTMLElement>("visit-status").textContent = `Selected ${this.selectedOfficeDefinition().name}`;
  }

  private pick(clientX: number, clientY: number): void {
    if (!this.renderer || !this.sceneRoot) return;
    const rect = this.renderer.domElement.getBoundingClientRect();
    this.pointer.x = ((clientX - rect.left) / rect.width) * 2 - 1;
    this.pointer.y = -((clientY - rect.top) / rect.height) * 2 + 1;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const intersections = this.raycaster.intersectObjects(this.sceneRoot.children, true);
    const hit = intersections.find((entry) => {
      let current: THREE.Object3D | null = entry.object;
      while (current) {
        if (typeof current.userData.officeId === "string") return true;
        current = current.parent;
      }
      return false;
    });
    if (!hit) return;
    let current: THREE.Object3D | null = hit.object;
    while (current && typeof current.userData.officeId !== "string") current = current.parent;
    if (current && OFFICE_IDS.includes(current.userData.officeId as OfficeId)) this.selectOffice(current.userData.officeId as OfficeId);
  }

  private visitSelectedOffice(): void {
    if (!this.inspector) return;
    byId<HTMLDivElement>("scene-shell").scrollIntoView({ block: "start", behavior: this.reducedMotion ? "auto" : "smooth" });
    this.overviewCamera = false;
    const current = this.inspector.root.position;
    const from: Point3 = { x: current.x, y: current.y, z: current.z };
    this.visitRoute = routeBetween(from, this.selectedOffice);
    this.visitProgress = this.reducedMotion ? 1 : 0;
    this.visitDuration = Math.max(1.7, Math.min(4.3, 1.45 + routeLengthSafe(this.visitRoute) / 8));
    if (this.reducedMotion) {
      const target = sampleRoute(this.visitRoute, 1);
      this.inspector.root.position.set(target.x, target.y, target.z);
      this.setInspectorWalking(false);
      this.visitRoute = [];
      byId<HTMLElement>("visit-status").textContent = `Arrived at ${this.selectedOfficeDefinition().name}`;
      byId<HTMLButtonElement>("cancel-visit").hidden = true;
    }
  }

  private cancelVisit(): void {
    this.visitRoute = [];
    this.visitProgress = 1;
    this.setInspectorWalking(false);
    byId<HTMLButtonElement>("cancel-visit").hidden = true;
    byId<HTMLElement>("visit-status").textContent = `Visit canceled — ${this.selectedOfficeDefinition().name} remains selected`;
  }

  private resetCamera(): void {
    if (!this.controls) return;
    this.overviewCamera = true;
    this.camera.position.set(26, 23, 28);
    this.controls.target.set(0, 0, 0);
    this.fitOverviewCamera();
  }

  private zoomCamera(delta: number): void {
    if (!this.controls) return;
    this.overviewCamera = false;
    const offset = this.camera.position.clone().sub(this.controls.target);
    const next = clampZoom(offset.length() + delta, this.controls.minDistance, this.controls.maxDistance);
    offset.setLength(next);
    this.camera.position.copy(this.controls.target).add(offset);
    this.controls.update();
  }

  private rotateCamera(delta: number): void {
    if (!this.controls) return;
    this.overviewCamera = false;
    const offset = this.camera.position.clone().sub(this.controls.target);
    const spherical = new THREE.Spherical().setFromVector3(offset);
    spherical.theta += delta;
    this.camera.position.setFromSpherical(spherical).add(this.controls.target);
    this.controls.update();
  }

  private setStage(index: number): void {
    this.activeStageIndex = Math.min(SCENARIO_STAGES.length - 1, Math.max(0, index));
    this.scenarioElapsed = 0;
    this.scenarioPlaying = false;
    this.updateStageCopy();
    this.renderScenarioControls();
  }

  private updateStageCopy(): void {
    const stage = SCENARIO_STAGES[this.activeStageIndex];
    byId<HTMLElement>("stage-state").textContent = stage.hold ? "Held at review" : stage.status === "complete" ? "Complete in scenario" : "Next in scenario";
    byId<HTMLElement>("stage-description").textContent = stage.description;
    this.renderScenarioControls();
  }

  private renderScenarioControls(): void {
    const stageContainer = byId<HTMLDivElement>("stage-list");
    stageContainer.replaceChildren();
    SCENARIO_STAGES.forEach((stage, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `stage-button${index === this.activeStageIndex ? " is-active" : ""}${stage.status === "complete" ? " is-complete" : ""}`;
      button.setAttribute("aria-pressed", String(index === this.activeStageIndex));
      const label = document.createElement("span");
      label.className = "stage-label";
      label.textContent = stage.label;
      const subtitle = document.createElement("span");
      subtitle.className = "stage-subtitle";
      subtitle.textContent = stage.subtitle;
      button.append(label, subtitle);
      if (stage.role) {
        const role = document.createElement("span");
        role.className = "stage-role";
        role.textContent = stage.role;
        button.append(role);
      }
      button.addEventListener("click", () => this.setStage(index));
      stageContainer.append(button);
    });
    const play = byId<HTMLButtonElement>("scenario-play");
    play.textContent = this.scenarioPlaying ? "Pause" : "Play";
    play.setAttribute("aria-label", this.scenarioPlaying ? "Pause scenario trace" : "Play scenario trace");
  }

  private renderRoomList(): void {
    const list = byId<HTMLDivElement>("room-list");
    list.replaceChildren();
    if (!this.snapshotReady) return;
    byId<HTMLElement>("room-count").textContent = String(this.offices.length);
    this.offices.forEach((office) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `room-button${office.id === this.selectedOffice ? " is-selected" : ""}`;
      button.setAttribute("aria-pressed", String(office.id === this.selectedOffice));
      const number = document.createElement("span");
      number.className = "room-number";
      number.textContent = office.roomNumber;
      const name = document.createElement("span");
      name.className = "room-name";
      name.textContent = office.name;
      const tag = document.createElement("span");
      tag.className = "room-tag";
      tag.textContent = this.snapshot.mode === "current"
        ? ({ "In progress": "Working", "Recorded completed": "Complete", "Awaiting review": "Review", "Access blocked": "Blocked", "Awaiting acceptance": "Queued", "No fresh data": "No update" } as Record<string, string>)[(office as CurrentOffice).status] ?? "Unknown"
        : "inspect";
      if (this.snapshot.mode === "current") button.title = (office as CurrentOffice).status + " · " + (office as CurrentOffice).freshness;
      button.append(number, name, tag);
      button.addEventListener("click", () => this.selectOffice(office.id));
      list.append(button);
    });
  }

  private renderPanel(): void {
    if (this.providerError) {
      byId<HTMLElement>("selected-room-title").textContent = "Current snapshot unavailable";
      byId<HTMLElement>("selected-room-time").textContent = "Read-only provider error";
      const unavailable = byId<HTMLDivElement>("panel-content");
      unavailable.replaceChildren();
      const message = document.createElement("p");
      message.className = "scenario-description";
      message.textContent = "No current-state data was returned. Retry when the private provider is available.";
      unavailable.append(message);
      return;
    }
    if (!this.snapshotReady) {
      byId<HTMLElement>("selected-room-title").textContent = "Reading the factory";
      byId<HTMLElement>("selected-room-time").textContent = "Waiting for the snapshot";
      byId<HTMLDivElement>("panel-content").replaceChildren();
      return;
    }
    const office = this.selectedOfficeDefinition();
    byId<HTMLElement>("selected-room-title").textContent = office.name;
    const currentOffice = this.snapshot.mode === "current"
      ? this.offices.find((candidate) => candidate.id === this.selectedOffice) as CurrentOffice | undefined
      : undefined;
    byId<HTMLElement>("selected-room-time").textContent = this.providerError
      ? "Current snapshot unavailable"
      : this.snapshot.mode === "scenario"
        ? "Authored scenario / fixed trace"
        : "Recorded " + displayTime(currentOffice?.recordedUpdate) + " · " + currentOffice?.freshness;
    const content = byId<HTMLDivElement>("panel-content");
    content.replaceChildren();
    if (this.activeTab === "receipts") {
      const grid = document.createElement("div");
      grid.className = "receipt-grid";
      if (currentOffice) {
        const currentRows: Array<[string, string]> = [
          ["Status", currentOffice.status],
          ["Role", currentOffice.role],
          ["Next", currentOffice.next],
          ["Freshness", currentOffice.freshness],
        ];
        currentRows.forEach(([labelText, valueText]) => {
          const row = document.createElement("div");
          row.className = "receipt-item";
          const label = document.createElement("span");
          label.className = "receipt-label";
          label.textContent = labelText;
          const value = document.createElement("span");
          value.className = "receipt-value";
          value.textContent = valueText;
          row.append(label, value);
          grid.append(row);
        });
      }
      office.receipts.forEach((receipt) => {
        const row = document.createElement("div");
        row.className = "receipt-item";
        const label = document.createElement("span");
        label.className = "receipt-label";
        label.textContent = receipt.label;
        const value = document.createElement("span");
        value.className = "receipt-value";
        value.textContent = receipt.value;
        row.append(label, value);
        grid.append(row);
      });
      content.append(grid);
    } else {
      const list = document.createElement("ul");
      list.className = "panel-list";
      if (this.activeTab === "tasks" && currentOffice) {
        currentOffice.taskStatuses.forEach((taskStatus) => {
          const item = document.createElement("li");
          item.className = "current-task";
          const title = document.createElement("h3");
          title.textContent = taskStatus.task;
          const status = document.createElement("p");
          status.className = "current-task-status";
          status.textContent = taskStatus.status + " · " + taskStatus.freshness;
          const role = document.createElement("p");
          role.className = "current-task-meta";
          role.textContent = taskStatus.role;
          item.append(title, status, role);
          if (taskStatus.recordedAt) {
            const time = document.createElement("p");
            time.className = "current-task-meta";
            time.textContent = "Recorded " + displayTime(taskStatus.recordedAt);
            item.append(time);
          }
          if (taskStatus.next) {
            const next = document.createElement("p");
            next.textContent = "Next: " + taskStatus.next;
            item.append(next);
          }
          if (taskStatus.originalNote) {
            const details = document.createElement("details");
            const summary = document.createElement("summary");
            summary.textContent = "Recorded note · original language";
            const note = document.createElement("p");
            note.textContent = taskStatus.originalNote;
            details.append(summary, note);
            item.append(details);
          }
          if (taskStatus.urlReceipt?.url) {
            const link = document.createElement("a");
            link.href = taskStatus.urlReceipt.url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = taskStatus.urlReceipt.label ?? "Open receipt";
            item.append(" ", link);
          }
          list.append(item);
        });
      } else {
        const values = this.activeTab === "tasks" ? office.tasks : office.process;
        values.forEach((value) => {
          const item = document.createElement("li");
          item.textContent = value;
          list.append(item);
        });
      }
      content.append(list);
    }
    document.querySelectorAll<HTMLButtonElement>(".tab-button").forEach((button) => {
      const active = button.dataset.tab === this.activeTab;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-selected", String(active));
      button.id = "room-tab-" + button.dataset.tab;
      button.setAttribute("aria-controls", "panel-content");
      button.tabIndex = active ? 0 : -1;
      if (active) content.setAttribute("aria-labelledby", button.id);
    });
  }

  private bindStaticControls(): void {
    if (this.controlsBound) return;
    this.controlsBound = true;
    this.motionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    this.reducedMotion = this.motionQuery.matches;
    if (typeof this.motionQuery.addEventListener === "function") this.motionQuery.addEventListener("change", this.motionChangeHandler);
    else this.motionQuery.addListener(this.motionChangeHandler);
    byId<HTMLButtonElement>("visit-office").addEventListener("click", () => this.visitSelectedOffice());
    byId<HTMLButtonElement>("cancel-visit").addEventListener("click", () => this.cancelVisit());
    byId<HTMLButtonElement>("reset-camera").addEventListener("click", () => this.resetCamera());
    byId<HTMLButtonElement>("zoom-out").addEventListener("click", () => this.zoomCamera(3));
    byId<HTMLButtonElement>("zoom-in").addEventListener("click", () => this.zoomCamera(-3));
    byId<HTMLButtonElement>("rotate-left").addEventListener("click", () => this.rotateCamera(-0.24));
    byId<HTMLButtonElement>("rotate-right").addEventListener("click", () => this.rotateCamera(0.24));
    byId<HTMLButtonElement>("scenario-play").addEventListener("click", () => {
      this.scenarioPlaying = !this.scenarioPlaying;
      this.scenarioElapsed = 0;
      this.renderScenarioControls();
    });
    byId<HTMLButtonElement>("scenario-step").addEventListener("click", () => this.setStage(this.activeStageIndex + 1));
    byId<HTMLButtonElement>("scenario-reset").addEventListener("click", () => this.setStage(0));
    document.querySelectorAll<HTMLButtonElement>(".tab-button").forEach((button) => {
      button.addEventListener("keydown", (event) => {
        const tabs = ["tasks", "process", "receipts"] as const;
        const index = tabs.indexOf(this.activeTab);
        let next = index;
        if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
        else if (event.key === "ArrowLeft") next = (index + tabs.length - 1) % tabs.length;
        else if (event.key === "Home") next = 0;
        else if (event.key === "End") next = tabs.length - 1;
        else return;
        event.preventDefault();
        this.activeTab = tabs[next];
        this.renderPanel();
        document.getElementById("room-tab-" + this.activeTab)?.focus();
      });
      button.addEventListener("click", () => {
        const tab = button.dataset.tab;
        if (tab === "tasks" || tab === "process" || tab === "receipts") {
          this.activeTab = tab;
          this.renderPanel();
        }
      });
    });
    document.addEventListener("keydown", (event) => {
      if (isInteractiveTarget(event.target) || !isFactoryKeyboardScope(event.target)) return;
      const officeNavigationKey = event.key === "ArrowRight"
        || event.key === "ArrowDown"
        || event.key === "ArrowLeft"
        || event.key === "ArrowUp";
      const keyboardScope = event.target instanceof Element
        ? event.target.closest("#canvas-root, #room-list")
        : event.target === document.body;
      if (officeNavigationKey && !keyboardScope) return;
      if (event.key === "ArrowRight" || event.key === "ArrowDown") {
        event.preventDefault();
        this.selectOffice(cycleOffice(this.selectedOffice, 1));
      } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
        event.preventDefault();
        this.selectOffice(cycleOffice(this.selectedOffice, -1));
      } else if (event.key.toLowerCase() === "v") {
        this.visitSelectedOffice();
      } else if (event.key.toLowerCase() === "r") {
        this.resetCamera();
      } else if (event.key === "+" || event.key === "=") {
        this.zoomCamera(-3);
      } else if (event.key === "-" || event.key === "_") {
        this.zoomCamera(3);
      } else if (event.key === "[") {
        this.rotateCamera(-0.24);
      } else if (event.key === "]") {
        this.rotateCamera(0.24);
      } else if (event.key === " " && !this.providerError && this.snapshot.mode === "scenario") {
        event.preventDefault();
        this.scenarioPlaying = !this.scenarioPlaying;
        this.renderScenarioControls();
      }
    });
    document.addEventListener("visibilitychange", () => {
      this.hidden = document.hidden;
      if (this.hidden) this.stopLoop();
      else this.startLoop();
    });
  }

  private showWebGLFallback(show: boolean, title?: string, detail?: string): void {
    const fallback = byId<HTMLDivElement>("webgl-fallback");
    fallback.hidden = !show;
    if (title) byId<HTMLElement>("fallback-title").textContent = title;
    if (detail) byId<HTMLElement>("fallback-detail").textContent = detail;
    byId<HTMLDivElement>("canvas-root").setAttribute("aria-hidden", String(show));
  }
}

function routeLengthSafe(route: readonly Point3[]): number {
  let total = 0;
  for (let index = 1; index < route.length; index += 1) {
    const previous = route[index - 1];
    const current = route[index];
    total += Math.hypot(current.x - previous.x, current.y - previous.y, current.z - previous.z);
  }
  return total;
}

export async function createFactoryApp(provider: FactoryDataProvider = scenarioProvider): Promise<FactoryApp> {
  const app = new FactoryApp(provider);
  await app.start();
  return app;
}
