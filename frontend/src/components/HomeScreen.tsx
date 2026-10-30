import React from 'react';
import {
  Compass,
  Search,
  ShieldCheck,
  HelpCircle,
  FileText,
  AlertTriangle,
  Layers,
  ArrowRight,
  TrendingUp,
  Cpu,
  Building2,
  Users,
  CheckCircle2,
  Clock,
  Sparkles
} from 'lucide-react';

interface HomeScreenProps {
  question: string;
  setQuestion: (q: string) => void;
  depth: 'quick' | 'standard' | 'deep';
  setDepth: (d: 'quick' | 'standard' | 'deep') => void;
  onStartResearch: () => void;
  isLoading: boolean;
  systemHealth: any;
  history: any[];
  onSelectHistory: (runId: string) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  question,
  setQuestion,
  depth,
  setDepth,
  onStartResearch,
  isLoading,
  systemHealth,
  history,
  onSelectHistory,
}) => {
  const exampleTemplates = [
    {
      icon: Cpu,
      category: 'Technology Comparison',
      query: 'Compare the top 3 open-source vector databases (Qdrant, Milvus, Chroma) for an enterprise startup building RAG products.',
    },
    {
      icon: Users,
      category: 'Startup Discovery',
      query: 'Find 5 leading Indian B2B SaaS startups in HR tech and describe their business models, funding, and key competitors.',
    },
    {
      icon: Building2,
      category: 'Company Intelligence',
      query: 'Research Databricks core business model, Lakehouse architecture differentiation, and enterprise revenue milestones.',
    },
    {
      icon: TrendingUp,
      category: 'Market & Industry Analysis',
      query: 'Analyze the global advanced semiconductor packaging market landscape, focusing on 2.5D/3D adoption and TSMC vs Intel positioning.',
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-12">
      {/* Hero Header */}
      <div className="text-center space-y-4 max-w-3xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-teal-50 border border-teal-200 text-teal-800 text-xs font-semibold uppercase tracking-wider">
          <Compass className="w-3.5 h-3.5 text-teal-600 animate-spin-slow" />
          The Research Integrity Engine
        </div>
        <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight leading-tight">
          From Questions to Decisions.<br />
          <span className="text-teal-700">Backed by Evidence.</span>
        </h1>
        <p className="text-lg text-slate-600 leading-relaxed">
          Autonomous intelligence for high-stakes decisions. Every factual claim is bound to an audited evidence ledger, every gap is surfaced, and every finding can be actively challenged.
        </p>
      </div>

      {/* Main Research Input Card */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xl shadow-slate-200/50 p-6 md:p-8 space-y-6">
        <div className="space-y-2">
          <label className="block text-sm font-semibold text-slate-700">
            What research inquiry or strategic question would you like to investigate?
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g., Compare the top 3 open-source vector databases for RAG startups, or Find 5 Indian B2B SaaS startups in HR tech and summarize their positioning..."
            rows={3}
            className="w-full rounded-xl border border-slate-300 p-4 text-slate-900 text-base placeholder-slate-400 focus:border-teal-600 focus:ring-2 focus:ring-teal-100 transition-all outline-none resize-none"
          />
        </div>

        {/* Controls Row */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2 border-t border-slate-100">
          <div className="flex items-center gap-2 w-full sm:w-auto">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Depth:</span>
            <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1">
              {(['quick', 'standard', 'deep'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => setDepth(mode)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium capitalize transition-all ${
                    depth === mode
                      ? 'bg-white text-teal-800 shadow-sm font-semibold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
            <span className="text-xs text-slate-400 hidden md:inline ml-2">
              {depth === 'quick' && '• 3 queries, fast overview'}
              {depth === 'standard' && '• 4 queries, structured analysis'}
              {depth === 'deep' && '• 5 queries, deep counter-evidence'}
            </span>
          </div>

          <button
            onClick={onStartResearch}
            disabled={isLoading || !question.trim()}
            className="w-full sm:w-auto px-7 py-3 rounded-xl bg-teal-700 hover:bg-teal-800 disabled:bg-slate-300 text-white font-semibold flex items-center justify-center gap-2 shadow-lg shadow-teal-700/20 transition-all"
          >
            {isLoading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Launching Pipeline...</span>
              </>
            ) : (
              <>
                <span>Start Autonomous Research</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>

      {/* Verified Research Templates */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-teal-600" />
            Verified Research Scenarios
          </h2>
          <span className="text-xs text-slate-400">Click any card to load</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {exampleTemplates.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div
                key={idx}
                onClick={() => setQuestion(item.query)}
                className="group cursor-pointer bg-white p-5 rounded-xl border border-slate-200 hover:border-teal-500 hover:shadow-md transition-all space-y-2"
              >
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-teal-700 bg-teal-50 px-2.5 py-1 rounded-md">
                    <Icon className="w-3.5 h-3.5" />
                    {item.category}
                  </span>
                  <span className="text-slate-300 group-hover:text-teal-600 transition-colors">↗</span>
                </div>
                <p className="text-sm text-slate-700 group-hover:text-slate-900 leading-snug font-medium">
                  "{item.query}"
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Investigations History */}
      {history && history.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
            <Clock className="w-4 h-4 text-teal-600" />
            Recent Investigations
          </h2>
          <div className="bg-white rounded-xl border border-slate-200 divide-y divide-slate-100 overflow-hidden">
            {history.slice(0, 5).map((h) => (
              <div
                key={h.run_id}
                onClick={() => onSelectHistory(h.run_id)}
                className="p-4 flex items-center justify-between hover:bg-slate-50 cursor-pointer transition-colors"
              >
                <div className="space-y-1 pr-4">
                  <p className="text-sm font-semibold text-slate-800 line-clamp-1">{h.question}</p>
                  <div className="flex items-center gap-3 text-xs text-slate-500">
                    <span>{new Date(h.created_at).toLocaleDateString()}</span>
                    <span>•</span>
                    <span className="capitalize">{h.depth} mode</span>
                    <span>•</span>
                    <span className="uppercase text-teal-700 font-semibold">{h.status}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-teal-700 text-xs font-semibold">
                  <span>Reopen</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Why Choose ResearchPilot Comparison Section */}
      <div className="pt-8 border-t border-slate-200 space-y-6">
        <div className="text-center space-y-2 max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-slate-900">Why ResearchPilot AI?</h2>
          <p className="text-sm text-slate-600">
            A fundamental architectural shift from generative chatbots to rigorous research intelligence.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
            <div className="w-10 h-10 rounded-lg bg-teal-50 border border-teal-200 flex items-center justify-center text-teal-700">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900">Claim-Level Evidence Ledger</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Never wonder if a citation is accurate. Findings are audited with exact text excerpts from primary documentation, eliminating phantom references.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
            <div className="w-10 h-10 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900">"Challenge This Finding"</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Actively dispatch counter-research queries to unearth contradictory evidence, technical criticisms, and market rebuttals before you make an executive commitment.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-700">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-slate-900">Research Completeness Gate</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              If you request 10 startups and only 7 can be confirmed, we explicitly state 7/10 and mark the run PARTIALLY COMPLETED. We never fabricate entities.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

