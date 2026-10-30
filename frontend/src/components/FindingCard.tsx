import React, { useState } from 'react';
import { Finding, SourceRecord } from '../types';
import {
  ShieldCheck,
  AlertTriangle,
  HelpCircle,
  XCircle,
  Swords,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Copy,
  Check,
  Quote
} from 'lucide-react';

interface FindingCardProps {
  finding: Finding;
  index: number;
  sources: SourceRecord[];
  onChallenge: (finding: Finding) => void;
}

export const FindingCard: React.FC<FindingCardProps> = ({
  finding,
  index,
  sources,
  onChallenge,
}) => {
  const [showExcerpts, setShowExcerpts] = useState(false);
  const [copied, setCopied] = useState(false);

  const statusConfig = {
    SUPPORTED: {
      label: 'Verified Supported',
      color: 'bg-emerald-50 text-emerald-700 border-emerald-200',
      icon: ShieldCheck,
    },
    PARTIALLY_SUPPORTED: {
      label: 'Partially Supported',
      color: 'bg-amber-50 text-amber-700 border-amber-200',
      icon: AlertTriangle,
    },
    CONFLICTING: {
      label: 'Conflicting Evidence',
      color: 'bg-rose-50 text-rose-700 border-rose-200',
      icon: XCircle,
    },
    UNVERIFIED: {
      label: 'Unverified / Thin Evidence',
      color: 'bg-slate-100 text-slate-700 border-slate-200',
      icon: HelpCircle,
    },
  }[finding.verification_status || 'SUPPORTED'];

  const StatusIcon = statusConfig.icon;

  const handleCopy = () => {
    navigator.clipboard.writeText(`${finding.finding}\n\n${finding.explanation}`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getSourceBySid = (sid: string) => sources.find((s) => s.source_id === sid);

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow space-y-4">
      {/* Card Header & Verification Status Badge */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-400 font-mono">#{index}</span>
          <span
            className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${statusConfig.color}`}
          >
            <StatusIcon className="w-3.5 h-3.5" />
            {statusConfig.label}
          </span>
        </div>

        {/* Citation Chips */}
        <div className="flex flex-wrap items-center gap-1.5">
          {finding.citations.map((c) => {
            const src = getSourceBySid(c);
            return (
              <a
                key={c}
                href={src?.url || '#'}
                target="_blank"
                rel="noreferrer"
                title={src?.title || `Source ${c}`}
                className="inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded bg-slate-100 hover:bg-teal-50 text-teal-800 border border-slate-200 hover:border-teal-300 transition-colors"
              >
                [{c}]
                {src && <ExternalLink className="w-2.5 h-2.5 opacity-60" />}
              </a>
            );
          })}
        </div>
      </div>

      {/* Main Finding Statement */}
      <h3 className="text-base font-bold text-slate-900 leading-snug">
        {finding.finding}
      </h3>

      {/* Detailed Analysis Explanation */}
      <p className="text-sm text-slate-700 leading-relaxed">
        {finding.explanation}
      </p>

      {/* Metrics or Numbers Chips */}
      {finding.metrics_or_figures && finding.metrics_or_figures.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Metrics:</span>
          {finding.metrics_or_figures.map((m, mIdx) => (
            <span
              key={mIdx}
              className="text-xs font-mono font-medium px-2 py-0.5 rounded bg-slate-50 text-slate-700 border border-slate-200"
            >
              {m}
            </span>
          ))}
        </div>
      )}

      {/* Caveats / Limitations */}
      {finding.caveats && finding.caveats.length > 0 && (
        <div className="text-xs bg-amber-50/70 border border-amber-200/60 rounded-lg p-2.5 text-amber-900 space-y-1">
          <span className="font-semibold block">⚠️ Nuances & Conditions:</span>
          <ul className="list-disc list-inside space-y-0.5">
            {finding.caveats.map((cav, cIdx) => (
              <li key={cIdx}>{cav}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Inspectable Evidence Drawer */}
      {finding.verified_evidence_excerpts && finding.verified_evidence_excerpts.length > 0 && (
        <div className="pt-2">
          <button
            onClick={() => setShowExcerpts(!showExcerpts)}
            className="text-xs font-semibold text-teal-700 hover:text-teal-900 flex items-center gap-1.5 transition-colors"
          >
            <Quote className="w-3.5 h-3.5" />
            <span>
              {showExcerpts ? 'Hide Audited Evidence' : `Inspect ${finding.verified_evidence_excerpts.length} Verified Evidence Excerpts`}
            </span>
            {showExcerpts ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>

          {showExcerpts && (
            <div className="mt-3 space-y-2.5 pl-2 border-l-2 border-teal-200">
              {finding.verified_evidence_excerpts.map((ex, exIdx) => (
                <div key={exIdx} className="bg-slate-50 rounded-lg p-3 text-xs space-y-1 border border-slate-200">
                  <div className="flex items-center justify-between text-slate-500 font-mono text-[11px]">
                    <span className="font-bold text-teal-800">Source [{ex.source_id}] ({ex.chunk_id})</span>
                    <a href={ex.url} target="_blank" rel="noreferrer" className="hover:underline flex items-center gap-1">
                      Inspect URL ↗
                    </a>
                  </div>
                  <p className="text-slate-800 italic leading-relaxed">
                    "{ex.excerpt}"
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Action Footer */}
      <div className="flex items-center justify-between pt-4 border-t border-slate-100">
        <button
          onClick={() => onChallenge(finding)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold shadow-sm hover:shadow transition-all"
        >
          <Swords className="w-3.5 h-3.5 text-amber-400" />
          <span>Challenge this finding</span>
        </button>

        <button
          onClick={handleCopy}
          className="text-xs text-slate-500 hover:text-slate-800 flex items-center gap-1 transition-colors"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          <span>{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>
    </div>
  );
};

