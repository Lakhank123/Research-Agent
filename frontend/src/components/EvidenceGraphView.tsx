import React, { useState } from 'react';
import { Finding, SourceRecord } from '../types';
import { Network, ArrowRight, ShieldCheck, Database, FileText } from 'lucide-react';

interface EvidenceGraphViewProps {
  question: string;
  subtasks: string[];
  findings: Finding[];
  sources: SourceRecord[];
}

export const EvidenceGraphView: React.FC<EvidenceGraphViewProps> = ({
  question,
  subtasks,
  findings,
  sources,
}) => {
  const [selectedFindingId, setSelectedFindingId] = useState<string | null>(
    findings.length > 0 ? findings[0].finding_id : null
  );

  const selectedFinding = findings.find((f) => f.finding_id === selectedFindingId) || findings[0];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-2.5 pb-4 border-b border-slate-100">
        <div className="w-9 h-9 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
          <Network className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-base font-bold text-slate-900">Visual Evidence Lineage Graph</h3>
          <p className="text-xs text-slate-500">
            Interactive traceability flow: Research Question → Subtasks → Findings → Evidence Chunks → Primary Sources
          </p>
        </div>
      </div>

      {/* Graph Visualizer Container */}
      <div className="bg-slate-50/70 rounded-xl border border-slate-200 p-5 space-y-6 overflow-x-auto">
        {/* Stage 1: Question */}
        <div className="flex items-center gap-3">
          <div className="px-3.5 py-2 rounded-lg bg-slate-900 text-white text-xs font-semibold shrink-0 shadow-sm flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-teal-400" />
            Inquiry Node
          </div>
          <ArrowRight className="w-4 h-4 text-slate-400 shrink-0" />
          <div className="p-2.5 rounded-lg bg-white border border-slate-300 text-xs font-medium text-slate-800 shadow-sm">
            "{question}"
          </div>
        </div>

        {/* Stage 2: Subtasks */}
        <div className="pl-4 border-l-2 border-teal-200 space-y-3">
          <span className="text-[11px] font-bold uppercase tracking-wider text-teal-800">
            Decomposed Subtask Nodes ({subtasks.length}):
          </span>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2">
            {subtasks.map((st, sIdx) => (
              <div key={sIdx} className="p-2.5 rounded-lg bg-white border border-slate-200 text-xs text-slate-700 shadow-sm">
                <span className="font-bold text-teal-700 block text-[10px]">SUBTASK #{sIdx + 1}</span>
                {st}
              </div>
            ))}
          </div>
        </div>

        {/* Stage 3: Interactive Finding Selector */}
        <div className="pl-4 border-l-2 border-teal-400 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-bold uppercase tracking-wider text-teal-900">
              Claim Nodes (Select finding to inspect traceability):
            </span>
            <span className="text-xs text-slate-400">Click finding pill below</span>
          </div>

          <div className="flex flex-wrap gap-2">
            {findings.map((f, fIdx) => (
              <button
                key={f.finding_id || fIdx}
                onClick={() => setSelectedFindingId(f.finding_id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                  selectedFinding?.finding_id === f.finding_id
                    ? 'bg-teal-700 text-white shadow-md'
                    : 'bg-white text-slate-700 border border-slate-200 hover:border-teal-400'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Finding #{fIdx + 1}</span>
              </button>
            ))}
          </div>

          {/* Active Finding Trace Details */}
          {selectedFinding && (
            <div className="p-4 rounded-xl bg-white border border-teal-200 shadow-sm space-y-3 mt-3">
              <h4 className="text-xs font-bold text-slate-900 leading-snug">
                "{selectedFinding.finding}"
              </h4>

              {/* Connected Excerpts & Sources */}
              <div className="space-y-2 pt-2 border-t border-slate-100">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Connected Evidence Chunks & Provenance:
                </span>

                {selectedFinding.verified_evidence_excerpts && selectedFinding.verified_evidence_excerpts.length > 0 ? (
                  selectedFinding.verified_evidence_excerpts.map((ex, exIdx) => {
                    const src = sources.find((s) => s.source_id === ex.source_id);
                    return (
                      <div key={exIdx} className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs space-y-1.5">
                        <div className="flex items-center justify-between text-slate-500 font-mono text-[11px]">
                          <span className="font-bold text-teal-800">Chunk [{ex.chunk_id}] → Source [{ex.source_id}]</span>
                          <span className="text-slate-400">{src?.publisher || src?.domain}</span>
                        </div>
                        <p className="text-slate-700 italic">"{ex.excerpt}"</p>
                        <a
                          href={ex.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-[11px] text-teal-700 hover:underline block pt-1 font-mono"
                        >
                          Source URL: {ex.url} ↗
                        </a>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-slate-400">No direct chunk connections tagged for this node.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

