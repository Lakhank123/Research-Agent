import React, { useState } from 'react';
import { Finding, ChallengeResult } from '../types';
import { challengeFinding } from '../api';
import {
  X,
  Swords,
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  XCircle,
  Loader2,
  ExternalLink,
  Scale,
  CheckCircle2
} from 'lucide-react';

interface ChallengeModalProps {
  runId: string;
  finding: Finding;
  onClose: () => void;
  onSaveChallengeResult: (result: ChallengeResult) => void;
  existingResult?: ChallengeResult;
}

export const ChallengeModal: React.FC<ChallengeModalProps> = ({
  runId,
  finding,
  onClose,
  onSaveChallengeResult,
  existingResult,
}) => {
  const [result, setResult] = useState<ChallengeResult | null>(existingResult || null);
  const [isChallenging, setIsChallenging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunChallenge = async () => {
    setIsChallenging(true);
    setError(null);

    const excerpts = (finding.verified_evidence_excerpts || []).map((e) => e.excerpt);
    const urls = (finding.verified_evidence_excerpts || []).map((e) => e.url);

    try {
      const res = await challengeFinding(
        runId,
        finding.finding_id,
        finding.finding,
        excerpts,
        urls
      );
      setResult(res);
      onSaveChallengeResult(res);
    } catch (err: any) {
      setError(err.message || 'Counter-research operation failed.');
    } finally {
      setIsChallenging(false);
    }
  };

  const getOutcomeBadge = (outcome: string) => {
    if (outcome.includes('remains supported')) {
      return {
        label: 'Claim Remains Supported',
        color: 'bg-emerald-50 text-emerald-800 border-emerald-300',
        icon: ShieldCheck,
      };
    }
    if (outcome.includes('needs qualification')) {
      return {
        label: 'Claim Needs Qualification',
        color: 'bg-amber-50 text-amber-800 border-amber-300',
        icon: AlertTriangle,
      };
    }
    if (outcome.includes('Conflicting evidence')) {
      return {
        label: 'Conflicting Evidence Discovered',
        color: 'bg-rose-50 text-rose-800 border-rose-300',
        icon: XCircle,
      };
    }
    return {
      label: outcome,
      color: 'bg-slate-100 text-slate-800 border-slate-300',
      icon: HelpCircle,
    };
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl max-w-3xl w-full border border-slate-200 shadow-2xl max-h-[90vh] flex flex-col overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-slate-900 text-amber-400 flex items-center justify-center">
              <Swords className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Adversarial Counter-Research Auditor</h2>
              <p className="text-xs text-slate-500">Actively hunt for contradictory evidence, criticisms, or opposing data</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-lg hover:bg-slate-200 flex items-center justify-center text-slate-500 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-6">
          {/* Original Finding Summary */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Audited Finding:</span>
            <p className="text-sm font-bold text-slate-900 leading-snug">"{finding.finding}"</p>
            <p className="text-xs text-slate-600">{finding.explanation}</p>
          </div>

          {/* Action Prompt before run */}
          {!result && !isChallenging && (
            <div className="text-center py-6 space-y-4">
              <Scale className="w-12 h-12 text-teal-600 mx-auto" />
              <div className="max-w-md mx-auto space-y-1">
                <h3 className="text-base font-bold text-slate-900">Ready to Challenge this Assertion?</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  ResearchPilot will formulate independent adversarial search queries, search for opposing viewpoints, regulatory actions, and technical criticisms, and evaluate source independence.
                </p>
              </div>

              {error && (
                <div className="text-xs text-rose-600 bg-rose-50 border border-rose-200 rounded-lg p-3">
                  {error}
                </div>
              )}

              <button
                onClick={handleRunChallenge}
                className="px-6 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold shadow-md hover:shadow-lg transition-all inline-flex items-center gap-2"
              >
                <Swords className="w-4 h-4 text-amber-400" />
                <span>Execute Counter-Research</span>
              </button>
            </div>
          )}

          {/* In-Progress State */}
          {isChallenging && (
            <div className="py-12 text-center space-y-4">
              <Loader2 className="w-8 h-8 text-teal-600 animate-spin mx-auto" />
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-slate-800">Dispatching Counter-Research Queries...</h3>
                <p className="text-xs text-slate-500">Searching independent publications, critiques, and alternative benchmarks</p>
              </div>
            </div>
          )}

          {/* Challenge Result View */}
          {result && (
            <div className="space-y-6">
              {/* Outcome Banner */}
              {(() => {
                const badge = getOutcomeBadge(result.outcome);
                const BadgeIcon = badge.icon;
                return (
                  <div className={`p-4 rounded-xl border ${badge.color} space-y-1`}>
                    <div className="flex items-center gap-2">
                      <BadgeIcon className="w-5 h-5 shrink-0" />
                      <h3 className="text-sm font-bold">{badge.label}</h3>
                    </div>
                    <p className="text-xs leading-relaxed">{result.explanation}</p>
                  </div>
                );
              })()}

              {/* Counter Queries Executed */}
              <div className="space-y-1.5">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Adversarial Queries Executed:
                </span>
                <div className="flex flex-wrap gap-2">
                  {result.counter_queries_executed.map((q, qIdx) => (
                    <span
                      key={qIdx}
                      className="text-xs font-mono px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200"
                    >
                      {q}
                    </span>
                  ))}
                </div>
              </div>

              {/* Side-by-side Evidence Comparison */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Supporting evidence */}
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                  <h4 className="text-xs font-bold text-teal-800 uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Original Supporting Evidence
                  </h4>
                  {result.supporting_evidence.length > 0 ? (
                    result.supporting_evidence.map((s, idx) => (
                      <p key={idx} className="text-xs text-slate-700 italic border-l-2 border-teal-400 pl-2">
                        "{s.text}"
                      </p>
                    ))
                  ) : (
                    <p className="text-xs text-slate-400">No original excerpts provided.</p>
                  )}
                </div>

                {/* Counter evidence */}
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-2">
                  <h4 className="text-xs font-bold text-amber-800 uppercase tracking-wider flex items-center gap-1.5">
                    <Scale className="w-3.5 h-3.5" />
                    Discovered Counter-Evidence
                  </h4>
                  {result.counter_evidence.length > 0 ? (
                    result.counter_evidence.map((c, idx) => (
                      <div key={idx} className="text-xs space-y-1 border-l-2 border-amber-400 pl-2">
                        <a
                          href={c.url}
                          target="_blank"
                          rel="noreferrer"
                          className="font-semibold text-slate-900 hover:text-teal-700 flex items-center gap-1"
                        >
                          {c.title || c.domain} <ExternalLink className="w-2.5 h-2.5" />
                        </a>
                        <p className="text-slate-700 italic">"{c.snippet}"</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-500">
                      No material counter-evidence was found in the sources investigated.
                    </p>
                  )}
                </div>
              </div>

              {/* Points of Divergence */}
              {result.source_disagreements && result.source_disagreements.length > 0 && (
                <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-900 space-y-1">
                  <span className="font-bold block">Identified Source Disagreements:</span>
                  <ul className="list-disc list-inside space-y-0.5">
                    {result.source_disagreements.map((dis, dIdx) => (
                      <li key={dIdx}>{dis}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex items-center justify-between">
          <span className="text-[11px] text-slate-400">
            Audit results are persisted in local research history.
          </span>
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-200 hover:bg-slate-300 text-slate-800 text-xs font-semibold transition-colors"
          >
            Close Audit Drawer
          </button>
        </div>
      </div>
    </div>
  );
};

