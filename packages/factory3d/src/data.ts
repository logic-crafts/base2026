export type OfficeId =
  | "growth"
  | "directories"
  | "product"
  | "design"
  | "media"
  | "engineering"
  | "pipeline"
  | "creator";

export type ScenarioStageId = "discover" | "rights-review" | "curate" | "release";

export interface FactoryReceipt {
  label: string;
  value: string;
  kind: "source" | "decision" | "output" | "hold";
}

export interface FactoryOffice {
  id: OfficeId;
  name: string;
  shortName: string;
  descriptor: string;
  roomNumber: string;
  color: number;
  process: string[];
  tasks: string[];
  receipts: FactoryReceipt[];
}

export interface ScenarioStage {
  id: ScenarioStageId;
  label: string;
  subtitle: string;
  description: string;
  officeIds: OfficeId[];
  status: "complete" | "active" | "held" | "next";
  hold: boolean;
  /** A named assistant role is part of the authored scenario only. */
  role?: "ChatGPT Scout" | "ChatGPT Curator";
}

export interface ScenarioSnapshot {
  mode: "scenario";
  label: "Scenario — not live operations";
  capturedAt: string;
  stageId: ScenarioStageId;
  offices: FactoryOffice[];
}

export type FactoryFreshness = "fresh" | "stale" | "unknown";

export interface FactoryUrlReceipt {
  url: string;
  label?: string;
}

export interface FactoryTaskStatus {
  task: string;
  status: string;
  freshness: FactoryFreshness;
  role: string;
  next: string;
  recordedAt?: string;
  originalNote?: string;
  urlReceipt?: FactoryUrlReceipt;
}

/** Read-only current-state shape reserved for a private adapter. */
export interface CurrentOffice extends FactoryOffice {
  freshness: FactoryFreshness;
  recordedUpdate?: string;
  status: string;
  role: string;
  next: string;
  originalNote?: string;
  taskStatuses: FactoryTaskStatus[];
}

export interface CurrentSnapshot {
  mode: "current";
  label: "Current-state snapshot";
  fetchedAt: string;
  capturedAt: string;
  recordedUpdate: string;
  freshness: FactoryFreshness;
  offices: CurrentOffice[];
}

export type FactorySnapshot = ScenarioSnapshot | CurrentSnapshot;

/**
 * This is the only data shape the public renderer understands. A future
 * private adapter can implement this boundary without importing this module's
 * authored scenario or exposing task identifiers.
 */
export interface FactoryDataProvider {
  getSnapshot(): Promise<FactorySnapshot>;
}

const scenarioOffices: FactoryOffice[] = [
  {
    id: "growth",
    name: "Growth",
    shortName: "Growth",
    descriptor: "Campaign planning workshop",
    roomNumber: "01",
    color: 0x3d72ff,
    process: ["Frame the question", "Choose a useful distribution test", "Record what changed"],
    tasks: ["Compare source paths", "Prepare a small distribution experiment", "Leave a dated observation"],
    receipts: [
      { label: "Scenario input", value: "A question worth tracing", kind: "source" },
      { label: "Next dependency", value: "A reviewed passage", kind: "decision" },
    ],
  },
  {
    id: "directories",
    name: "Directories",
    shortName: "Directories",
    descriptor: "Distribution registry station",
    roomNumber: "02",
    color: 0x5e8eff,
    process: ["Check the destination", "Submit only when the form is clear", "Keep acceptance separate from submission"],
    tasks: ["Review listing requirements", "Record a public destination", "Wait for a response"],
    receipts: [
      { label: "Receipt type", value: "Public destination", kind: "output" },
      { label: "Boundary", value: "Submission is not acceptance", kind: "hold" },
    ],
  },
  {
    id: "product",
    name: "Product",
    shortName: "Product",
    descriptor: "Planning and acceptance room",
    roomNumber: "03",
    color: 0x2c5fe8,
    process: ["Name the user question", "Choose the smallest useful check", "Review the result"],
    tasks: ["Keep the example concrete", "Make limitations visible", "Connect the tool to its source"],
    receipts: [
      { label: "Output", value: "A usable check", kind: "output" },
      { label: "Review", value: "Human acceptance required", kind: "decision" },
    ],
  },
  {
    id: "design",
    name: "Design",
    shortName: "Design",
    descriptor: "Interface and asset workshop",
    roomNumber: "04",
    color: 0x759bff,
    process: ["Make the path visible", "Keep the scene legible", "Polish after the loop works"],
    tasks: ["Arrange the room signs", "Protect focus and contrast", "Test the small screen"],
    receipts: [
      { label: "Design receipt", value: "Clear route through the factory", kind: "output" },
      { label: "Constraint", value: "Motion remains optional", kind: "hold" },
    ],
  },
  {
    id: "media",
    name: "Media",
    shortName: "Media",
    descriptor: "Production studio",
    roomNumber: "05",
    color: 0x416dca,
    process: ["Capture the useful moment", "Keep the source beside the claim", "Publish only a checked cut"],
    tasks: ["Review one short episode", "Keep the source traceable", "Separate a draft from a published result"],
    receipts: [
      { label: "Scenario output", value: "A source-led episode", kind: "output" },
      { label: "Status", value: "Illustrative only", kind: "hold" },
    ],
  },
  {
    id: "engineering",
    name: "Engineering",
    shortName: "Engineering",
    descriptor: "Build and test workshop",
    roomNumber: "06",
    color: 0x2245a9,
    process: ["Build the smallest slice", "Test the boundary", "Ship with a receipt"],
    tasks: ["Inspect the public adapter boundary", "Keep writes out of the renderer", "Record the build check"],
    receipts: [
      { label: "Boundary", value: "Read-only data shape", kind: "decision" },
      { label: "Build receipt", value: "Local bundle check", kind: "output" },
    ],
  },
  {
    id: "pipeline",
    name: "Pipeline",
    shortName: "Pipeline",
    descriptor: "Processing line and release gates",
    roomNumber: "07",
    color: 0x4e7ceb,
    process: ["Scout", "Curate", "Release or hold"],
    tasks: ["Follow the current stage", "Inspect a blocked gate", "Return to the source"],
    receipts: [
      { label: "Process", value: "Scout → Curation → Release", kind: "decision" },
      { label: "Current gate", value: "Rights review", kind: "hold" },
    ],
  },
  {
    id: "creator",
    name: "Creator desk",
    shortName: "Creator",
    descriptor: "Scout station and curation bench",
    roomNumber: "08",
    color: 0x8aa9ff,
    process: ["Find a candidate", "Read the original context", "Pass a bounded brief"],
    tasks: ["Scout one source", "Mark what is known", "Leave unknowns visible"],
    receipts: [
      { label: "Role", value: "Curation desk", kind: "decision" },
      { label: "Connection", value: "In progress in this scenario", kind: "hold" },
    ],
  },
];

export const OFFICES: readonly FactoryOffice[] = scenarioOffices;
export const OFFICE_IDS: readonly OfficeId[] = scenarioOffices.map((office) => office.id);

export const SCENARIO_STAGES: readonly ScenarioStage[] = [
  {
    id: "discover",
    label: "Scout",
    subtitle: "Find a question with a source",
    description: "The creator desk routes one candidate into the shared process.",
    officeIds: ["creator", "growth"],
    status: "complete",
    hold: false,
    role: "ChatGPT Scout",
  },
  {
    id: "rights-review",
    label: "Rights review",
    subtitle: "Hold before public use",
    description: "The source is held until its use and context are clear.",
    officeIds: ["pipeline", "product"],
    status: "held",
    hold: true,
  },
  {
    id: "curate",
    label: "Curation",
    subtitle: "Build a bounded passage",
    description: "A reviewed passage is shaped into a useful, limited brief.",
    officeIds: ["product", "design", "engineering"],
    status: "next",
    hold: false,
    role: "ChatGPT Curator",
  },
  {
    id: "release",
    label: "Release",
    subtitle: "Publish with a receipt",
    description: "A checked output can leave the line with a clear receipt.",
    officeIds: ["media", "directories", "pipeline"],
    status: "next",
    hold: false,
  },
];

const authoredCapturedAt = "2026-09-06T00:00:00Z";

export function createScenarioSnapshot(stageId: ScenarioStageId = "rights-review"): ScenarioSnapshot {
  return {
    mode: "scenario",
    label: "Scenario — not live operations",
    capturedAt: authoredCapturedAt,
    stageId,
    offices: scenarioOffices,
  };
}

export const scenarioProvider: FactoryDataProvider = {
  async getSnapshot() {
    return createScenarioSnapshot();
  },
};

export function officeById(id: OfficeId): FactoryOffice {
  const office = scenarioOffices.find((candidate) => candidate.id === id);
  if (!office) throw new Error(`Unknown office: ${id}`);
  return office;
}

export function stageById(id: ScenarioStageId): ScenarioStage {
  const stage = SCENARIO_STAGES.find((candidate) => candidate.id === id);
  if (!stage) throw new Error(`Unknown scenario stage: ${id}`);
  return stage;
}
