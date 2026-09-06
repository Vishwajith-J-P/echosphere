export type Language = 'en-IN' | 'hi-IN' | 'ta-IN';
export type Mode = 'voice';
export interface Rtc { app_id: string; channel: string; uid: number; token: string; expires_at: number }
export interface Fact { value: string; version: number; state: string; confirmed_at: number | null }
export interface Escalation { id: string; trigger: string; status: string; version: number; assigned_to: string | null; requested_at: number }
export interface Conversation {
  status: string; language: Language; language_history: Language[]; required: string[];
  fields: Record<string, Fact>; history: (Fact & { field: string })[];
  challenge: { id: string; field: string; version: number; expires_at: number } | null;
  escalation: Escalation | null; confidence: { overall_band: string; reason_codes: string[] }; revision: number;
}
export interface SessionStatus {
  session_id: string; status: string; mode: Mode; requested_language: Language;
  provider_status: string; conversation: Conversation; ticket_status: string;
  generation: number; created_at: number; agent_uid: number; human_uid: number;
  transcript: { sequence: number; speaker: string; text: string; language: Language; delivery: string }[];
  snapshot: { summary: string; version: number; revision: number; open_questions: string[] } | null;
  reply?: string;
}
export interface SessionCreated extends SessionStatus { caller_capability: string; rtc: Rtc | null }
export interface Operator { username: string; role: 'agent' | 'supervisor' }
export interface QueueItem { session_id: string; status: string; language: Language; mode: Mode; escalation: Escalation; ticket_status: string }

export async function api<T>(path: string, token?: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch('/api' + path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: 'Bearer ' + token } : {}) },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal: signal ?? AbortSignal.timeout(20000),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.error?.message ?? 'The service could not complete your request.');
  return data as T;
}
export function createSession(language: Language) {
  return api<SessionCreated>('/sessions', undefined, { requested_language: language, client: { platform: 'web' } });
}
export function startAgent(session: SessionCreated) {
  return api<SessionStatus>('/sessions/' + session.session_id + '/start', session.caller_capability, {});
}
export function endSession(session: SessionCreated) {
  return api<SessionStatus>('/sessions/' + session.session_id + '/end', session.caller_capability, {});
}
export function parseSseFrame(frame: string): SessionStatus | null {
  if (!frame.split('\n').some(line => line.trim() === 'event: snapshot')) return null;
  const value = frame.split('\n').filter(line => line.startsWith('data:')).map(line => line.slice(5).trim()).join('\n');
  return value ? JSON.parse(value) as SessionStatus : null;
}
// Fetch permits bearer headers; credentials never enter an EventSource URL.
export async function watchSession(id: string, token: string | undefined, signal: AbortSignal, update: (state: SessionStatus) => void) {
  const response = await fetch('/api/sessions/' + id + '/events', { headers: token ? { Authorization: 'Bearer ' + token } : {}, signal });
  if (!response.ok || !response.body) throw new Error('Live updates disconnected. Reconnecting…');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let pending = '';
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      pending += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');
      let boundary: number;
      while ((boundary = pending.indexOf('\n\n')) >= 0) {
        const state = parseSseFrame(pending.slice(0, boundary));
        pending = pending.slice(boundary + 2);
        if (state) update(state);
      }
    }
  } finally { reader.releaseLock(); }
}
