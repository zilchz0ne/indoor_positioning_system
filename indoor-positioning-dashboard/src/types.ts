export interface IPSPayload {
  target_id: string;
  x: number;
  y: number;
  distances: Record<string, number>;
  rssi?: Record<string, number>;
  timestamp: number;
}

export interface Anchor {
  id: string;
  name: string;
  x: number; // platform units (feet)
  y: number;
  color: string;
  labelPosition: 'top' | 'bottom' | 'left' | 'right';
}

export interface PathPoint {
  x: number;
  y: number;
  timestamp: number;
  id: string;
}

export type ConnectionStatus = 'connected' | 'disconnected' | 'connecting' | 'error';

export interface SimulatorConfig {
  enabled: boolean;
  pattern: 'circle' | 'random_walk' | 'infinity' | 'manual';
  speed: number; // updates speed coefficient
  noise: number; // uncertainty noise in meters
}

export interface DashboardSettings {
  showRings: boolean;
  showTrail: boolean;
  maxTrailPoints: number;
  roomWidth: number; // feet
  roomHeight: number; // feet
  gridResolution: number; // grid line spacing in feet
  unit: string; // display unit, e.g. "ft"
  roomLabel: string; // human-readable platform size
}
