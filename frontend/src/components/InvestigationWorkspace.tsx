import React from 'react';
import { CheckCircle2, Clock, Loader2, AlertCircle, FileSearch, Globe, Database, Cpu, ShieldCheck } from 'lucide-react';

interface InvestigationWorkspaceProps {
  question: string;
  depth: string;
  events: Array<{ stage: string; status: string; detail: string; timestamp?: string }>;
  currentStage: string;
}

export const InvestigationWorkspace: React.FC<InvestigationWorkspaceProps> = ({
  question,
  depth,
  events,
  currentStage,
}) => {
  const pipelineStages = [
    { key: 'planning', label: '1. Understanding & Contract Planning', icon: FileSearch },
    { key: 'web_search', label: '2. Multi-Query Web Discovery', icon: Globe },
    { key: 'extracting', label: '3. Full Page Extraction & Boilerplate Strip', icon: Database },
    { key: 'evaluating_evidence', label: '4. Okapi BM25 Ranking & Ledger Assembly', icon: Cpu },
    { key: 'generating_report', label: '5. Grounded Synthesis & Claim Verification', icon: ShieldCheck },
  ];

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 space-y-8">
      {/* Current Run Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2.5 py-1 rounded-md">
            Active Research Investigation
          </span>
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider capitalize">
            {depth} Execution Mode
          </span>
        </div>
        <h2 className="text-xl font-bold text-slate-900 leading-snug">
          "{question}"
        </h2>
      </div>

      {/* Live Stage Timeline */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">
          Autonomous Execution Stages
        </h3>

        <div className="space-y-3">
          {pipelineStages.map((stage, idx) => {
            const Icon = stage.icon;
            
            // Check state
            const hasStarted = events.some((e) => e.stage === stage.key);
            const isCompleted = events.some(
              (e) => e.stage === stage.key && (e.status === 'completed' || e.status === 'partial')
            );
            const isRunning = events.some(
              (e) => e.stage === stage.key && e.status === 'running'
            ) && !isCompleted;
            const isFailed = events.some(
              (e) => e.stage === stage.key && e.status === 'failed'
            );

            // Latest detail for this stage
            const stageEvents = events.filter((e) => e.stage === stage.key);
            const latestDetail = stageEvents.length > 0 ? stageEvents[stageEvents.length - 1].detail : '';

            return (
              <div
                key={stage.key}
                className={`p-4 rounded-xl border transition-all flex items-start justify-between gap-4 ${
                  isRunning
                    ? 'bg-teal-50/60 border-teal-500 shadow-sm'
                    : isCompleted
                    ? 'bg-white border-slate-200'
                    : isFailed
                    ? 'bg-rose-50 border-rose-300'
                    : 'bg-slate-50/50 border-slate-200 opacity-60'
                }`}
              >
                <div className="flex items-start gap-3.5">
                  <div
                    className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                      isRunning
                        ? 'bg-teal-600 text-white animate-pulse'
                        : isCompleted
                        ? 'bg-teal-100 text-teal-800'
                        : isFailed
                        ? 'bg-rose-200 text-rose-800'
                        : 'bg-slate-200 text-slate-500'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{stage.label}</h4>
                    <p className="text-xs text-slate-600 mt-1">
                      {latestDetail || (isRunning ? 'Executing stage operations...' : 'Pending execution...')}
                    </p>
                  </div>
                </div>

                <div className="shrink-0 text-right">
                  {isRunning && (
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 bg-white px-2.5 py-1 rounded-full border border-teal-200">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      In Progress
                    </span>
                  )}
                  {isCompleted && (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Completed
                    </span>
                  )}
                  {isFailed && (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-rose-700 bg-rose-100 px-2.5 py-1 rounded-full">
                      <AlertCircle className="w-3.5 h-3.5" />
                      Issue Handled
                    </span>
                  )}
                  {!hasStarted && (
                    <span className="text-xs font-medium text-slate-400">Waiting</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Live Stream Terminal Box */}
      <div className="bg-slate-900 rounded-xl p-5 font-mono text-xs text-slate-300 space-y-2 border border-slate-800 shadow-inner max-h-56 overflow-y-auto">
        <div className="text-slate-500 uppercase tracking-wider text-[10px] font-bold pb-1 border-b border-slate-800 flex items-center justify-between">
          <span>Live Server Pipeline Events (SSE)</span>
          <span className="flex items-center gap-1.5 text-teal-400">
            <span className="w-2 h-2 rounded-full bg-teal-400 animate-ping" />
            Connected
          </span>
        </div>
        {events.map((e, idx) => (
          <div key={idx} className="leading-relaxed flex gap-2">
            <span className="text-slate-500">[{e.stage}]</span>
            <span className={e.status === 'failed' ? 'text-rose-400' : e.status === 'completed' ? 'text-teal-400' : 'text-slate-200'}>
              {e.detail}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

