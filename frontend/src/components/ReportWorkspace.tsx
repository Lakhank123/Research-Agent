import React, { useState } from 'react';
import { ResearchResult, Finding, ChallengeResult } from '../types';
import { getExportUrl } from '../api';
import { FindingCard } from './FindingCard';
import { ChallengeModal } from './ChallengeModal';
import { CompletenessGateView } from './CompletenessGateView';
import { ResearchGapView } from './ResearchGapView';
import { DecisionBriefView } from './DecisionBriefView';
import { EvidenceGraphView } from './EvidenceGraphView';
import { SourceExplorer } from './SourceExplorer';
import {
  FileText,
  ShieldCheck,
  Scale,
  Database,
  Swords,
  Search,
  Briefcase,
  Layers,
  Download,
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  Network
} from 'lucide-react';

interface ReportWorkspaceProps {
  result: ResearchResult;
  onNewSearch: () => void;
  onUpdateChallenge: (res: ChallengeResult) => void;
}

type TabType =
  | 'overview'
  | 'findings'
  | 'decision'
  | 'completeness'
  | 'gaps'
  | 'sources'
  | 'graph'
  | 'methodology';

export const ReportWorkspace: React.FC<ReportWorkspaceProps> = ({
  result,
  onNewSearch,
  onUpdateChallenge,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [challengingFinding, setChallengingFinding] = useState<Finding | null>(null);

  const report = result.report;
  const plan = result.plan;
  const metrics = result.metrics;
  const runId = result.run_id || 'active';

  const statusLabel = report.status || 'COMPLETED';
  const isComplete = statusLabel === 'COMPLETED';
  const isPartial = statusLabel === 'PARTIALLY_COMPLETED';

  const tabs = [
    { key: 'overview', label: 'Executive Summary', icon: FileText },
    { key: 'findings', label: `Key Findings (${report.key_findings.length})`, icon: ShieldCheck },
    { key: 'decision', label: 'Decision Brief', icon: Briefcase },
    { key: 'completeness', label: 'Completeness Gate', icon: Layers },
    { key: 'gaps', label: 'Research Gaps', icon: Search },
    { key: 'sources', label: `Sources (${report.sources_used.length})`, icon: Database },
    { key: 'graph', label: 'Evidence Graph', icon: Network },
    { key: 'methodology', label: 'Audit & Trace', icon: Scale },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* Top Bar with Status & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200">
        <button
          onClick={onNewSearch}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>New Investigation</span>
        </button>

        {/* Export Dropdown / Actions */}
        <div className="flex items-center gap-2">
          <a
            href={getExportUrl(runId, 'markdown')}
            download
            className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 inline-flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3 h-3 text-slate-500" />
            <span>Export Markdown</span>
          </a>
          <a
            href={getExportUrl(runId, 'json')}
            download
            className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-50 text-xs font-semibold text-slate-700 inline-flex items-center gap-1.5 transition-colors"
          >
            <Download className="w-3 h-3 text-slate-500" />
            <span>Export JSON</span>
          </a>
        </div>
      </div>

      {/* Inquiry Title Header & Status Ribbon */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-2.5">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider inline-flex items-center gap-1.5 ${
              isComplete
                ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                : isPartial
                ? 'bg-amber-50 text-amber-800 border border-amber-200'
                : 'bg-rose-50 text-rose-800 border border-rose-200'
            }`}
          >
            {isComplete ? <CheckCircle2 className="w-3.5 h-3.5" /> : <AlertTriangle className="w-3.5 h-3.5" />}
            {statusLabel}
          </span>
          <span className="text-xs font-semibold text-slate-500 capitalize bg-slate-100 px-2.5 py-1 rounded-md">
            Confidence: {report.confidence.toUpperCase()} ({report.confidence_score.toFixed(2)})
          </span>
          <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-md">
            Duration: {metrics.total_duration_seconds}s
          </span>
        </div>

        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 leading-snug">
          "{report.user_question}"
        </h1>
      </div>

      {/* Workspace Persistent Tab Navigation */}
      <div className="border-b border-slate-200 flex overflow-x-auto gap-2 no-scrollbar">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as TabType)}
              className={`pb-3 px-3 text-xs font-semibold border-b-2 flex items-center gap-2 whitespace-nowrap transition-all ${
                isActive
                  ? 'border-teal-700 text-teal-800 font-bold'
                  : 'border-transparent text-slate-500 hover:text-slate-800 hover:border-slate-300'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-teal-700' : 'text-slate-400'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab Panels */}
      <div className="space-y-6">
        {/* OVERVIEW TAB */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Executive Summary Card */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 md:p-8 space-y-4 shadow-sm">
              <span className="text-xs font-bold uppercase tracking-wider text-teal-700 flex items-center gap-1.5">
                <FileText className="w-4 h-4" />
                Direct Executive Answer
              </span>
              <p className="text-base text-slate-800 leading-relaxed font-medium">
                {report.executive_summary || report.short_answer}
              </p>
              <div className="pt-3 border-t border-slate-100 text-xs text-slate-500">
                <strong>Confidence Rationale:</strong> {report.confidence_reason}
              </div>
            </div>

            {/* Comparison Table (If populated) */}
            {report.comparison_table && report.comparison_table.headers && report.comparison_table.rows && (
              <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4 shadow-sm">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
                  <Scale className="w-4 h-4 text-teal-600" />
                  Comparative Analysis Breakdown
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 bg-slate-50">
                        {report.comparison_table.headers.map((h, idx) => (
                          <th key={idx} className="p-3 font-bold text-slate-700">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {report.comparison_table.rows.map((row, rIdx) => (
                        <tr key={rIdx} className="hover:bg-slate-50/50">
                          {report.comparison_table!.headers.map((h, cIdx) => (
                            <td key={cIdx} className="p-3 text-slate-800 font-medium">
                              {row[h] || '—'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Quick Preview of Decision Brief & Top Findings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Decision Highlight</h3>
                <p className="text-sm font-bold text-slate-900 leading-snug">
                  {report.decision_brief?.main_conclusion || 'Review key findings for strategic analysis.'}
                </p>
                <button
                  onClick={() => setActiveTab('decision')}
                  className="text-xs font-semibold text-teal-700 hover:underline inline-flex items-center gap-1"
                >
                  Inspect Full Decision Brief ↗
                </button>
              </div>

              <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">Completeness Gate</h3>
                <p className="text-sm font-bold text-slate-900 leading-snug">
                  {report.completeness?.is_complete ? 'All requirements satisfied.' : report.completeness?.gap_explanation}
                </p>
                <button
                  onClick={() => setActiveTab('completeness')}
                  className="text-xs font-semibold text-teal-700 hover:underline inline-flex items-center gap-1"
                >
                  View Completeness Gate Audit ↗
                </button>
              </div>
            </div>
          </div>
        )}

        {/* KEY FINDINGS TAB */}
        {activeTab === 'findings' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2">
              <span className="text-xs font-semibold text-slate-500">
                Audited evidence findings. Click <strong>"Challenge this finding"</strong> to execute counter-research.
              </span>
            </div>
            {report.key_findings.map((f, idx) => (
              <FindingCard
                key={f.finding_id || idx}
                finding={f}
                index={idx + 1}
                sources={report.sources_used}
                onChallenge={(finding) => setChallengingFinding(finding)}
              />
            ))}
          </div>
        )}

        {/* DECISION BRIEF TAB */}
        {activeTab === 'decision' && (
          <DecisionBriefView decisionBrief={report.decision_brief} />
        )}

        {/* COMPLETENESS GATE TAB */}
        {activeTab === 'completeness' && (
          <CompletenessGateView completeness={report.completeness} contract={report.contract} />
        )}

        {/* RESEARCH GAPS TAB */}
        {activeTab === 'gaps' && (
          <ResearchGapView runId={runId} coverageMatrix={report.coverage_matrix} />
        )}

        {/* SOURCES TAB */}
        {activeTab === 'sources' && (
          <SourceExplorer sources={report.sources_used} />
        )}

        {/* EVIDENCE GRAPH TAB */}
        {activeTab === 'graph' && (
          <EvidenceGraphView
            question={report.user_question}
            subtasks={plan.subtasks || []}
            findings={report.key_findings}
            sources={report.sources_used}
          />
        )}

        {/* METHODOLOGY & AUDIT TRACE TAB */}
        {activeTab === 'methodology' && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-6">
            <h3 className="text-base font-bold text-slate-900">Execution Plan & Audit Diagnostics</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Planned Queries:</span>
                <ul className="list-disc list-inside text-xs text-slate-700 space-y-1 font-mono">
                  {plan.search_queries.map((q, qIdx) => (
                    <li key={qIdx}>{q.query}</li>
                  ))}
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Assumptions & Limitations:</span>
                <ul className="list-disc list-inside text-xs text-slate-700 space-y-1">
                  {report.limitations.map((lim, lIdx) => (
                    <li key={lIdx}>{lim}</li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Execution Trace */}
            {result.trace && result.trace.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-400">Backend Event Trace:</span>
                <div className="bg-slate-900 text-slate-300 p-4 rounded-xl font-mono text-xs space-y-1 max-h-64 overflow-y-auto">
                  {result.trace.map((tr, tIdx) => (
                    <div key={tIdx} className="flex gap-2">
                      <span className="text-teal-400">[{tr.stage}]</span>
                      <span className="text-slate-400">{tr.status}:</span>
                      <span>{tr.detail}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Challenge Modal Overlay */}
      {challengingFinding && (
        <ChallengeModal
          runId={runId}
          finding={challengingFinding}
          onClose={() => setChallengingFinding(null)}
          onSaveChallengeResult={(cRes) => {
            onUpdateChallenge(cRes);
          }}
        />
      )}
    </div>
  );
};

