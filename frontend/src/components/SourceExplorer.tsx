import React, { useState } from 'react';
import { SourceRecord } from '../types';
import { Globe, ExternalLink, Filter, ShieldCheck, Calendar, BookOpen } from 'lucide-react';

interface SourceExplorerProps {
  sources: SourceRecord[];
}

export const SourceExplorer: React.FC<SourceExplorerProps> = ({ sources }) => {
  const [filterType, setFilterType] = useState<string>('all');
  const [sortField, setSortField] = useState<'authority' | 'relevance' | 'freshness'>('authority');

  const filteredSources = sources.filter((s) => {
    if (filterType === 'all') return true;
    if (filterType === 'primary') return s.is_primary_source;
    if (filterType === 'media') return s.source_type.includes('media');
    if (filterType === 'academic') return s.source_type.includes('academic');
    return true;
  });

  const sortedSources = [...filteredSources].sort((a, b) => {
    if (sortField === 'authority') return b.authority_score - a.authority_score;
    if (sortField === 'relevance') return b.relevance_score - a.relevance_score;
    if (sortField === 'freshness') return b.freshness_score - a.freshness_score;
    return 0;
  });

  const getBadgeStyle = (stype: string, isPrimary: boolean) => {
    if (isPrimary) return 'bg-sky-50 text-sky-800 border-sky-200';
    if (stype.includes('media')) return 'bg-amber-50 text-amber-800 border-amber-200';
    if (stype.includes('academic')) return 'bg-purple-50 text-purple-800 border-purple-200';
    return 'bg-slate-100 text-slate-700 border-slate-200';
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div>
          <h3 className="text-base font-bold text-slate-900">Interactive Source Explorer & Authority Ledger</h3>
          <p className="text-xs text-slate-500">
            {sources.length} evaluated web sources with transparent authority, freshness, and extraction status
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Filter */}
          <div className="flex items-center gap-1.5 text-xs text-slate-500">
            <Filter className="w-3.5 h-3.5" />
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-slate-700 font-medium outline-none focus:border-teal-500"
            >
              <option value="all">All Sources ({sources.length})</option>
              <option value="primary">Official / Primary</option>
              <option value="media">Reputable Media</option>
              <option value="academic">Academic & Regulatory</option>
            </select>
          </div>

          {/* Sort */}
          <select
            value={sortField}
            onChange={(e) => setSortField(e.target.value as any)}
            className="bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1 text-xs text-slate-700 font-medium outline-none focus:border-teal-500"
          >
            <option value="authority">Sort by Authority Score</option>
            <option value="relevance">Sort by Contextual Relevance</option>
            <option value="freshness">Sort by Freshness</option>
          </select>
        </div>
      </div>

      {/* Source Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sortedSources.map((s) => {
          const badgeClass = getBadgeStyle(s.source_type, s.is_primary_source);

          return (
            <div
              key={s.source_id}
              className="bg-white rounded-xl border border-slate-200 p-4 space-y-3 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-start justify-between gap-2">
                  <span className="font-mono text-xs font-bold text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                    [{s.source_id}]
                  </span>
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${badgeClass}`}>
                    {s.is_primary_source ? 'Primary Documentation' : s.source_type.replace('_', ' ')}
                  </span>
                </div>

                <h4 className="text-sm font-bold text-slate-900 line-clamp-2 leading-snug">
                  {s.title || s.url}
                </h4>

                <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 font-medium pt-1">
                  <span>Domain: <strong className="text-slate-700">{s.domain}</strong></span>
                  {s.published_date && (
                    <span>• Date: <strong className="text-slate-700">{s.published_date}</strong></span>
                  )}
                  <span>• Extraction: <strong className="text-slate-700">{s.extraction_status}</strong></span>
                </div>

                {s.reason_for_selection && (
                  <p className="text-[11px] text-slate-500 bg-slate-50 p-2 rounded-lg border border-slate-100">
                    <span className="font-semibold text-slate-600">Selection Rationale:</span> {s.reason_for_selection}
                  </p>
                )}
              </div>

              {/* Card Footer */}
              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase">Authority:</span>
                  <span className="font-mono font-bold text-slate-800">{s.authority_score.toFixed(2)}</span>
                </div>

                <a
                  href={s.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 font-semibold text-teal-700 hover:text-teal-900 hover:underline"
                >
                  <span>Open Webpage</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

