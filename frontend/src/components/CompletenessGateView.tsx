import React from 'react';
import { CompletenessEvaluation, ResearchContract } from '../types';
import { CheckCircle2, AlertTriangle, Layers, Target, ArrowRight } from 'lucide-react';

interface CompletenessGateViewProps {
  completeness?: CompletenessEvaluation;
  contract?: ResearchContract;
}

export const CompletenessGateView: React.FC<CompletenessGateViewProps> = ({
  completeness,
  contract,
}) => {
  if (!completeness) return null;

  const isComplete = completeness.is_complete;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-9 h-9 rounded-lg flex items-center justify-center ${
              isComplete ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
            }`}
          >
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900">Research Completeness Gate</h3>
            <p className="text-xs text-slate-500">
              Audit of verified entities and required attributes against research contract
            </p>
          </div>
        </div>

        <span
          className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider inline-flex items-center gap-1.5 ${
            isComplete
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              : 'bg-amber-50 text-amber-700 border border-amber-200'
          }`}
        >
          {isComplete ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
          {isComplete ? '100% Contract Satisfied' : 'Partially Completed'}
        </span>
      </div>

      {/* Progress & Target Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Contract Target</span>
          <p className="text-2xl font-bold text-slate-900">
            {completeness.target_count ? `${completeness.target_count} Entities` : 'Unbounded'}
          </p>
          <span className="text-xs text-slate-500">{contract?.geography || 'Global'} • {contract?.industry || 'Domain'}</span>
        </div>

        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
          <span className="text-xs font-bold text-emerald-700 uppercase tracking-wider">Verified Discovered</span>
          <p className="text-2xl font-bold text-emerald-800">{completeness.verified_count} Entities</p>
          <span className="text-xs text-slate-500">Backed by independent citations</span>
        </div>

        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
          <span className="text-xs font-bold text-amber-700 uppercase tracking-wider">Missing Evidence</span>
          <p className="text-2xl font-bold text-amber-800">{completeness.missing_count} Gaps</p>
          <span className="text-xs text-slate-500">Unconfirmed without citations</span>
        </div>
      </div>

      {/* Explanation Banner */}
      <div
        className={`p-4 rounded-xl text-xs leading-relaxed border ${
          isComplete ? 'bg-emerald-50/60 border-emerald-200 text-emerald-900' : 'bg-amber-50/60 border-amber-200 text-amber-900'
        }`}
      >
        <span className="font-bold block mb-1">Gate Audit Finding:</span>
        {completeness.gap_explanation}
      </div>

      {/* Verified vs Missing Entity Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Verified */}
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Verified & Grounded Entities ({completeness.verified_entities.length})
          </h4>
          <div className="flex flex-wrap gap-2">
            {completeness.verified_entities.length > 0 ? (
              completeness.verified_entities.map((ent, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold"
                >
                  ✓ {ent}
                </span>
              ))
            ) : (
              <span className="text-xs text-slate-400">No specific entity names tagged.</span>
            )}
          </div>
        </div>

        {/* Missing Entities */}
        {completeness.missing_entities.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
              Unfulfilled Requested Slots ({completeness.missing_entities.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {completeness.missing_entities.map((m, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 text-xs font-semibold"
                >
                  ⚠ {m}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Recommended Remedy */}
      {completeness.recommended_remedy.length > 0 && (
        <div className="pt-3 border-t border-slate-100 space-y-1.5">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Recommended Action to Complete Contract:
          </span>
          <ul className="list-disc list-inside text-xs text-slate-600 space-y-1">
            {completeness.recommended_remedy.map((rem, rIdx) => (
              <li key={rIdx}>{rem}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

