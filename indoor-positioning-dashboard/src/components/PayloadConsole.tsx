import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Trash2, Pause, Play, Copy, Check, Search, ShieldAlert } from 'lucide-react';
import { IPSPayload } from '../types';
import { formatTime } from '../utils/distance';

interface PayloadConsoleProps {
  logs: IPSPayload[];
  clearLogs: () => void;
}

export default function PayloadConsole({ logs, clearLogs }: PayloadConsoleProps) {
  const [isPaused, setIsPaused] = useState(false);
  const [filterQuery, setFilterQuery] = useState('');
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const [frozenLogs, setFrozenLogs] = useState<IPSPayload[]>([]);

  useEffect(() => {
    if (!isPaused) setFrozenLogs(logs);
  }, [logs, isPaused]);

  useEffect(() => {
    if (!isPaused && scrollContainerRef.current) {
      scrollContainerRef.current.scrollTop = scrollContainerRef.current.scrollHeight;
    }
  }, [frozenLogs, isPaused]);

  const filteredLogs = frozenLogs.filter((log) => {
    const jsonStr = JSON.stringify({
      target_id: log.target_id,
      x: log.x,
      y: log.y,
      distances: log.distances,
    });
    return jsonStr.toLowerCase().includes(filterQuery.toLowerCase());
  });

  const handleCopyJSON = (log: IPSPayload, index: number) => {
    const payloadOnly = {
      target_id: log.target_id,
      x: Number(log.x.toFixed(2)),
      y: Number(log.y.toFixed(2)),
      distances: Object.fromEntries(
        Object.entries(log.distances).map(([k, v]) => [k, Number((v as number).toFixed(2))])
      ),
    };
    navigator.clipboard.writeText(JSON.stringify(payloadOnly));
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 1500);
  };

  return (
    <div className="ips-card p-5 flex flex-col h-[360px] select-none text-slate-800" id="ips-console-card">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b ips-border mb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-sky-100 text-sky-800">
            <Terminal className="w-5 h-5" />
          </div>
          <div>
            <h3 className="ips-heading text-lg">Live data stream</h3>
            <p className="ips-muted text-sm">WebSocket JSON packets</p>
          </div>
        </div>
        <div className="flex items-center gap-2 bg-slate-100 p-1 rounded-lg border ips-border">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`px-3 py-1.5 rounded-md text-sm font-semibold flex items-center gap-1 ${
              isPaused ? 'bg-amber-100 text-amber-900 border border-amber-300' : 'text-slate-600'
            }`}
            id="pause-console-btn"
          >
            {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
            {isPaused ? 'Resume' : 'Pause'}
          </button>
          <button
            onClick={clearLogs}
            className="px-3 py-1.5 rounded-md text-sm font-semibold text-slate-600 hover:text-rose-700 flex items-center gap-1"
            id="clear-console-btn"
          >
            <Trash2 className="w-4 h-4" />
            Clear
          </button>
        </div>
      </div>

      <div className="relative mb-3 flex items-center">
        <Search className="absolute left-3 w-4 h-4 text-slate-500 pointer-events-none" />
        <input
          type="text"
          placeholder="Filter (e.g. Anchor_A)…"
          value={filterQuery}
          onChange={(e) => setFilterQuery(e.target.value)}
          className="w-full pl-10 pr-3 py-2 bg-white rounded-lg text-base border ips-border focus:outline-none focus:border-sky-600 text-slate-900"
          id="console-search-input"
        />
      </div>

      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-y-auto bg-slate-50 rounded-lg p-3 border ips-border text-sm leading-relaxed select-text font-mono"
      >
        {filteredLogs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 gap-2">
            <ShieldAlert className="w-6 h-6" />
            <span className="text-base font-semibold">
              {isPaused ? 'Stream paused' : 'Waiting for data…'}
            </span>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {filteredLogs.map((log, index) => {
              const strRepresentation = JSON.stringify({
                target_id: log.target_id,
                x: Number(log.x.toFixed(2)),
                y: Number(log.y.toFixed(2)),
                distances: Object.fromEntries(
                  Object.entries(log.distances).map(([k, v]) => [k, Number((v as number).toFixed(2))])
                ),
              });

              return (
                <div
                  key={log.timestamp + '-' + index}
                  className="group flex items-start gap-3 hover:bg-white p-2 rounded-lg"
                >
                  <span className="text-slate-500 text-xs font-semibold mt-1 whitespace-nowrap">
                    [{formatTime(log.timestamp)}]
                  </span>
                  <span className="text-slate-800 flex-1 break-all select-all text-sm">
                    {strRepresentation}
                  </span>
                  <button
                    onClick={() => handleCopyJSON(log, index)}
                    className="opacity-0 group-hover:opacity-100 p-1 bg-white border ips-border rounded hover:text-sky-700 text-slate-500"
                    title="Copy"
                  >
                    {copiedIndex === index ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="flex justify-between items-center mt-2 text-sm text-slate-600 font-semibold">
        <span>{filteredLogs.length} packets</span>
        {isPaused && <span className="text-amber-700">Paused</span>}
      </div>
    </div>
  );
}
