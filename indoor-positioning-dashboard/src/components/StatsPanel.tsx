import React, { useMemo } from 'react';
import { Radio, Signal, Activity, TrendingUp, ShieldCheck } from 'lucide-react';
import { IPSPayload, Anchor, DashboardSettings } from '../types';
import { getDistance, getAnchorDistance, solvePositionFromDistances } from '../utils/distance';

interface StatsPanelProps {
  currentPayload: IPSPayload | null;
  previousPayload: IPSPayload | null;
  anchors: Anchor[];
  settings: DashboardSettings;
  connectionStatus: string;
}

export default function StatsPanel({
  currentPayload,
  previousPayload,
  anchors,
  settings,
  connectionStatus,
}: StatsPanelProps) {
  const updateRateHz = useMemo(() => {
    if (!currentPayload || !previousPayload) return 0;
    const deltaMs = currentPayload.timestamp - previousPayload.timestamp;
    if (deltaMs <= 0) return 0;
    return Math.round(1000 / deltaMs);
  }, [currentPayload, previousPayload]);

  const instantSpeed = useMemo(() => {
    if (!currentPayload || !previousPayload) return 0;
    const dist = getDistance(currentPayload.x, currentPayload.y, previousPayload.x, previousPayload.y);
    const timeSec = (currentPayload.timestamp - previousPayload.timestamp) / 1000;
    if (timeSec <= 0) return 0;
    return dist / timeSec;
  }, [currentPayload, previousPayload]);

  const solvedPosition = useMemo(() => {
    if (!currentPayload) return null;
    return solvePositionFromDistances(
      anchors,
      currentPayload.distances,
      settings.roomWidth,
      settings.roomHeight,
    );
  }, [currentPayload, anchors, settings.roomWidth, settings.roomHeight]);

  const displayX = solvedPosition?.x ?? currentPayload?.x;
  const displayY = solvedPosition?.y ?? currentPayload?.y;

  // Platform edge length (4 ft) — NOT diagonal (which wrongly showed as 6 ft)
  const platformMax = Math.max(settings.roomWidth, settings.roomHeight);

  return (
    <div className="flex flex-col gap-4 h-full" id="ips-stats-panel">
      <div className="ips-card p-5">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className={`w-3 h-3 rounded-full ${connectionStatus === 'connected' ? 'bg-emerald-500' : 'bg-red-500'}`} />
            <span className="ips-heading text-base">Target Telemetry</span>
          </div>
          <span className="ips-muted font-semibold">ID: {currentPayload?.target_id || 'T1'}</span>
        </div>

        <div className="grid grid-cols-2 gap-4 my-2">
          <div className="bg-slate-50 rounded-lg p-4 border ips-border">
            <span className="ips-label">X Axis</span>
            <div className="ips-value mt-1">
              {displayX !== undefined ? displayX.toFixed(2) : '0.00'}
              <span className="text-lg font-semibold text-slate-600 ml-1">{settings.unit}</span>
            </div>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 border ips-border">
            <span className="ips-label">Y Axis</span>
            <div className="ips-value mt-1">
              {displayY !== undefined ? displayY.toFixed(2) : '0.00'}
              <span className="text-lg font-semibold text-slate-600 ml-1">{settings.unit}</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 mt-4 pt-4 border-t ips-border">
          <div className="flex items-center gap-3">
            <TrendingUp className="w-5 h-5 text-slate-600" />
            <div>
              <p className="ips-label">Velocity</p>
              <p className="ips-value-sm text-rose-700">
                {currentPayload ? `${instantSpeed.toFixed(2)} ${settings.unit}/s` : `0.00 ${settings.unit}/s`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Activity className="w-5 h-5 text-slate-600" />
            <div>
              <p className="ips-label">Update Rate</p>
              <p className="ips-value-sm text-sky-800">
                {connectionStatus === 'connected' && updateRateHz > 0 ? `${updateRateHz} Hz` : '0 Hz'}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="ips-card p-5 flex-1">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-sky-700" />
            <h3 className="ips-heading text-base">Anchor Signal Weights</h3>
          </div>
          <span className="ips-muted font-semibold">{anchors.length} anchors</span>
        </div>

        <div className="flex flex-col gap-4">
          {anchors.map((anchor) => {
            const rawDist = currentPayload ? getAnchorDistance(currentPayload.distances, anchor.name, anchor.id) : null;
            const rawSignalStr = rawDist !== null
              ? Math.max(12, Math.round(100 - (rawDist / platformMax) * 90))
              : 0;
            const signalStrengthColor =
              rawSignalStr > 75 ? 'text-emerald-700' :
              rawSignalStr > 40 ? 'text-amber-700' : 'text-rose-700';

            return (
              <div key={anchor.id} className="bg-slate-50 p-4 rounded-lg border ips-border">
                <div className="flex justify-between items-center mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full border-2" style={{ borderColor: anchor.color, backgroundColor: anchor.color + '40' }} />
                    <span className="ips-subheading">{anchor.name}</span>
                    <span className="ips-muted">({anchor.x.toFixed(1)}, {anchor.y.toFixed(1)} {settings.unit})</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Signal className={`w-5 h-5 ${signalStrengthColor}`} />
                    <span className="ips-muted font-semibold">
                      {rawDist !== null ? `${rawSignalStr}%` : 'offline'}
                    </span>
                  </div>
                </div>

                <div className="h-2 w-full bg-slate-200 rounded overflow-hidden">
                  <div
                    className="h-full transition-all duration-300"
                    style={{
                      width: rawDist !== null ? `${Math.min(100, (rawDist / platformMax) * 100)}%` : '0%',
                      backgroundColor: anchor.color,
                    }}
                  />
                </div>

                <div className="flex justify-between mt-2 ips-muted font-semibold">
                  <span>0 {settings.unit}</span>
                  <span className="ips-value-sm text-base">
                    {rawDist !== null ? `${rawDist.toFixed(2)} ${settings.unit}` : '--'}
                  </span>
                  <span>{platformMax.toFixed(0)} {settings.unit}</span>
                </div>
              </div>
            );
          })}
        </div>

        {currentPayload && solvedPosition && (
          <div className={`mt-4 p-4 rounded-lg border ${
            solvedPosition.conflict
              ? 'bg-amber-50 border-amber-300'
              : 'bg-sky-50 border-sky-200'
          }`}>
            <h4 className={`ips-label flex items-center gap-2 mb-2 ${
              solvedPosition.conflict ? 'text-amber-900' : 'text-sky-900'
            }`}>
              <ShieldCheck className="w-5 h-5" />
              {solvedPosition.conflict ? 'Conflicting anchor readings' : 'Position accuracy'}
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <span className="ips-muted">Circle fit error</span>
                <p className="ips-value-sm">{solvedPosition.error.toFixed(2)} {settings.unit}</p>
              </div>
              <div>
                <span className="ips-muted">Status</span>
                <p className="ips-value-sm">
                  {solvedPosition.conflict
                    ? 'Near strongest anchor'
                    : solvedPosition.error < 0.3
                      ? 'Good'
                      : 'Noisy'}
                </p>
              </div>
            </div>
            {solvedPosition.conflict && (
              <p className="text-sm text-amber-900 mt-2 font-semibold">
                Distances cannot all be true at one point (e.g. 0.25 ft from A but 1.26 ft from B). The dot is placed near the closest anchor.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
