import React, { useState } from 'react';
import { ResearchCoverageMatrix } from '../types';
import { investigateGaps } from '../api';
import { Search, AlertCircle, CheckCircle2, Clock, Sparkles, Loader2, ExternalLink } from 'lucide-react';

interface ResearchGapViewProps {
  runId: string;
  coverageMatrix?: ResearchCoverageMatrix;
}

export const ResearchGapView: React.FC<ResearchGapViewProps> = ({
  runId,
  coverageMatrix,
}) => {
  const [investigating, setInvestigating] = useState(false);
  const [discoveredEvidence, setDiscoveredEvidence] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  if (!coverageMatrix) return null;

  const gapQueries = coverageMatrix.gap_items
    .filter((g) => g.evidence_status !== 'complete' && g.recommended_next_query)
    .map((g) => g.recommended_next_query);

  const handleInvestigateGaps = async () => {
    if (!gapQueries.length) return;
    setInvestigating(true);
    setError(null);
    try {
      const res = await investigateGaps(runId, gapQueries);
      setDiscoveredEvidence(res.discovered_evidence || []);
    } catch (err: any) {
      setError(err.message || 'Gap investigation failed');
    } finally {
      setInvestigating(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div>
          <h3 className="text-base font-bold text-slate-900">Research Coverage & Gap Analyzer</h3>
          <p className="text-xs text-slate-500">
            Audit of subtasks, single-source dependencies, metric omissions, and evidence recency
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-500">Coverage Score:</span>
          <span className="text-sm font-bold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-md border border-teal-200">
            {coverageMatrix.coverage_percentage}%
          </span>
        </div>
      </div>

      {/* Coverage Matrix Table */}
      <div className="divide-y divide-slate-100 border border-slate-200 rounded-xl overflow-hidden">
        {coverageMatrix.gap_items.map((item, idx) => {
          const isComplete = item.evidence_status === 'complete';
          const isPartial = item.evidence_status === 'partial';

          return (
            <div key={idx} className="p-4 space-y-2 hover:bg-slate-50/50 transition-colors">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {isComplete ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  ) : isPartial ? (
                    <AlertCircle className="w-4 h-4 text-amber-500 shrink-0" />
                  ) : (
                    <Clock className="w-4 h-4 text-rose-500 shrink-0" />
                  )}
                  <h4 className="text-sm font-bold text-slate-900">{item.requirement}</h4>
                </div>
                <span
                  className={`text-[11px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                    isComplete
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : isPartial
                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                      : 'bg-rose-50 text-rose-700 border border-rose-200'
                  }`}
                >
                  {item.evidence_status}
                </span>
              </div>

              {item.missing_information && (
                <p className="text-xs text-slate-600 pl-6 leading-relaxed">
                  <span className="font-semibold text-slate-700">Identified Gap: </span>
                  {item.missing_information}
                </p>
              )}

              {item.recommended_next_query && (
                <div className="pl-6 pt-1 flex items-center gap-2 text-xs text-teal-800">
                  <span className="font-semibold text-slate-400">Targeted Query:</span>
                  <span className="font-mono bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                    {item.recommended_next_query}
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Action to Investigate Gaps */}
      {gapQueries.length > 0 && (
        <div className="p-4 bg-teal-50/50 rounded-xl border border-teal-200 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="space-y-1 text-center sm:text-left">
            <h4 className="text-sm font-bold text-teal-900 flex items-center justify-center sm:justify-start gap-1.5">
              <Sparkles className="w-4 h-4 text-teal-600" />
              Automated Follow-Up Investigation
            </h4>
            <p className="text-xs text-teal-700">
              Dispatch {gapQueries.length} targeted search queries to resolve missing metrics and independent verification gaps.
            </p>
          </div>

          <button
            onClick={handleInvestigateGaps}
            disabled={investigating}
            className="px-5 py-2.5 rounded-lg bg-teal-700 hover:bg-teal-800 disabled:bg-slate-300 text-white text-xs font-bold shadow-sm transition-all inline-flex items-center gap-2 shrink-0"
          >
            {investigating ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                <span>Investigating Gaps...</span>
              </>
            ) : (
              <>
                <Search className="w-3.5 h-3.5" />
                <span>Investigate Research Gaps</span>
              </>
            )}
          </button>
        </div>
      )}

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-xs text-rose-700 rounded-lg">
          {error}
        </div>
      )}

      {/* Discovered Follow-Up Evidence */}
      {discoveredEvidence.length > 0 && (
        <div className="space-y-3 pt-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500">
            Discovered Follow-Up Evidence ({discoveredEvidence.length} Chunks)
          </h4>
          <div className="space-y-2">
            {discoveredEvidence.map((ev, eIdx) => (
              <div key={eIdx} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs space-y-1">
                <a
                  href={ev.url}
                  target="_blank"
                  rel="noreferrer"
                  className="font-bold text-teal-800 hover:underline flex items-center gap-1"
                >
                  {ev.title || ev.url} <ExternalLink className="w-3 h-3 opacity-60" />
                </a>
                <p className="text-slate-700 italic">"{ev.snippet}"</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

