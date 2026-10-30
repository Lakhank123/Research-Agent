import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { HomeScreen } from './components/HomeScreen';
import { InvestigationWorkspace } from './components/InvestigationWorkspace';
import { ReportWorkspace } from './components/ReportWorkspace';
import {
  getSystemHealth,
  startResearch,
  subscribeToResearchEvents,
  getReport,
  getResearchHistory,
  getHistoryItem,
} from './api';
import { ResearchResult, ChallengeResult } from './types';

export function App() {
  const [view, setView] = useState<'home' | 'investigating' | 'report'>('home');
  const [question, setQuestion] = useState('');
  const [depth, setDepth] = useState<'quick' | 'standard' | 'deep'>('standard');
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);

  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [liveEvents, setLiveEvents] = useState<
    Array<{ stage: string; status: string; detail: string; timestamp?: string }>
  >([]);
  const [currentStage, setCurrentStage] = useState('planning');
  const [activeResult, setActiveResult] = useState<ResearchResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load health and history on mount
  useEffect(() => {
    getSystemHealth()
      .then(setSystemHealth)
      .catch((err) => console.warn('Health check issue:', err));

    getResearchHistory()
      .then(setHistory)
      .catch((err) => console.warn('History load issue:', err));
  }, []);

  // Launch Autonomous Research
  const handleStartResearch = async () => {
    if (!question.trim()) return;
    setIsLoading(true);
    setErrorMessage(null);
    setLiveEvents([]);
    setView('investigating');

    try {
      const { run_id } = await startResearch(question, depth);
      setCurrentRunId(run_id);

      // Subscribe to Server-Sent Events stream
      subscribeToResearchEvents(
        run_id,
        (event) => {
          setLiveEvents((prev) => [...prev, event]);
          if (event.stage) setCurrentStage(event.stage);
        },
        async () => {
          // Stream completed: fetch full structured report
          try {
            const reportData = await getReport(run_id);
            setActiveResult(reportData);
            setView('report');
            setIsLoading(false);
            // Refresh history
            getResearchHistory().then(setHistory);
          } catch (fetchErr: any) {
            setErrorMessage(fetchErr.message || 'Failed to fetch final report.');
            setIsLoading(false);
          }
        },
        (err) => {
          console.error('SSE Stream error:', err);
          // Fallback check after timeout
          setTimeout(async () => {
            try {
              const res = await getReport(run_id);
              setActiveResult(res);
              setView('report');
              setIsLoading(false);
            } catch (fallbackErr) {
              setErrorMessage('Streaming connection closed unexpectedly.');
              setIsLoading(false);
            }
          }, 3000);
        }
      );
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to initiate research pipeline.');
      setView('home');
      setIsLoading(false);
    }
  };

  // Reopen investigation from history
  const handleSelectHistory = async (runId: string) => {
    setIsLoading(true);
    try {
      const item = await getHistoryItem(runId);
      setActiveResult(item);
      setCurrentRunId(runId);
      setView('report');
    } catch (err: any) {
      alert('Could not load historical investigation: ' + err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateChallenge = (challengeRes: ChallengeResult) => {
    if (!activeResult) return;
    setActiveResult((prev) => {
      if (!prev) return prev;
      const updatedFindings = prev.report.key_findings.map((f) => {
        if (f.finding_id === challengeRes.claim_id) {
          return {
            ...f,
            verification_status: challengeRes.updated_verification_status,
          };
        }
        return f;
      });
      return {
        ...prev,
        report: {
          ...prev.report,
          key_findings: updatedFindings,
        },
        challenges: [...(prev.challenges || []), challengeRes],
      };
    });
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900 font-sans">
      <Header
        systemHealth={systemHealth}
        onNewSearch={() => {
          setView('home');
          setActiveResult(null);
        }}
      />

      {errorMessage && (
        <div className="max-w-4xl mx-auto w-full px-4 pt-4">
          <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs rounded-xl flex items-center justify-between">
            <span>{errorMessage}</span>
            <button onClick={() => setErrorMessage(null)} className="font-bold">
              ✕
            </button>
          </div>
        </div>
      )}

      <main className="flex-1 pb-16">
        {view === 'home' && (
          <HomeScreen
            question={question}
            setQuestion={setQuestion}
            depth={depth}
            setDepth={setDepth}
            onStartResearch={handleStartResearch}
            isLoading={isLoading}
            systemHealth={systemHealth}
            history={history}
            onSelectHistory={handleSelectHistory}
          />
        )}

        {view === 'investigating' && (
          <InvestigationWorkspace
            question={question}
            depth={depth}
            events={liveEvents}
            currentStage={currentStage}
          />
        )}

        {view === 'report' && activeResult && (
          <ReportWorkspace
            result={activeResult}
            onNewSearch={() => {
              setView('home');
              setActiveResult(null);
            }}
            onUpdateChallenge={handleUpdateChallenge}
          />
        )}
      </main>

      <footer className="border-t border-slate-200 bg-white py-6 text-center text-xs text-slate-500 space-y-1">
        <p className="font-medium text-slate-700">
          ResearchPilot AI 3.0 • The Research Integrity Engine
        </p>
        <p className="text-[11px] text-slate-400">
          Evidence-linked answers • Adversarial counter-research • Research completeness validation
        </p>
      </footer>
    </div>
  );
}

export default App;

