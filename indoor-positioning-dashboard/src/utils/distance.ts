import { Anchor } from '../types';

/**
 * Calculates Euclidean distance between two 2D points
 */
export function getDistance(x1: number, y1: number, x2: number, y2: number): number {
  return Math.sqrt(Math.pow(x2 - x1, 2) + Math.pow(y2 - y1, 2));
}

/**
 * Generates box-muller transform random value for simulating natural Gaussian noise
 */
export function generateGaussianNoise(mean: number = 0, stdDev: number = 1): number {
  const u1 = Math.random();
  const u2 = Math.random();
  if (u1 === 0) return mean; // keep safe from log(0)
  const randStdNormal = Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
  return mean + stdDev * randStdNormal;
}

/**
 * Formats seconds into simple hh:mm:ss
 */
export function formatTime(timestamp: number): string {
  const date = new Date(timestamp);
  return date.toTimeString().split(' ')[0] + '.' + String(date.getMilliseconds()).padStart(3, '0');
}

/**
 * Basic 2D Trilateration algorithm for demonstration (if desired)
 * Using Anchor A(0,0), B(0,4), C(5,0)
 * Let's calculate estimated coordinates based on distances from these three anchors
 */
export function trilaterate(
  anchorA: Anchor,
  anchorB: Anchor,
  anchorC: Anchor,
  r1: number, // distance from A
  r2: number, // distance from B
  r3: number  // distance from C
): { x: number; y: number; error: number } | null {
  try {
    // Math model using standard trilateration for three spheres/circles
    // A is at (x1, y1) = (0,0)
    // B is at (x2, y2) = (0,4)
    // C is at (x3, y3) = (5,0)
    
    // We can simplify calculations with these specific anchors:
    // Circle A: x^2 + y^2 = r1^2
    // Circle B: x^2 + (y - 4)^2 = r2^2  => x^2 + y^2 - 8y + 16 = r2^2 => r1^2 - 8y + 16 = r2^2 => y = (r1^2 - r2^2 + 16) / 8
    // Circle C: (x - 5)^2 + y^2 = r3^2  => x^2 - 10x + 25 + y^2 = r3^2 => r1^2 - 10x + 25 = r3^2 => x = (r1^2 - r3^2 + 25) / 10
    
    const y = (Math.pow(r1, 2) - Math.pow(r2, 2) + Math.pow(anchorB.y, 2)) / (2 * anchorB.y);
    const x = (Math.pow(r1, 2) - Math.pow(r3, 2) + Math.pow(anchorC.x, 2)) / (2 * anchorC.x);
    
    // Back-calculate expected radii to evaluate the error
    const d1 = getDistance(x, y, anchorA.x, anchorA.y);
    const d2 = getDistance(x, y, anchorB.x, anchorB.y);
    const d3 = getDistance(x, y, anchorC.x, anchorC.y);
    
    const error = (Math.abs(d1 - r1) + Math.abs(d2 - r2) + Math.abs(d3 - r3)) / 3;
    
    return { x: isNaN(x) ? 0 : x, y: isNaN(y) ? 0 : y, error: isNaN(error) ? 0 : error };
  } catch (e) {
    return null;
  }
}

/** Weight for multilateration — closer anchors dominate (matches server). */
function anchorWeight(distance: number): number {
  return 1 / Math.max(distance, 0.25) ** 2;
}

export interface SolvedPosition {
  x: number;
  y: number;
  error: number;
  conflict: boolean;
}

/**
 * Solve (x,y) from displayed anchor distances using weighted least squares.
 */
export function solvePositionFromDistances(
  anchors: Anchor[],
  distances: Record<string, number> | undefined,
  roomWidth: number,
  roomHeight: number,
): SolvedPosition | null {
  if (!distances) return null;

  const samples = anchors
    .map((a) => {
      const d = getAnchorDistance(distances, a.name, a.id);
      return d !== null ? { ax: a.x, ay: a.y, d, w: anchorWeight(d) } : null;
    })
    .filter((s): s is { ax: number; ay: number; d: number; w: number } => s !== null);

  if (samples.length < 3) return null;

  const closest = samples.reduce((a, b) => (a.d < b.d ? a : b));
  let x = Math.max(0, Math.min(roomWidth, closest.ax + closest.d * 0.5));
  let y = Math.max(0, Math.min(roomHeight, closest.ay + closest.d * 0.5));

  for (let iter = 0; iter < 80; iter++) {
    let gx = 0;
    let gy = 0;
    for (const { ax, ay, d, w } of samples) {
      const dist = Math.max(getDistance(x, y, ax, ay), 0.01);
      const err = dist - d;
      gx += w * err * (x - ax) / dist;
      gy += w * err * (y - ay) / dist;
    }
    x -= 0.35 * gx;
    y -= 0.35 * gy;
    x = Math.max(0, Math.min(roomWidth, x));
    y = Math.max(0, Math.min(roomHeight, y));
  }

  const error =
    samples.reduce((sum, { ax, ay, d }) => sum + Math.abs(getDistance(x, y, ax, ay) - d), 0) /
    samples.length;

  return { x, y, error, conflict: error > 0.8 };
}

/**
 * Safely fetches distance for a given anchor from the IPS payload,
 * handling case sensitivity, spaces, and formatting variations.
 */
export function getAnchorDistance(
  distances: Record<string, number> | undefined,
  anchorName: string,
  anchorId: string
): number | null {
  if (!distances) return null;

  // 1. Direct key match (e.g. "ANCHOR_A" or "anch_a")
  if (distances[anchorName] !== undefined && distances[anchorName] !== null) {
    return distances[anchorName];
  }
  if (distances[anchorId] !== undefined && distances[anchorId] !== null) {
    return distances[anchorId];
  }

  // 2. Normalize and check keys (e.g., "Anchor_A", "ANCHOR_A", "anch_a" -> "anchora")
  const normalize = (s: string) => s.toLowerCase().replace(/[-_\s]/g, '');
  const normName = normalize(anchorName);
  const normId = normalize(anchorId);

  for (const [key, value] of Object.entries(distances)) {
    const normKey = normalize(key);
    if (normKey === normName || normKey === normId || normKey.includes(normName) || normName.includes(normKey)) {
      if (typeof value === 'number') {
        return value;
      }
    }
  }

  return null;
}
