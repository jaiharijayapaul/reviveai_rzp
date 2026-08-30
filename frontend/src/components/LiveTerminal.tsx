import React, { useEffect, useState, useRef } from 'react';
import { Terminal } from 'lucide-react';

interface LogEvent {
  id: string;
  timestamp: string;
  level: string;
  system: string;
  message: string;
}

export default function LiveTerminal() {
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // We poll the backend for SSE stream
    const eventSource = new EventSource('http://localhost:8000/api/stream/logs');

    eventSource.onmessage = (event) => {
      const newLog = JSON.parse(event.data);
      setLogs((prev) => {
        // Prevent duplicates if SSE restarts
        if (prev.find(l => l.id === newLog.id)) return prev;
        return [...prev, newLog];
      });
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
      // Retry logic could be added here, but SSE usually auto-reconnects
    };

    return () => {
      eventSource.close();
    };
  }, []);

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const getLogColor = (level: string) => {
    switch (level) {
      case 'INFO': return 'text-blue-400';
      case 'WARN': return 'text-yellow-400';
      case 'ERROR': return 'text-red-400';
      case 'SUCCESS': return 'text-emerald-400';
      default: return 'text-gray-300';
    }
  };

  const getSystemColor = (system: string) => {
    switch (system) {
      case 'RAZORPAY': return 'text-purple-400';
      case 'REVIVE-AI': return 'text-emerald-400';
      case 'POLICY': return 'text-blue-400';
      case 'SYSTEM': return 'text-gray-400';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className="bg-black border border-gray-800 rounded-lg overflow-hidden flex flex-col h-full font-mono text-[11px] sm:text-xs">
      <div className="bg-gray-900 border-b border-gray-800 px-4 py-2 flex items-center gap-2">
        <Terminal className="h-4 w-4 text-emerald-500" />
        <span className="text-gray-300 font-semibold tracking-wider">LIVE_WEBHOOK_STREAM</span>
        <div className="ml-auto flex gap-1.5">
          <div className="h-2.5 w-2.5 rounded-full bg-red-500"></div>
          <div className="h-2.5 w-2.5 rounded-full bg-yellow-500"></div>
          <div className="h-2.5 w-2.5 rounded-full bg-green-500"></div>
        </div>
      </div>
      
      <div className="p-4 overflow-y-auto flex-1 max-h-[400px] space-y-1">
        {logs.length === 0 ? (
          <div className="text-gray-600 italic">Waiting for incoming webhooks...</div>
        ) : (
          logs.map((log) => (
            <div key={log.id} className="flex gap-2">
              <span className="text-gray-500 shrink-0">
                [{new Date(log.timestamp).toLocaleTimeString()}]
              </span>
              <span className={`shrink-0 ${getLogColor(log.level)}`}>
                [{log.level}]
              </span>
              <span className={`shrink-0 ${getSystemColor(log.system)}`}>
                [{log.system}]
              </span>
              <span className="text-gray-300 break-words">
                {log.message}
              </span>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
