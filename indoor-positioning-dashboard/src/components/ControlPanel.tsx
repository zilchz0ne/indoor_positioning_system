import React, { useState } from 'react';
import { Trash2, Server, Sliders, RefreshCw, Zap, Compass } from 'lucide-react';
import { ConnectionStatus, SimulatorConfig, DashboardSettings } from '../types';

interface ControlPanelProps {
  wsUrl: string;
  setWsUrl: (url: string) => void;
  connectionStatus: ConnectionStatus;
  connectToWebSocket: () => void;
  disconnectFromWebSocket: () => void;
  simulatorConfig: SimulatorConfig;
  setSimulatorConfig: React.Dispatch<React.SetStateAction<SimulatorConfig>>;
  settings: DashboardSettings;
  setSettings: React.Dispatch<React.SetStateAction<DashboardSettings>>;
  onClearTrail: () => void;
}

export default function ControlPanel({
  wsUrl,
  setWsUrl,
  connectionStatus,
  connectToWebSocket,
  disconnectFromWebSocket,
  simulatorConfig,
  setSimulatorConfig,
  settings,
  setSettings,
  onClearTrail,
}: ControlPanelProps) {
  const [showConfig, setShowConfig] = useState(false);

  const getStatusBadge = () => {
    switch (connectionStatus) {
      case 'connected':
        return (
          <span className="flex items-center gap-2 px-3 py-1 rounded-lg text-sm font-bold bg-emerald-50 text-emerald-800 border border-emerald-300">
            <span className="h-2 w-2 rounded-full bg-emerald-600 animate-pulse" />
            Connected
          </span>
        );
      case 'connecting':
        return (
          <span className="flex items-center gap-2 px-3 py-1 rounded-lg text-sm font-bold bg-sky-50 text-sky-800 border border-sky-300 animate-pulse">
            <RefreshCw className="h-4 w-4 animate-spin" />
            Connecting…
          </span>
        );
      case 'error':
        return (
          <span className="flex items-center gap-2 px-3 py-1 rounded-lg text-sm font-bold bg-amber-50 text-amber-800 border border-amber-300">
            Connection error
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-2 px-3 py-1 rounded-lg text-sm font-bold bg-rose-50 text-rose-800 border border-rose-300">
            Disconnected
          </span>
        );
    }
  };

  const inputClass =
    'flex-1 bg-white px-3 py-2 rounded-lg text-base border ips-border focus:outline-none focus:border-sky-600 text-slate-900 disabled:opacity-50';

  return (
    <div className="flex flex-col gap-4 ips-card p-5 select-none text-slate-800" id="ips-control-card">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b ips-border">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-sky-100 text-sky-800">
            <Server className="w-5 h-5" />
          </div>
          <h3 className="ips-heading text-lg">Server connection</h3>
        </div>
        {getStatusBadge()}
      </div>

      <div className="flex flex-col gap-2">
        <label className="ips-label">WebSocket address</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={wsUrl}
            onChange={(e) => setWsUrl(e.target.value)}
            disabled={connectionStatus === 'connected' || connectionStatus === 'connecting'}
            placeholder="ws://localhost:8765"
            className={inputClass}
            id="ws-endpoint-input"
          />
          {connectionStatus === 'connected' || connectionStatus === 'connecting' ? (
            <button
              onClick={disconnectFromWebSocket}
              className="px-4 py-2 bg-rose-50 hover:bg-rose-100 border border-rose-300 text-rose-800 rounded-lg text-base font-bold"
              id="ws-disconnect-btn"
            >
              Disconnect
            </button>
          ) : (
            <button
              onClick={connectToWebSocket}
              className="px-4 py-2 bg-sky-700 hover:bg-sky-800 text-white rounded-lg text-base font-bold flex items-center gap-2"
              id="ws-connect-btn"
            >
              <Zap className="w-4 h-4" />
              Connect
            </button>
          )}
        </div>
        {connectionStatus === 'error' && (
          <p className="text-sm text-slate-600 leading-relaxed">
            Could not reach {wsUrl}. Start <code className="text-sky-800">python server/server.py</code> or enable the simulator below.
          </p>
        )}
      </div>

      <div className="bg-slate-50 p-4 rounded-lg border ips-border">
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-sky-100 text-sky-800">
              <Compass className="w-5 h-5" />
            </div>
            <div>
              <h4 className="ips-subheading">Demo simulator</h4>
              <p className="ips-muted text-sm">Mock target movement (no hardware)</p>
            </div>
          </div>
          <button
            onClick={() => {
              if (connectionStatus === 'connected') disconnectFromWebSocket();
              setSimulatorConfig((prev) => ({ ...prev, enabled: !prev.enabled }));
            }}
            className={`px-3 py-1.5 text-sm font-bold rounded-lg border ${
              simulatorConfig.enabled
                ? 'bg-sky-100 text-sky-900 border-sky-400'
                : 'bg-white text-slate-600 border-slate-300 hover:border-sky-400'
            }`}
            id="toggle-simulator-btn"
          >
            {simulatorConfig.enabled ? 'On' : 'Off'}
          </button>
        </div>

        {simulatorConfig.enabled && (
          <div className="flex flex-col gap-4 mt-3 pt-3 border-t ips-border">
            <div className="grid grid-cols-2 gap-2">
              {(['circle', 'infinity', 'random_walk', 'manual'] as const).map((pat) => (
                <button
                  key={pat}
                  type="button"
                  onClick={() => setSimulatorConfig((prev) => ({ ...prev, pattern: pat }))}
                  className={`px-2 py-2 rounded-lg text-sm font-semibold border ${
                    simulatorConfig.pattern === pat
                      ? 'bg-sky-100 border-sky-400 text-sky-900'
                      : 'bg-white border-slate-300 text-slate-600'
                  }`}
                  id={`pattern-${pat}-btn`}
                >
                  {pat === 'circle' && 'Circle'}
                  {pat === 'infinity' && 'Infinity'}
                  {pat === 'random_walk' && 'Random walk'}
                  {pat === 'manual' && 'Drag pin'}
                </button>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="ips-label text-xs">Speed {simulatorConfig.speed.toFixed(1)}×</label>
                <input
                  type="range"
                  min="0.2"
                  max="4.0"
                  step="0.2"
                  value={simulatorConfig.speed}
                  onChange={(e) => setSimulatorConfig((prev) => ({ ...prev, speed: Number(e.target.value) }))}
                  disabled={simulatorConfig.pattern === 'manual'}
                  className="w-full accent-sky-700"
                  id="simulator-speed-slider"
                />
              </div>
              <div>
                <label className="ips-label text-xs">Noise {simulatorConfig.noise.toFixed(2)} ft</label>
                <input
                  type="range"
                  min="0"
                  max="0.8"
                  step="0.05"
                  value={simulatorConfig.noise}
                  onChange={(e) => setSimulatorConfig((prev) => ({ ...prev, noise: Number(e.target.value) }))}
                  className="w-full accent-sky-700"
                  id="simulator-noise-slider"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <button
          onClick={() => setShowConfig(!showConfig)}
          className="text-base text-slate-700 hover:text-slate-900 flex items-center justify-between p-1 font-semibold"
          id="toggle-advanced-btn"
        >
          <span className="flex items-center gap-2">
            <Sliders className="w-4 h-4" />
            Grid settings
          </span>
          <span>{showConfig ? '−' : '+'}</span>
        </button>

        {showConfig && (
          <div className="flex flex-col gap-3 p-4 bg-slate-50 rounded-lg border ips-border">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="ips-label text-xs">Width</label>
                <select
                  value={settings.roomWidth}
                  onChange={(e) => setSettings((prev) => ({ ...prev, roomWidth: Number(e.target.value) }))}
                  className="w-full bg-white px-2 py-2 text-base rounded-lg border ips-border text-slate-900"
                  id="room-width-select"
                >
                  <option value={4}>4 ft (platform)</option>
                  <option value={5}>5 ft</option>
                  <option value={6}>6 ft</option>
                  <option value={8}>8 ft</option>
                </select>
              </div>
              <div>
                <label className="ips-label text-xs">Height</label>
                <select
                  value={settings.roomHeight}
                  onChange={(e) => setSettings((prev) => ({ ...prev, roomHeight: Number(e.target.value) }))}
                  className="w-full bg-white px-2 py-2 text-base rounded-lg border ips-border text-slate-900"
                  id="room-height-select"
                >
                  <option value={4}>4 ft (platform)</option>
                  <option value={5}>5 ft</option>
                  <option value={6}>6 ft</option>
                  <option value={8}>8 ft</option>
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="ips-label text-xs">Trail points</label>
                <input
                  type="number"
                  min="5"
                  max="80"
                  value={settings.maxTrailPoints}
                  onChange={(e) =>
                    setSettings((prev) => ({
                      ...prev,
                      maxTrailPoints: Math.min(80, Math.max(5, Number(e.target.value))),
                    }))
                  }
                  className="w-full bg-white px-2 py-2 text-base rounded-lg border ips-border"
                  id="trail-points-input"
                />
              </div>
              <div className="flex flex-col justify-end">
                <button
                  type="button"
                  onClick={onClearTrail}
                  className="px-3 py-2 bg-white border ips-border text-slate-700 hover:text-rose-700 rounded-lg text-sm font-bold flex items-center justify-center gap-2"
                  id="clear-trail-btn"
                >
                  <Trash2 className="w-4 h-4" />
                  Clear trail
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
