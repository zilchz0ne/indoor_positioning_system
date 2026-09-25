import React, { useState, useEffect, useRef } from 'react';
import {
  ChevronDown, ChevronUp, Info, Radio, Waves
} from 'lucide-react';
import {
  IPSPayload, Anchor, PathPoint, ConnectionStatus,
  SimulatorConfig, DashboardSettings
} from './types';
import ArenaCanvas from './components/ArenaCanvas';
import StatsPanel from './components/StatsPanel';
import PayloadConsole from './components/PayloadConsole';
import ControlPanel from './components/ControlPanel';
import { getDistance, generateGaussianNoise } from './utils/distance';
import { DEFAULT_ANCHORS, mapServerAnchors, PLATFORM_FT } from './utils/anchors';

export default function App() {
  const [wsUrl, setWsUrl] = useState('ws://localhost:8765');
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [currentPayload, setCurrentPayload] = useState<IPSPayload | null>(null);
  const [previousPayload, setPreviousPayload] = useState<IPSPayload | null>(null);
  const [hasLiveData, setHasLiveData] = useState(false);

  const [logs, setLogs] = useState<IPSPayload[]>([]);
  const [trail, setTrail] = useState<PathPoint[]>([]);
  const [isIntroOpen, setIsIntroOpen] = useState(true);

  const [settings, setSettings] = useState<DashboardSettings>({
    showRings: true,
    showTrail: true,
    maxTrailPoints: 40,
    roomWidth: PLATFORM_FT,
    roomHeight: PLATFORM_FT,
    gridResolution: 1.0,
    unit: 'ft',
    roomLabel: '4 ft × 4 ft (48 in)',
  });

  // Simulator off by default — real target UDP data drives the dashboard
  const [simulatorConfig, setSimulatorConfig] = useState<SimulatorConfig>({
    enabled: false,
    pattern: 'circle',
    speed: 1.5,
    noise: 0.15,
  });

  const [anchors, setAnchors] = useState<Anchor[]>(DEFAULT_ANCHORS);
  const anchorsRef = useRef(anchors);
  anchorsRef.current = anchors;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const angleRef = useRef(0);
  const lastStepAngleRef = useRef(Math.random() * Math.PI * 2);

  const handleIncomingPayload = (payload: IPSPayload) => {
    setPreviousPayload(currentPayload);
    setCurrentPayload(payload);

    setLogs((prev) => [...prev, payload].slice(-100));

    setTrail((prev) => {
      const newElem: PathPoint = {
        x: payload.x,
        y: payload.y,
        timestamp: payload.timestamp,
        id: Math.random().toString(36).substring(2, 11),
      };
      return [...prev, newElem].slice(-settings.maxTrailPoints);
    });
  };

  const connectToWebSocket = () => {
    if (wsRef.current) wsRef.current.close();
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current);

    setConnectionStatus('connecting');

    try {
      const socket = new WebSocket(wsUrl);
      wsRef.current = socket;

      socket.onopen = () => {
        setConnectionStatus('connected');
      };

      socket.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);

          if (parsed.type === 'config' && Array.isArray(parsed.anchors)) {
            setAnchors(mapServerAnchors(parsed.anchors));
            if (parsed.room?.width && parsed.room?.height) {
              setSettings((prev) => ({
                ...prev,
                roomWidth: Math.max(parsed.room.width, 1),
                roomHeight: Math.max(parsed.room.height, 1),
                unit: parsed.room.unit ?? 'ft',
                roomLabel: parsed.room.label ?? `${parsed.room.width} × ${parsed.room.height} ft`,
              }));
            }
            return;
          }

          if (parsed && typeof parsed.x === 'number' && typeof parsed.y === 'number') {
            setHasLiveData(true);
            // Real data arrived — keep simulator off
            setSimulatorConfig((prev) => (prev.enabled ? { ...prev, enabled: false } : prev));

            handleIncomingPayload({
              target_id: parsed.target_id || 'T1',
              x: parsed.x,
              y: parsed.y,
              distances: parsed.distances || {},
              rssi: parsed.rssi,
              timestamp: Date.now(),
            });
          }
        } catch {
          console.warn('Ignored malformed WebSocket frame');
        }
      };

      socket.onerror = () => setConnectionStatus('error');

      socket.onclose = () => {
        setConnectionStatus('disconnected');
        reconnectTimer.current = setTimeout(connectToWebSocket, 3000);
      };
    } catch {
      setConnectionStatus('error');
    }
  };

  const disconnectFromWebSocket = () => {
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    wsRef.current?.close();
    wsRef.current = null;
    setConnectionStatus('disconnected');
  };

  useEffect(() => {
    connectToWebSocket();
    return () => {
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, []);

  const triggerSimulatedPayload = (x: number, y: number) => {
    const namedDistances: Record<string, number> = {};
    for (const a of anchorsRef.current) {
      const serverName = `Anchor_${a.name.replace(/^ANCHOR_/, '')}`;
      const dist = getDistance(x, y, a.x, a.y);
      const noise = generateGaussianNoise(0, simulatorConfig.noise);
      namedDistances[serverName] = Number(Math.max(0, dist + noise).toFixed(3));
    }

    handleIncomingPayload({
      target_id: 'T1',
      x: Number(x.toFixed(3)),
      y: Number(y.toFixed(3)),
      distances: namedDistances,
      timestamp: Date.now(),
    });
  };

  const handleManualMove = (x: number, y: number) => {
    if (simulatorConfig.enabled && simulatorConfig.pattern === 'manual') {
      triggerSimulatedPayload(x, y);
    }
  };

  useEffect(() => {
    if (!simulatorConfig.enabled) return;

    const interval = setInterval(() => {
      let nextX = 2.5;
      let nextY = 2.5;
      const center_x = settings.roomWidth / 2;
      const center_y = settings.roomHeight / 2;

      if (simulatorConfig.pattern === 'circle') {
        angleRef.current += 0.035 * simulatorConfig.speed;
        const radius = Math.min(settings.roomWidth, settings.roomHeight) * 0.32;
        nextX = center_x + Math.cos(angleRef.current) * radius;
        nextY = center_y + Math.sin(angleRef.current) * radius;
      } else if (simulatorConfig.pattern === 'infinity') {
        angleRef.current += 0.025 * simulatorConfig.speed;
        const a = Math.min(settings.roomWidth, settings.roomHeight) * 0.38;
        const t = angleRef.current;
        const denom = 1 + Math.pow(Math.sin(t), 2);
        nextX = center_x + (a * Math.cos(t)) / denom;
        nextY = center_y + (a * Math.sin(t) * Math.cos(t)) / denom;
      } else if (simulatorConfig.pattern === 'random_walk') {
        const prevX = currentPayload ? currentPayload.x : center_x;
        const prevY = currentPayload ? currentPayload.y : center_y;
        if (Math.random() < 0.15) {
          lastStepAngleRef.current += (Math.random() - 0.5) * Math.PI * 0.6;
        }
        const stepLength = 0.09 * simulatorConfig.speed;
        const dx = Math.cos(lastStepAngleRef.current) * stepLength;
        const dy = Math.sin(lastStepAngleRef.current) * stepLength;
        let testX = prevX + dx;
        let testY = prevY + dy;
        const boundaryMargin = 0.2;
        if (testX < boundaryMargin || testX > settings.roomWidth - boundaryMargin) {
          lastStepAngleRef.current = Math.PI - lastStepAngleRef.current;
          testX = Math.max(boundaryMargin, Math.min(settings.roomWidth - boundaryMargin, prevX - dx));
        }
        if (testY < boundaryMargin || testY > settings.roomHeight - boundaryMargin) {
          lastStepAngleRef.current = -lastStepAngleRef.current;
          testY = Math.max(boundaryMargin, Math.min(settings.roomHeight - boundaryMargin, prevY - dy));
        }
        nextX = testX;
        nextY = testY;
      } else {
        return;
      }

      triggerSimulatedPayload(nextX, nextY);
    }, 100);

    return () => clearInterval(interval);
  }, [
    simulatorConfig.enabled,
    simulatorConfig.pattern,
    simulatorConfig.speed,
    simulatorConfig.noise,
    settings.roomWidth,
    settings.roomHeight,
  ]);

  const clearLogsAndTrail = () => {
    setLogs([]);
    setTrail([]);
    setCurrentPayload(null);
    setPreviousPayload(null);
  };

  return (
    <div className="min-h-screen ips-page flex flex-col" id="ips-root-layout">

      <header className="border-b ips-border bg-white sticky top-0 z-50 px-6 py-5 shadow-sm">
        <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-sky-700 rounded-lg flex items-center justify-center text-white font-bold">
              <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="2"/><path d="M12 2v4"/><path d="M12 18v4"/><path d="M4.93 4.93l2.83 2.83"/><path d="M16.24 16.24l2.83 2.83"/><path d="M2 12h4"/><path d="M18 12h4"/><path d="M4.93 19.07l2.83-2.83"/><path d="M16.24 7.76l2.83-2.83"/></svg>
            </div>
            <div className="flex flex-col">
              <h1 className="text-xl font-bold text-slate-900 tracking-wide">Indoor Positioning System</h1>
              <span className="text-base text-slate-600 font-semibold">4 ft × 4 ft platform — live tracking dashboard</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {simulatorConfig.enabled && (
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-emerald-50 border border-emerald-300 text-emerald-800 text-base font-semibold">
                <Waves className="w-5 h-5" />
                <span>Simulating: {simulatorConfig.pattern.toUpperCase()}</span>
              </div>
            )}
            {hasLiveData && !simulatorConfig.enabled && (
              <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-rose-50 border border-rose-300 text-rose-800 text-base font-semibold">
                <Radio className="w-5 h-5" />
                <span>LIVE TARGET DATA</span>
              </div>
            )}
          </div>
        </div>
      </header>

      <section className="px-6 py-4">
        <div className="max-w-[1600px] mx-auto">
          <div className="glass-panel rounded-lg p-5">
            <button onClick={() => setIsIntroOpen(!isIntroOpen)} className="w-full flex justify-between items-center text-left text-slate-800 hover:text-slate-900" id="toggle-intro-btn">
              <span className="flex items-center gap-2 ips-heading text-lg">
                <Info className="w-5 h-5 text-sky-700" />
                How positioning works
              </span>
              <span>{isIntroOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}</span>
            </button>
            {isIntroOpen && (
              <div className="mt-4 text-base text-slate-700 leading-relaxed grid md:grid-cols-12 gap-6">
                <div className="md:col-span-8 flex flex-col gap-3">
                  <p>Targets scan anchor BLE signals. The server converts RSSI to distance and calculates position on your <strong>4 ft × 4 ft</strong> board.</p>
                  <p>Circles on the map show measured distance from each corner anchor. The target dot sits where those circles intersect.</p>
                </div>
                <div className="md:col-span-4 bg-slate-50 p-4 rounded-lg border ips-border flex flex-col gap-2 text-base">
                  <div className="ips-label text-slate-800 pb-2 border-b ips-border">Corner anchors</div>
                  {anchors.map((a) => (
                    <div key={a.id} className="font-semibold text-slate-800">
                      <span style={{ color: a.color }}>{a.name}</span>: ({a.x.toFixed(1)} ft, {a.y.toFixed(1)} ft)
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      <main className="flex-1 px-6 py-6 max-w-[1600px] mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-8 flex flex-col gap-4 h-full min-h-[600px]">
          <ArenaCanvas
            currentPayload={currentPayload}
            anchors={anchors}
            trail={trail}
            settings={settings}
            setSettings={setSettings}
            onManualMove={handleManualMove}
            simulatorEnabled={simulatorConfig.enabled}
            simulatorPattern={simulatorConfig.pattern}
          />
        </div>

        <div className="lg:col-span-4 flex flex-col gap-6">
          <ControlPanel
            wsUrl={wsUrl}
            setWsUrl={setWsUrl}
            connectionStatus={connectionStatus}
            connectToWebSocket={connectToWebSocket}
            disconnectFromWebSocket={disconnectFromWebSocket}
            simulatorConfig={simulatorConfig}
            setSimulatorConfig={setSimulatorConfig}
            settings={settings}
            setSettings={setSettings}
            onClearTrail={() => setTrail([])}
          />
          <StatsPanel
            currentPayload={currentPayload}
            previousPayload={previousPayload}
            anchors={anchors}
            settings={settings}
            connectionStatus={connectionStatus}
          />
          <PayloadConsole logs={logs} clearLogs={clearLogsAndTrail} />
        </div>
      </main>

      <footer className="border-t ips-border mt-8 py-5 px-6 bg-white">
        <div className="max-w-[1600px] mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-base text-slate-600 font-semibold">
          <span>Indoor Positioning System Dashboard</span>
          <div className="flex flex-wrap gap-4">
            {anchors.map((a) => (
              <span key={a.id} className="flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: a.color }} />
                {a.name} ({a.x},{a.y} ft)
              </span>
            ))}
          </div>
        </div>
      </footer>
    </div>
  );
}
