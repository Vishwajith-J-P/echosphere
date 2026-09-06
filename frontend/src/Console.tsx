import { useEffect, useRef, useState } from 'react';
import { api, type Operator, type QueueItem, type Rtc, type SessionStatus } from './api';
import { useSessionLive } from './useSessionLive';
import { Facts, Transcript } from './SessionPanel';
import { joinMedia, type MediaSession } from './media';

export function Console() {
  const operator: Operator = { username: 'local-operator', role: 'supervisor' };
  const [error, setError] = useState('');
  return <Workspace operator={operator} />;
}

function Workspace({ operator }: { operator: Operator }) {
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [selected, setSelected] = useState<string>();
  const [error, setError] = useState('');
  const [connecting, setConnecting] = useState(false);
  const [muted, setMuted] = useState(false);
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [now, setNow] = useState(() => Date.now());
  const [jobs, setJobs] = useState<{ id: string; status: string; attempts: number }[]>([]);
  const { snapshot, reconnecting } = useSessionLive(selected, undefined);
  const media = useRef<MediaSession | null>(null);
  const abort = useRef<AbortController | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    const refresh = async () => {
      try {
        setQueue((await api<{ items: QueueItem[] }>('/queue', undefined, undefined, controller.signal)).items);
        setJobs((await api<{ items: typeof jobs }>('/integration-jobs', undefined, undefined, controller.signal)).items);
      } catch (cause) { if (!controller.signal.aborted) setError((cause as Error).message); }
    };
    void refresh(); const timer = setInterval(() => void refresh(), 2500);
    return () => { controller.abort(); clearInterval(timer); };
  }, []);
  useEffect(() => () => { abort.current?.abort(); void media.current?.close(); }, []);
  useEffect(() => {
    if (snapshot?.status === 'ended') { abort.current?.abort(); void media.current?.close(); setConnecting(false); }
  }, [snapshot?.status]);
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  async function accept() {
    if (!snapshot?.conversation.escalation || !selected) return;
    setError(''); setConnecting(true); const id = selected;
    const escalation = snapshot.conversation.escalation;
    try {
      const result = await api<SessionStatus & { rtc: Rtc | null }>('/sessions/' + id + '/handoff/accept', undefined,
        { escalation_id: escalation.id, snapshot_version: escalation.version });
      let published = false, callerReady = false, notified = false;
      const ready = async () => {
        if (!published || !callerReady || notified) return;
        notified = true;
        try { await api('/sessions/' + id + '/handoff/connected', undefined, { media_ready: true }); setConnecting(false); }
        catch (cause) { setError((cause as Error).message); setConnecting(false); }
      };
      if (result.rtc) {
        abort.current?.abort(); abort.current = new AbortController();
        media.current = await joinMedia(result.rtc, abort.current.signal, members => {
          callerReady = members.some(uid => uid !== result.agent_uid && uid !== result.human_uid); void ready();
        }, state => { if (['AUDIO_ERROR', 'TOKEN_ERROR', 'DISCONNECTED'].includes(state)) setError('Media connection needs attention: ' + state.toLowerCase()); },
        async () => (await api<{ rtc: Rtc }>('/sessions/' + id + '/token', undefined, {})).rtc);
        published = true; await ready();
      } else {
        await api('/sessions/' + id + '/handoff/connected', undefined, { media_ready: true }); setConnecting(false);
      }
    } catch (cause) { setError((cause as Error).message); setConnecting(false); }
  }
  async function end() {
    abort.current?.abort(); await media.current?.close(); setConnecting(false);
    try { await api('/sessions/' + selected + '/end', undefined, {}); }
    catch (cause) { setError((cause as Error).message); }
  }
  async function toggleMute() {
    if (!media.current) return;
    const next = !muted;
    try { await media.current.mute(next); setMuted(next); }
    catch (cause) { setError((cause as Error).message); }
  }
  async function sendMessage(event: React.FormEvent) {
    event.preventDefault();
    if (!selected || !message.trim() || snapshot?.status !== 'human_connected') return;
    setSending(true); setError('');
    try { await api('/sessions/' + selected + '/messages', undefined, { text: message.trim() }); setMessage(''); }
    catch (cause) { setError((cause as Error).message); }
    finally { setSending(false); }
  }
  const mine = snapshot?.conversation.escalation?.assigned_to === operator.username;
  const escalation = snapshot?.conversation.escalation;
  const elapsed = escalation ? Math.max(0, Math.floor((now - escalation.requested_at * 1000) / 1000)) : 0;
  const elapsedLabel = elapsed < 60 ? `${elapsed}s` : `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`;
  return <main className="page workspace"><div className="workspace-heading"><div><p className="eyebrow">{operator.role} workspace</p><h1>Conversations, with context.</h1></div><div className="actions"><span>{operator.username}</span></div></div>
    {error && <p className="error" role="alert">{error}</p>}
    <div className="workspace-grid"><aside className="panel queue"><div className="section-title"><h2>Handoff queue</h2><span className="badge">{queue.filter(item => item.status !== 'ended').length} active</span></div>
      <button className="quiet" onClick={() => void api<{ cleared: number }>('/queue/clear', undefined, {}).then(result => { setQueue([]); setSelected(undefined); setError(result.cleared ? `${result.cleared} pending handoff(s) cleared.` : 'No pending handoffs to clear.'); }).catch(cause => setError((cause as Error).message))}>Clear handoff queue</button>
      {!queue.length && <div className="empty"><strong>No calls waiting</strong><p>New handoff requests appear here automatically.</p></div>}
      {queue.map(item => <button className={'queue-item ' + (selected === item.session_id ? 'selected' : '')} key={item.session_id} disabled={connecting || (mine && snapshot?.status === 'human_connected' && item.session_id !== selected)} onClick={() => setSelected(item.session_id)}>
        <span><strong>{item.language.slice(0, 2).toUpperCase()} · Voice call</strong><small>#{item.session_id.slice(0, 8)}</small></span><span className="badge">{item.status.replaceAll('_', ' ')}</span><small>{item.escalation.trigger.replaceAll('_', ' ')}</small>
      </button>)}
    </aside>
    <div className="conversation-column">{snapshot ? <><div className="transfer-banner"><div className="section-title"><strong>{snapshot.status.replaceAll("_", " ")}</strong><span>{reconnecting ? "Reconnecting..." : "Live context"}</span></div><p>{snapshot.snapshot?.summary}</p>
      {escalation && <div className="detail-row"><span>Escalated</span><strong>{new Date(escalation.requested_at * 1000).toLocaleString()} - {elapsedLabel} ago</strong></div>}
      {snapshot.snapshot && snapshot.conversation.revision > snapshot.snapshot.revision && <p className="warning">Caller details changed after the accepted snapshot. Review the current facts below.</p>}
      <div className="actions">{["escalating", "transferring"].includes(snapshot.status) && (!snapshot.conversation.escalation?.assigned_to || mine) && <button onClick={() => void accept()} disabled={connecting}>{connecting ? "Waiting for caller audio..." : mine ? "Retry connection" : "Accept transfer"}</button>}{mine && snapshot.status === "human_connected" && <button className="secondary" onClick={() => void toggleMute()}>{muted ? "Unmute microphone" : "Mute microphone"}</button>}{snapshot.status !== "ended" && <button className="quiet danger" onClick={() => void end()}>End conversation</button>}</div></div><Transcript session={snapshot} />{snapshot.status === "human_connected" && <form className="composer panel" onSubmit={sendMessage}><label htmlFor="human-message">Optional message to caller</label><div className="composer-input"><textarea id="human-message" value={message} onChange={event => setMessage(event.target.value)} maxLength={600} rows={2} placeholder="Send a short text message if voice is unavailable" /><button disabled={sending || !message.trim()}>{sending ? "Sending..." : "Send"}</button></div></form>}<p className="muted small">The human continues this call by voice through Agora. Text is an optional fallback.</p></> : <section className="panel empty workspace-empty"><h2>Ready when you are.</h2><p>Select a call to review its context before accepting.</p></section>}</div>
    <aside className="context-column">{snapshot && <Facts session={snapshot} token={undefined} />}<section className="panel"><h2>Case synchronization</h2><p className="small muted">Ticket processing is independent of the call.</p>{jobs.length === 0 && <p className="empty">No integration jobs yet.</p>}{jobs.filter(job => !selected || job.id.startsWith(selected)).map(job => <div className="job" key={job.id}><span className="badge">{job.status}</span><small>{job.attempts} attempts</small>{operator.role === 'supervisor' && job.status !== 'succeeded' && <button className="quiet" onClick={() => void api('/integration-jobs/' + job.id + '/retry', undefined, {}).catch(cause => setError(cause.message))}>Retry sync</button>}</div>)}</section></aside>
    </div></main>;
}
