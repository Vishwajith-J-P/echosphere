import { useEffect, useRef, useState } from 'react';
import { api, type Operator, type QueueItem, type Rtc, type SessionStatus } from './api';
import { useSessionLive } from './useSessionLive';
import { Facts, Transcript } from './SessionPanel';
import { joinMedia, type MediaSession } from './media';

export function Console() {
  const [operator, setOperator] = useState<Operator | null>(null);
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  async function login(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(''); setPending(true);
    const data = new FormData(event.currentTarget);
    try { setOperator(await api<Operator>('/auth/login', undefined, { access_token: data.get('access_token') })); }
    catch (cause) { setError((cause as Error).message); }
    finally { setPending(false); }
  }
  if (!operator) return <main className="page login-page"><section className="panel login-panel"><p className="eyebrow">Operator workspace</p><h1>Welcome back.</h1><p className="muted">Sign in with the configured operator access token to review context and continue a caller's conversation.</p><form onSubmit={event => void login(event)}><label htmlFor="access_token">Operator access token</label><input id="access_token" name="access_token" type="text" autoComplete="off" spellCheck={false} required /><button className="primary" disabled={pending}>{pending ? 'Signing in...' : 'Sign in'}</button></form>{error && <p role="alert" className="error">{error}</p>}<p className="small muted">Access is limited to the configured operator token.</p></section></main>;
  return <Workspace operator={operator} logout={() => { void api('/auth/logout', operator.token, {}); setOperator(null); }} />;
}

function Workspace({ operator, logout }: { operator: Operator; logout: () => void }) {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [selected, setSelected] = useState<string>();
  const [error, setError] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [jobs, setJobs] = useState<{ id: string; status: string; attempts: number }[]>([]);
  const { snapshot, reconnecting } = useSessionLive(selected, operator.token);
  const media = useRef<MediaSession | null>(null);
  const abort = useRef<AbortController | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    const refresh = async () => {
      try {
        setQueue((await api<{ items: QueueItem[] }>('/queue', operator.token, undefined, controller.signal)).items);
        setJobs((await api<{ items: typeof jobs }>('/integration-jobs', operator.token, undefined, controller.signal)).items);
      } catch (cause) { if (!controller.signal.aborted) setError((cause as Error).message); }
    };
    void refresh(); const timer = setInterval(() => void refresh(), 2500);
    return () => { controller.abort(); clearInterval(timer); };
  }, [operator.token]);
  useEffect(() => () => { abort.current?.abort(); void media.current?.close(); }, []);
  useEffect(() => {
    if (snapshot?.status === 'ended') { abort.current?.abort(); void media.current?.close(); setConnecting(false); }
  }, [snapshot?.status]);
  async function accept() {
    if (!snapshot?.conversation.escalation || !selected) return;
    setError(''); setConnecting(true); const id = selected;
    const escalation = snapshot.conversation.escalation;
    try {
      const result = await api<SessionStatus & { rtc: Rtc | null }>('/sessions/' + id + '/handoff/accept', operator.token,
        { escalation_id: escalation.id, snapshot_version: escalation.version });
      let published = false, callerReady = false, notified = false;
      const ready = async () => {
        if (!published || !callerReady || notified) return;
        notified = true;
        try { await api('/sessions/' + id + '/handoff/connected', operator.token, { media_ready: true }); setConnecting(false); }
        catch (cause) { setError((cause as Error).message); setConnecting(false); }
      };
      if (result.rtc) {
        abort.current?.abort(); abort.current = new AbortController();
        media.current = await joinMedia(result.rtc, abort.current.signal, members => {
          callerReady = members.some(uid => uid !== result.agent_uid && uid !== result.human_uid); void ready();
        }, state => { if (['AUDIO_ERROR', 'TOKEN_ERROR', 'DISCONNECTED'].includes(state)) setError('Media connection needs attention: ' + state.toLowerCase()); },
        async () => (await api<{ rtc: Rtc }>('/sessions/' + id + '/token', operator.token, {})).rtc);
        published = true; await ready();
      } else {
        await api('/sessions/' + id + '/handoff/connected', operator.token, { media_ready: true }); setConnecting(false);
      }
    } catch (cause) { setError((cause as Error).message); setConnecting(false); }
  }
  async function end() {
    abort.current?.abort(); await media.current?.close(); setConnecting(false);
    try { await api('/sessions/' + selected + '/end', operator.token, {}); }
    catch (cause) { setError((cause as Error).message); }
  }
  const mine = snapshot?.conversation.escalation?.assigned_to === operator.username;
  return <main className="page workspace"><div className="workspace-heading"><div><p className="eyebrow">{operator.role} workspace</p><h1>Conversations, with context.</h1></div><div className="actions"><span>{operator.username}</span><button className="quiet" onClick={logout}>Sign out</button></div></div>
    {error && <p className="error" role="alert">{error}</p>}
    <div className="workspace-grid"><aside className="panel queue"><div className="section-title"><h2>Handoff queue</h2><span className="badge">{queue.filter(item => item.status !== 'ended').length} active</span></div>
      {!queue.length && <div className="empty"><strong>No calls waiting</strong><p>New handoff requests appear here automatically.</p></div>}
      {queue.map(item => <button className={'queue-item ' + (selected === item.session_id ? 'selected' : '')} key={item.session_id} disabled={connecting || (mine && snapshot?.status === 'human_connected' && item.session_id !== selected)} onClick={() => setSelected(item.session_id)}>
        <span><strong>{item.language.slice(0, 2).toUpperCase()} · Voice call</strong><small>#{item.session_id.slice(0, 8)}</small></span><span className="badge">{item.status.replaceAll('_', ' ')}</span><small>{item.escalation.trigger.replaceAll('_', ' ')}</small>
      </button>)}
    </aside>
    <div className="conversation-column">{snapshot ? <><div className="transfer-banner"><div className="section-title"><strong>{snapshot.status.replaceAll('_', ' ')}</strong><span>{reconnecting ? 'Reconnecting…' : 'Live context'}</span></div><p>{snapshot.snapshot?.summary}</p>
      {snapshot.snapshot && snapshot.conversation.revision > snapshot.snapshot.revision && <p className="warning">Caller details changed after the accepted snapshot. Review the current facts below.</p>}
      <div className="actions">{['escalating', 'transferring'].includes(snapshot.status) && (!snapshot.conversation.escalation?.assigned_to || mine) && <button onClick={() => void accept()} disabled={connecting}>{connecting ? 'Waiting for caller audio…' : mine ? 'Retry connection' : 'Accept transfer'}</button>}{mine && snapshot.status !== 'ended' && <button className="secondary" onClick={() => void end()}>End session</button>}</div></div><Transcript session={snapshot} /><p className="muted small">The human continues this call by voice through Agora. Text replies are disabled.</p></> : <section className="panel empty workspace-empty"><h2>Ready when you are.</h2><p>Select a call to review its context before accepting.</p></section>}</div>
    <aside className="context-column">{snapshot && <Facts session={snapshot} token={operator.token} />}<section className="panel"><h2>Case synchronization</h2><p className="small muted">Ticket processing is independent of the call.</p>{jobs.length === 0 && <p className="empty">No integration jobs yet.</p>}{jobs.filter(job => !selected || job.id.startsWith(selected)).map(job => <div className="job" key={job.id}><span className="badge">{job.status}</span><small>{job.attempts} attempts</small>{operator.role === 'supervisor' && job.status !== 'succeeded' && <button className="quiet" onClick={() => void api('/integration-jobs/' + job.id + '/retry', operator.token, {}).catch(cause => setError(cause.message))}>Retry sync</button>}</div>)}</section></aside>
    </div></main>;
}
