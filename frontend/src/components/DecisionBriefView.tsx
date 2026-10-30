import React from 'react';
import { DecisionBrief } from '../types';
import {
  Briefcase,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  ShieldAlert,
  HelpCircle,
  Award
} from 'lucide-react';

interface DecisionBriefViewProps {
  decisionBrief?: DecisionBrief;
}

export const DecisionBriefView: React.FC<DecisionBriefViewProps> = ({ decisionBrief }) => {
  if (!decisionBrief) return null;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2.5 pb-4 border-b border-slate-100">
        <div className="w-9 h-9 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
          <Briefcase className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-bold text-slate-900">Executive Decision-Support Brief</h3>
          <p className="text-xs text-slate-500">
            Translating verified research evidence into strategic options, risks, and next steps
          </p>
        </div>
      </div>

      {/* Main Conclusion Hero Card */}
      <div className="bg-slate-900 text-white rounded-xl p-6 space-y-3 shadow-md">
        <span className="text-xs font-bold uppercase tracking-wider text-teal-400 flex items-center gap-1.5">
          <Award className="w-4 h-4" />
          Primary Strategic Takeaway
        </span>
        <h2 className="text-lg md:text-xl font-bold leading-snug">
          {decisionBrief.main_conclusion}
        </h2>
        {decisionBrief.next_practical_action && (
          <div className="pt-3 border-t border-slate-800 flex items-center gap-2 text-xs text-slate-300">
            <span className="font-semibold text-teal-300">Recommended Next Step:</span>
            <span>{decisionBrief.next_practical_action}</span>
          </div>
        )}
      </div>

      {/* Key Supporting Evidence Points */}
      {decisionBrief.key_evidence && decisionBrief.key_evidence.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Core Grounding Evidence Points
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {decisionBrief.key_evidence.map((ev, idx) => (
              <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs flex items-start gap-2">
                <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
                <span className="text-slate-700 leading-relaxed">{ev}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Available Options Comparison (if generated) */}
      {decisionBrief.available_options && decisionBrief.available_options.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
            Evaluated Alternatives & Tradeoffs
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {decisionBrief.available_options.map((opt, idx) => (
              <div key={idx} className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
                <h5 className="font-bold text-slate-900 text-sm">{opt.name}</h5>
                {opt.best_for && (
                  <span className="text-[11px] font-semibold text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-200 block">
                    Best for: {opt.best_for}
                  </span>
                )}
                <div className="space-y-1.5 text-xs">
                  <span className="font-semibold text-emerald-700 block">Advantages:</span>
                  <ul className="list-disc list-inside text-slate-600 space-y-0.5">
                    {opt.pros.map((p, pIdx) => (
                      <li key={pIdx}>{p}</li>
                    ))}
                  </ul>
                </div>
                <div className="space-y-1.5 text-xs">
                  <span className="font-semibold text-rose-700 block">Disadvantages:</span>
                  <ul className="list-disc list-inside text-slate-600 space-y-0.5">
                    {opt.cons.map((c, cIdx) => (
                      <li key={cIdx}>{c}</li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risks & Uncertainties Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        {/* Strategic Risks */}
        <div className="p-4 rounded-xl bg-rose-50/50 border border-rose-200 space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-rose-800 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-rose-600" />
            Strategic & Operational Risks
          </h4>
          <ul className="list-disc list-inside text-xs text-rose-900 space-y-1.5">
            {decisionBrief.strategic_risks.map((r, idx) => (
              <li key={idx}>{r}</li>
            ))}
          </ul>
        </div>

        {/* Key Uncertainties */}
        <div className="p-4 rounded-xl bg-amber-50/50 border border-amber-200 space-y-2">
          <h4 className="text-xs font-bold uppercase tracking-wider text-amber-800 flex items-center gap-1.5">
            <HelpCircle className="w-4 h-4 text-amber-600" />
            Decision-Altering Uncertainties
          </h4>
          <ul className="list-disc list-inside text-xs text-amber-900 space-y-1.5">
            {decisionBrief.important_uncertainties.map((u, idx) => (
              <li key={idx}>{u}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

