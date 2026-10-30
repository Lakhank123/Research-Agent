import React from 'react';
import { Compass, Database, ShieldCheck, Activity } from 'lucide-react';

interface HeaderProps {
  systemHealth: any;
  onNewSearch: () => void;
}

export const Header: React.FC<HeaderProps> = ({ systemHealth, onNewSearch }) => {
  const isOnline = systemHealth?.status === 'online';
  const modelName = systemHealth?.active_model || 'openai/gpt-oss-120b';

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Brand */}
        <div
          onClick={onNewSearch}
          className="flex items-center gap-2.5 cursor-pointer group select-none"
        >
          <div className="w-9 h-9 rounded-xl bg-teal-700 text-white flex items-center justify-center shadow-md shadow-teal-700/20 group-hover:scale-105 transition-transform">
            <Compass className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-900 tracking-tight text-base leading-none">
                ResearchPilot AI
              </span>
              <span className="text-[10px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-teal-100 text-teal-800 leading-none">
                v3.0
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium leading-tight mt-0.5">
              The Research Integrity Engine
            </p>
          </div>
        </div>

        {/* System Health Indicators */}
        <div className="flex items-center gap-3 text-xs">
          {/* Active Model Pill */}
          <div className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-50 border border-slate-200 text-slate-700 font-mono text-[11px]">
            <Activity className="w-3.5 h-3.5 text-teal-600" />
            <span>{modelName}</span>
          </div>

          {/* Operational Status Pill */}
          <div
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full font-semibold ${
              isOnline
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-rose-50 text-rose-700 border border-rose-200'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                isOnline ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'
              }`}
            />
            <span className="text-[11px]">
              {isOnline ? 'Pipeline Live' : 'Backend Offline'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};

