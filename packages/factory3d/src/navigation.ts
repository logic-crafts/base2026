import type { OfficeId } from "./data";

export interface Point2 {
  x: number;
  z: number;
}

export interface Point3 extends Point2 {
  y: number;
}

export const OFFICE_POSITIONS: Record<OfficeId, Point2> = {
  growth: { x: -15, z: -6.5 },
  directories: { x: -5, z: -6.5 },
  product: { x: 5, z: -6.5 },
  design: { x: 15, z: -6.5 },
  media: { x: -15, z: 6.5 },
  engineering: { x: -5, z: 6.5 },
  pipeline: { x: 5, z: 6.5 },
  creator: { x: 15, z: 6.5 },
};

export const START_POINT: Point3 = { x: 0, y: 1, z: 0 };

/** Authored routes stay on the open central circulation floor. */
export function routeBetween(from: Point3, officeId: OfficeId): Point3[] {
  const destination = OFFICE_POSITIONS[officeId];
  const entranceZ = destination.z < 0 ? -3 : 3;
  const approachX = destination.x;
  return [
    { ...from },
    { x: from.x, y: 1, z: 0 },
    { x: approachX, y: 1, z: 0 },
    { x: approachX, y: 1, z: entranceZ },
    { x: destination.x, y: 1, z: destination.z },
  ];
}

export function routeLength(points: readonly Point3[]): number {
  let length = 0;
  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1];
    const current = points[index];
    length += Math.hypot(current.x - previous.x, current.z - previous.z, current.y - previous.y);
  }
  return length;
}

export function sampleRoute(points: readonly Point3[], progress: number): Point3 {
  if (points.length === 0) return { ...START_POINT };
  if (points.length === 1) return { ...points[0] };
  const target = Math.min(1, Math.max(0, progress));
  const total = routeLength(points);
  if (total === 0) return { ...points[0] };
  let remaining = target * total;
  for (let index = 1; index < points.length; index += 1) {
    const previous = points[index - 1];
    const current = points[index];
    const segment = Math.hypot(current.x - previous.x, current.z - previous.z, current.y - previous.y);
    if (remaining <= segment || index === points.length - 1) {
      const ratio = segment === 0 ? 1 : remaining / segment;
      return {
        x: previous.x + (current.x - previous.x) * ratio,
        y: previous.y + (current.y - previous.y) * ratio,
        z: previous.z + (current.z - previous.z) * ratio,
      };
    }
    remaining -= segment;
  }
  return { ...points[points.length - 1] };
}

export function clampZoom(distance: number, min = 14, max = 36): number {
  return Math.min(max, Math.max(min, distance));
}

/**
 * Fit the world bounds in the default three-quarter view. Projecting the
 * eight box corners avoids the excess empty space of a bounding-sphere fit.
 */
export function overviewCameraDistance(
  aspect: number,
  verticalFovDegrees = 38,
  halfWidth = 21.5,
  halfDepth = 13,
  height = 4.2,
  padding = 1.08,
): number {
  const safeAspect = Number.isFinite(aspect) ? Math.max(0.2, aspect) : 1;
  const safeFov = Number.isFinite(verticalFovDegrees)
    ? Math.min(120, Math.max(1, verticalFovDegrees))
    : 38;
  const verticalFov = safeFov * Math.PI / 180;
  const verticalTangent = Math.tan(verticalFov / 2);
  const horizontalTangent = verticalTangent * safeAspect;
  const length = Math.hypot(26, 23, 28);
  const backward = { x: 26 / length, y: 23 / length, z: 28 / length };
  const sideLength = Math.hypot(backward.x, backward.z);
  const right = { x: backward.z / sideLength, y: 0, z: -backward.x / sideLength };
  const up = {
    x: backward.y * right.z,
    y: backward.z * right.x - backward.x * right.z,
    z: -backward.y * right.x,
  };
  let distance = 1;
  for (const x of [-Math.max(0, halfWidth), Math.max(0, halfWidth)]) {
    for (const z of [-Math.max(0, halfDepth), Math.max(0, halfDepth)]) {
      for (const y of [0, Math.max(0, height)]) {
        const depth = x * backward.x + y * backward.y + z * backward.z;
        const horizontal = Math.abs(x * right.x + z * right.z);
        const vertical = Math.abs(x * up.x + y * up.y + z * up.z);
        distance = Math.max(distance, depth + Math.max(1, padding) * horizontal / horizontalTangent, depth + Math.max(1, padding) * vertical / verticalTangent);
      }
    }
  }
  return distance;
}

export type InspectorAnimationState = "idle" | "walk";

/** Keep animation transitions idempotent so reset/play is only called on a real state change. */
export function inspectorAnimationTransition(
  current: InspectorAnimationState,
  moving: boolean,
): { state: InspectorAnimationState; changed: boolean } {
  const state: InspectorAnimationState = moving ? "walk" : "idle";
  return { state, changed: state !== current };
}

export function isTap(start: Point2, end: Point2, threshold = 6): boolean {
  return Math.hypot(end.x - start.x, end.z - start.z) <= threshold;
}

export function cycleOffice(current: OfficeId, direction: 1 | -1): OfficeId {
  const ids = Object.keys(OFFICE_POSITIONS) as OfficeId[];
  const index = ids.indexOf(current);
  return ids[(index + direction + ids.length) % ids.length];
}

export function rotateAngle(angle: number, delta: number): number {
  const result = angle + delta;
  return ((result + Math.PI) % (Math.PI * 2)) - Math.PI;
}
