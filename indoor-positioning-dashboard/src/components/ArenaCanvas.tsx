import React, { useRef, useState, useEffect } from 'react';
import { Camera, RefreshCw, Eye, EyeOff, Radio, Compass, Orbit } from 'lucide-react';
import { Anchor, PathPoint, IPSPayload, DashboardSettings } from '../types';
import { getDistance, getAnchorDistance, solvePositionFromDistances } from '../utils/distance';

interface ArenaCanvasProps {
  currentPayload: IPSPayload | null;
  anchors: Anchor[];
  trail: PathPoint[];
  settings: DashboardSettings;
  setSettings: React.Dispatch<React.SetStateAction<DashboardSettings>>;
  onManualMove?: (x: number, y: number) => void;
  simulatorEnabled: boolean;
  simulatorPattern: string;
}

export default function ArenaCanvas({
  currentPayload,
  anchors,
  trail,
  settings,
  setSettings,
  onManualMove,
  simulatorEnabled,
  simulatorPattern,
}: ArenaCanvasProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 450, height: 450 });
  const [isDragging, setIsDragging] = useState(false);
  const [showRays, setShowRays] = useState(true);

  // Resize listener to make coordinates container fluidly responsive
  useEffect(() => {
    if (!containerRef.current) return;
    const resizeObserver = new ResizeObserver((entries) => {
      for (let entry of entries) {
        const { width } = entry.contentRect;
        // Keep a 1:1 square ratio for standard room sizing
        const size = Math.max(560, Math.min(width, 800));
        setDimensions({ width: size, height: size });
      }
    });
    resizeObserver.observe(containerRef.current);
    return () => resizeObserver.disconnect();
  }, []);

  const padding = 64;
  const innerWidth = dimensions.width - padding * 2;
  const innerHeight = dimensions.height - padding * 2;

  // Feet → SVG pixels (uniform scale so circles match real distances)
  const scaleX = innerWidth / settings.roomWidth;
  const feetToPixels = (feet: number) => feet * scaleX;

  const getPixels = (x: number, y: number) => {
    const px = padding + (x / settings.roomWidth) * innerWidth;
    const py = dimensions.height - padding - (y / settings.roomHeight) * innerHeight;
    return { x: px, y: py };
  };

  // Convert SVG pixels back to real-world coordinates (meters)
  const getCoordinates = (px: number, py: number) => {
    const x = ((px - padding) / innerWidth) * settings.roomWidth;
    const y = ((dimensions.height - padding - py) / innerHeight) * settings.roomHeight;
    // Bound coordinates inside the room
    return {
      x: Math.max(0, Math.min(settings.roomWidth, Math.round(x * 100) / 100)),
      y: Math.max(0, Math.min(settings.roomHeight, Math.round(y * 100) / 100)),
    };
  };

  const handlePointerDown = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!simulatorEnabled || simulatorPattern !== 'manual' || !onManualMove) return;
    setIsDragging(true);
    e.currentTarget.setPointerCapture(e.pointerId);
    updateCoordinatesFromEvent(e);
  };

  const handlePointerMove = (e: React.PointerEvent<SVGSVGElement>) => {
    if (!isDragging || !onManualMove) return;
    updateCoordinatesFromEvent(e);
  };

  const handlePointerUp = (e: React.PointerEvent<SVGSVGElement>) => {
    setIsDragging(false);
    e.currentTarget.releasePointerCapture(e.pointerId);
  };

  const updateCoordinatesFromEvent = (e: React.PointerEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    const coords = getCoordinates(px, py);
    onManualMove(coords.x, coords.y);
  };

  // Create list of lines for grid coordinates
  const gridLinesX = [];
  const gridLinesY = [];
  for (let i = 0; i <= settings.roomWidth; i += settings.gridResolution) {
    gridLinesX.push(i);
  }
  for (let i = 0; i <= settings.roomHeight; i += settings.gridResolution) {
    gridLinesY.push(i);
  }

  // Plot from the same distance numbers shown in the sidebar (weighted multilateration)
  const solved = currentPayload
    ? solvePositionFromDistances(
        anchors,
        currentPayload.distances,
        settings.roomWidth,
        settings.roomHeight,
      )
    : null;
  const targetX = solved?.x ?? (currentPayload ? currentPayload.x : null);
  const targetY = solved?.y ?? (currentPayload ? currentPayload.y : null);
  const targetPx = targetX !== null && targetY !== null ? getPixels(targetX, targetY) : null;

  return (
    <div className="flex flex-col h-full ips-card p-5" id="ips-arena-card">
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4 select-none">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded bg-sky-100 text-sky-800">
            <Compass className="w-6 h-6" />
          </div>
          <div>
            <h3 className="ips-heading text-lg">Coordinate Arena</h3>
            <p className="ips-muted font-semibold">{settings.roomLabel || `${settings.roomWidth}${settings.unit} × ${settings.roomHeight}${settings.unit}`}</p>
          </div>
        </div>

        {/* Action Toggles */}
        <div className="flex items-center gap-1 bg-slate-100 p-1.5 rounded-lg border ips-border">
          <button
            onClick={() => setSettings(prev => ({ ...prev, showRings: !prev.showRings }))}
            className={`px-3 py-1.5 text-sm font-semibold rounded-md transition-colors flex items-center gap-2 ${
              settings.showRings
                ? 'bg-sky-100 text-sky-900 border border-sky-300'
                : 'text-slate-600 hover:text-slate-900'
            }`}
            title="Toggle Trilateration Circles"
            id="toggle-rings-btn"
          >
            {settings.showRings ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            <span>Rings</span>
          </button>
          
          <button
            onClick={() => setSettings(prev => ({ ...prev, showTrail: !prev.showTrail }))}
            className={`px-3 py-1.5 text-sm font-semibold rounded-md transition-colors flex items-center gap-2 ${
              settings.showTrail
                ? 'bg-sky-100 text-sky-900 border border-sky-300'
                : 'text-slate-600 hover:text-slate-900'
            }`}
            title="Toggle Historical Path Trail"
            id="toggle-trail-btn"
          >
            {settings.showTrail ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            <span>Trail</span>
          </button>

          <button
            onClick={() => setShowRays(!showRays)}
            className={`px-3 py-1.5 text-sm font-semibold rounded-md transition-colors flex items-center gap-2 ${
              showRays
                ? 'bg-sky-100 text-sky-900 border border-sky-300'
                : 'text-slate-600 hover:text-slate-900'
            }`}
            title="Toggle Distance Rays"
            id="toggle-rays-btn"
          >
            {showRays ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
            <span>Distances</span>
          </button>
        </div>
      </div>
      {/* Main Coordinate System Box */}
      <div 
        ref={containerRef} 
        className="flex-1 flex justify-center items-center overflow-hidden relative min-h-[300px] select-none"
        style={{ cursor: simulatorEnabled && simulatorPattern === 'manual' ? 'crosshair' : 'default' }}
      >
        <svg
          width={dimensions.width}
          height={dimensions.height}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          className="text-slate-400 overflow-visible relative"
          id="ips-position-svg"
        >
          {/* Definitions for gradients / filters */}
          <defs>
            <radialGradient id="target-glow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.8" />
              <stop offset="40%" stopColor="#f43f5e" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#f43f5e" stopOpacity="0" />
            </radialGradient>
            <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="4" stdDeviation="4" floodColor="#000" floodOpacity="0.5" />
            </filter>
          </defs>

          {/* SENSOR ROOM BOUNDARIES & GRID */}
          <rect
            x={padding}
            y={padding}
            width={innerWidth}
            height={innerHeight}
            className="fill-slate-100 stroke-slate-300 stroke-[1.5]"
          />

          {/* Subtle Grid Sub-Lines */}
          {gridLinesX.map((xVal) => {
            // Include intermediate tick lines every 0.1 meters
            const lines = [];
            for (let sub = 0.1; sub < settings.gridResolution; sub += 0.1) {
              const subX = xVal + sub;
              if (subX >= settings.roomWidth) break;
              const px = getPixels(subX, 0).x;
              lines.push(
                <line
                  key={`sub-grid-x-${xVal}-${sub}`}
                  x1={px}
                  y1={padding}
                  x2={px}
                  y2={dimensions.height - padding}
                  className="stroke-slate-900/40 stroke-[0.5]"
                />
              );
            }
            return lines;
          })}

          {gridLinesY.map((yVal) => {
            const lines = [];
            for (let sub = 0.1; sub < settings.gridResolution; sub += 0.1) {
              const subY = yVal + sub;
              if (subY >= settings.roomHeight) break;
              const py = getPixels(0, subY).y;
              lines.push(
                <line
                  key={`sub-grid-y-${yVal}-${sub}`}
                  x1={padding}
                  y1={py}
                  x2={dimensions.width - padding}
                  y2={py}
                  className="stroke-slate-900/40 stroke-[0.5]"
                />
              );
            }
            return lines;
          })}

          {/* Grid Lines Main (every 1.0m) */}
          {gridLinesX.map((xVal) => {
            const { x: px } = getPixels(xVal, 0);
            return (
              <g key={`grid-x-${xVal}`}>
                <line
                  x1={px}
                  y1={padding}
                  x2={px}
                  y2={dimensions.height - padding}
                  className="stroke-slate-800/70 stroke-[1]"
                  strokeDasharray="4 4"
                />
                {/* Meter labels on bottom axis */}
                <text
                  x={px}
                  y={dimensions.height - padding + 18}
                  textAnchor="middle"
                  className="fill-slate-700 font-bold text-[15px]"
                >
                  {xVal}{settings.unit}
                </text>
              </g>
            );
          })}

          {gridLinesY.map((yVal) => {
            const { y: py } = getPixels(0, yVal);
            return (
              <g key={`grid-y-${yVal}`}>
                <line
                  x1={padding}
                  y1={py}
                  x2={dimensions.width - padding}
                  y2={py}
                  className="stroke-slate-800/70 stroke-[1]"
                  strokeDasharray="4 4"
                />
                {/* Meter labels on left axis */}
                <text
                  x={padding - 10}
                  y={py + 3}
                  textAnchor="end"
                  className="fill-slate-700 font-bold text-[15px]"
                >
                  {yVal}{settings.unit}
                </text>
              </g>
            );
          })}

          {/* TRILATERATION ESTIMATION RINGS (Drawn around Anchors if selected) */}
          {settings.showRings && currentPayload && anchors.map((anchor) => {
            const dist = getAnchorDistance(currentPayload.distances, anchor.name, anchor.id);
            if (dist === null || dist === undefined) return null;

            const { x: ax, y: ay } = getPixels(anchor.x, anchor.y);
            const pixelRadius = feetToPixels(dist);

            return (
              <g key={`ring-${anchor.id}`}>
                {/* Solid core representation of current estimated radius boundary */}
                <circle
                  cx={ax}
                  cy={ay}
                  r={pixelRadius}
                  fill="none"
                  stroke={anchor.color}
                  strokeOpacity="0.15"
                  className="stroke-[1.5]"
                  strokeDasharray="6 3"
                />
                {/* Dynamic signal ripple simulation */}
                <circle
                  cx={ax}
                  cy={ay}
                  r={pixelRadius}
                  fill="none"
                  stroke={anchor.color}
                  strokeOpacity="0.05"
                  className="stroke-[3]"
                />
              </g>
            );
          })}

          {/* HISTORIC PATH BREADCRUMBS */}
          {settings.showTrail && trail.length > 1 && (
            <g id="ips-path-trail">
              {/* Path Connector Line */}
              <path
                d={trail
                  .map((point, index) => {
                    const { x, y } = getPixels(point.x, point.y);
                    return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
                  })
                  .join(' ')}
                fill="none"
                stroke="url(#trail-gradient)"
                className="stroke-[2]"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeOpacity="0.4"
              />
              <linearGradient id="trail-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#4338ca" stopOpacity="0.1" />
                <stop offset="50%" stopColor="#6366f1" stopOpacity="0.4" />
                <stop offset="100%" stopColor="#10b981" stopOpacity="0.9" />
              </linearGradient>

              {/* Individual historical breadcrumbs */}
              {trail.slice(0, -1).map((point, i) => {
                const { x, y } = getPixels(point.x, point.y);
                const progressRatio = i / trail.length; // newer points are larger/brighter
                return (
                  <circle
                    key={point.id}
                    cx={x}
                    cy={y}
                    r={2 + progressRatio * 2}
                    fill="#818cf8"
                    fillOpacity={0.15 + progressRatio * 0.5}
                  />
                );
              })}
            </g>
          )}

          {/* DISTANCE PATH RAYS (Lines connecting target to Anchors) */}
          {showRays && targetPx && anchors.map((anchor) => {
            const { x: ax, y: ay } = getPixels(anchor.x, anchor.y);
            const rawDist = currentPayload ? getAnchorDistance(currentPayload.distances, anchor.name, anchor.id) : null;
            if (rawDist === null) return null;

            // Ray length = measured RSSI distance (matches the circle radius)
            const pixelLen = feetToPixels(rawDist);
            const angle = Math.atan2(targetPx.y - ay, targetPx.x - ax);
            const endX = ax + Math.cos(angle) * pixelLen;
            const endY = ay + Math.sin(angle) * pixelLen;
            
            return (
              <g key={`ray-${anchor.id}`}>
                <line
                  x1={ax}
                  y1={ay}
                  x2={endX}
                  y2={endY}
                  stroke={anchor.color}
                  strokeOpacity="0.55"
                  strokeWidth="2"
                  strokeDasharray="6 4"
                />
                <g transform={`translate(${(ax + endX) / 2}, ${(ay + endY) / 2})`}>
                  <rect
                    x="-28"
                    y="-11"
                    width="56"
                    height="22"
                    rx="4"
                    className="fill-white stroke-slate-400"
                    strokeWidth="1"
                  />
                  <text
                    textAnchor="middle"
                    y="5"
                    className="fill-slate-900 font-semibold text-[14px]"
                  >
                    {rawDist.toFixed(2)}{settings.unit}
                  </text>
                </g>
              </g>
            );
          })}

          {/* STATIC ANCHOR DOTS */}
          {anchors.map((anchor) => {
            const { x: ax, y: ay } = getPixels(anchor.x, anchor.y);
            const isNearTarget = targetX !== null && targetY !== null 
              ? getDistance(anchor.x, anchor.y, targetX, targetY) < 1.0 
              : false;

            return (
              <g key={anchor.id} filter="url(#shadow)" className="group cursor-pointer">
                {/* Anchor pulse border if active/sensing */}
                <circle
                  cx={ax}
                  cy={ay}
                  r="14"
                  fill="none"
                  stroke={anchor.color}
                  strokeOpacity={isNearTarget ? "0.4" : "0.15"}
                  className={`stroke-[1] ${isNearTarget ? 'animate-pulse' : ''}`}
                />
                
                {/* Physical Anchor Dot */}
                <circle
                  cx={ax}
                  cy={ay}
                  r="7"
                  fill="#ffffff"
                  stroke={anchor.color}
                  className="stroke-[3]"
                />

                {/* Pulsing signal notification light inside */}
                <circle
                  cx={ax}
                  cy={ay}
                  r="2"
                  fill={anchor.color}
                  className="animate-ping"
                  style={{ animationDuration: '2s' }}
                />

                {/* Anchor Label Box */}
                <g transform={`translate(${ax}, ${ay})`} className="pointer-events-none select-none">
                  <rect
                    x={anchor.labelPosition === 'left' ? -84 : anchor.labelPosition === 'right' ? 12 : -38}
                    y={anchor.labelPosition === 'top' ? -30 : anchor.labelPosition === 'bottom' ? 12 : -11}
                    width="76"
                    height="22"
                    rx="4"
                    className="fill-white stroke-slate-400"
                    strokeWidth="1"
                  />
                  <text
                    x={anchor.labelPosition === 'left' ? -46 : anchor.labelPosition === 'right' ? 50 : 0}
                    y={anchor.labelPosition === 'top' ? -15 : anchor.labelPosition === 'bottom' ? 26 : 4}
                    textAnchor="middle"
                    className="fill-slate-900 font-bold text-[13px]"
                  >
                    {anchor.name}
                  </text>
                  <text
                    x={anchor.labelPosition === 'left' ? -46 : anchor.labelPosition === 'right' ? 50 : 0}
                    y={anchor.labelPosition === 'top' ? -2 : anchor.labelPosition === 'bottom' ? 38 : 17}
                    textAnchor="middle"
                    className="fill-slate-600 font-semibold text-[11px]"
                  >
                    ({anchor.x.toFixed(0)}, {anchor.y.toFixed(0)})
                  </text>
                </g>
              </g>
            );
          })}

          {/* DYNAMIC MOVING TARGET (T1) */}
          {targetPx && (
            <g filter="url(#shadow)" id="ips-moving-target" className="cursor-grab active:cursor-grabbing">
              {/* Animated locator radar ring */}
              <circle
                cx={targetPx.x}
                cy={targetPx.y}
                r="32"
                fill="url(#target-glow)"
                className="pointer-events-none animate-pulse"
                style={{ animationDuration: '2.5s' }}
              />

              {/* Exterior ring */}
              <circle
                cx={targetPx.x}
                cy={targetPx.y}
                r="10"
                fill="none"
                stroke="#f43f5e"
                strokeWidth="1.5"
                className="animate-spin-slow"
                strokeDasharray="4 2"
              />

              {/* Central Target Point */}
              <circle
                cx={targetPx.x}
                cy={targetPx.y}
                r="5"
                fill="#f43f5e"
                className="stroke-slate-950 stroke-[1.5]"
              />

              {/* Target ID overlay label */}
              <g transform={`translate(${targetPx.x}, ${targetPx.y - 20})`}>
                <rect
                  x="-24"
                  y="-12"
                  width="48"
                  height="20"
                  rx="4"
                  className="fill-white stroke-rose-500"
                  strokeWidth="1.5"
                />
                <text
                  textAnchor="middle"
                  y="3"
                  className="fill-rose-700 font-bold text-[13px]"
                >
                  {currentPayload?.target_id || 'T1'}
                </text>
              </g>

              {/* Axis alignment lines displaying intersection coordinates */}
              <line
                x1={padding}
                y1={targetPx.y}
                x2={targetPx.x}
                y2={targetPx.y}
                className="stroke-rose-500/20 stroke-[1]"
                strokeDasharray="2 2"
              />
              <line
                x1={targetPx.x}
                y1={targetPx.y}
                x2={targetPx.x}
                y2={dimensions.height - padding}
                className="stroke-rose-500/20 stroke-[1]"
                strokeDasharray="2 2"
              />

              {/* Coordinate projection bubbles on axes */}
              <g transform={`translate(${padding - 8}, ${targetPx.y})`}>
                <rect x="-32" y="-10" width="32" height="20" rx="4" className="fill-white stroke-rose-400" strokeWidth="1" />
                <text textAnchor="middle" x="-16" y="5" className="fill-rose-800 font-bold text-[12px]">
                  {targetY?.toFixed(2)}
                </text>
              </g>
              <g transform={`translate(${targetPx.x}, ${dimensions.height - padding + 6})`}>
                <rect x="-16" y="2" width="32" height="20" rx="4" className="fill-white stroke-rose-400" strokeWidth="1" />
                <text textAnchor="middle" y="16" className="fill-rose-800 font-bold text-[12px]">
                  {targetX?.toFixed(2)}
                </text>
              </g>
            </g>
          )}

          {/* DRAGGABILITY USER GUIDE FOOTER */}
          {simulatorEnabled && simulatorPattern === 'manual' && (
            <g transform={`translate(${padding + 10}, ${padding + 22})`} className="pointer-events-none opacity-85">
              <rect x="-4" y="-12" width="210" height="18" rx="4" className="fill-indigo-950/90 stroke-indigo-500/50 stroke-[0.7]" />
              <text y="0" className="fill-indigo-300 font-sans text-[9.5px]">
                💡 Click & Drag anywhere inside the arena grid!
              </text>
            </g>
          )}
        </svg>
      </div>

      {/* Numerical Coordinate Quick-Check */}
      {currentPayload && (
        <div className="mt-3 p-4 bg-slate-50 rounded-lg border ips-border flex flex-col gap-2">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2 text-base text-slate-800 font-semibold">
              <span>Target:</span>
              <span className="ips-value text-xl text-emerald-800">
                X = {targetX?.toFixed(2)} {settings.unit}, Y = {targetY?.toFixed(2)} {settings.unit}
              </span>
            </div>
            <div className="ips-muted font-semibold">
              Area: {settings.roomWidth * settings.roomHeight} ft²
            </div>
          </div>
          {solved?.conflict && (
            <p className="text-sm font-semibold text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2">
              Anchor distances conflict (fit error {solved.error.toFixed(2)} ft) — position favors the nearest anchor.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
