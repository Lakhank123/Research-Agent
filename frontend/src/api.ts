import { ChallengeResult, ResearchResult } from './types';

const API_BASE = '/api';

export async function getSystemHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Health check failed');
  return res.json();
}

export async function startResearch(question: string, depth: string = 'standard'): Promise<{ run_id: string }> {
  const res = await fetch(`${API_BASE}/research/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, depth }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to start research' }));
    throw new Error(err.detail || 'Failed to start research');
  }
  return res.json();
}

export function subscribeToResearchEvents(
  runId: string,
  onEvent: (event: { stage: string; status: string; detail: string; data?: any }) => void,
  onDone: () => void,
  onError: (err: any) => void
) {
  const eventSource = new EventSource(`${API_BASE}/research/stream/${runId}`);

  eventSource.onmessage = (msg) => {
    try {
      const data = JSON.parse(msg.data);
      onEvent(data);
      if (data.stage === 'done') {
        eventSource.close();
        onDone();
      }
    } catch (e) {
      console.error('Error parsing SSE event:', e);
    }
  };

  eventSource.onerror = (err) => {
    eventSource.close();
    onError(err);
  };

  return () => {
    eventSource.close();
  };
}

export async function getReport(runId: string): Promise<ResearchResult> {
  const res = await fetch(`${API_BASE}/research/report/${runId}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch report' }));
    throw new Error(err.detail || 'Failed to fetch report');
  }
  return res.json();
}

export async function challengeFinding(
  runId: string,
  findingId: string,
  claimText: string,
  supportingExcerpts: string[],
  supportingUrls: string[]
): Promise<ChallengeResult> {
  const res = await fetch(`${API_BASE}/research/challenge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      run_id: runId,
      finding_id: findingId,
      claim_text: claimText,
      supporting_excerpts: supportingExcerpts,
      supporting_urls: supportingUrls,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Challenge request failed' }));
    throw new Error(err.detail || 'Challenge request failed');
  }
  return res.json();
}

export async function investigateGaps(
  runId: string,
  gapQueries: string[]
): Promise<{ run_id: string; discovered_evidence: any[] }> {
  const res = await fetch(`${API_BASE}/research/investigate-gaps`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      run_id: runId,
      gap_queries: gapQueries,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Gap investigation failed' }));
    throw new Error(err.detail || 'Gap investigation failed');
  }
  return res.json();
}

export async function getResearchHistory() {
  const res = await fetch(`${API_BASE}/history`);
  if (!res.ok) throw new Error('Failed to load history');
  return res.json();
}

export async function getHistoryItem(runId: string): Promise<ResearchResult> {
  const res = await fetch(`${API_BASE}/history/${runId}`);
  if (!res.ok) throw new Error('Failed to load historical investigation');
  return res.json();
}

export function getExportUrl(runId: string, format: 'markdown' | 'json' | 'csv') {
  return `${API_BASE}/export/${runId}?format=${format}`;
}

