import { Anchor } from '../types';

/** 4 ft × 4 ft (48 in) square platform — coordinates in feet */
export const PLATFORM_FT = 4.0;

const COLORS = ['#0ea5e9', '#34d399', '#a78bfa', '#f472b6', '#fbbf24', '#fb923c'];
const LABEL_POSITIONS: Anchor['labelPosition'][] = ['bottom', 'top', 'bottom', 'right', 'left', 'top'];

export interface ServerAnchor {
  name: string;
  x: number;
  y: number;
}

/** Map server ANCHORS config to dashboard anchor markers. */
export function mapServerAnchors(serverAnchors: ServerAnchor[]): Anchor[] {
  return serverAnchors.map((a, i) => ({
    id: a.name.toLowerCase().replace(/[^a-z0-9]/g, '_'),
    name: a.name.toUpperCase().replace(/\s/g, '_'),
    x: a.x,
    y: a.y,
    color: COLORS[i % COLORS.length],
    labelPosition: LABEL_POSITIONS[i % LABEL_POSITIONS.length],
  }));
}

// Four corners of the 4×4 ft board (matches server.py layout)
export const DEFAULT_ANCHORS: Anchor[] = mapServerAnchors([
  { name: 'Anchor_A', x: 0, y: 0 },
  { name: 'Anchor_B', x: 0, y: PLATFORM_FT },
  { name: 'Anchor_C', x: PLATFORM_FT, y: 0 },
  { name: 'Anchor_D', x: PLATFORM_FT, y: PLATFORM_FT },
]);
