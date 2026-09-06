import { useEffect, useState } from 'react';
import { api, type Language } from './api';
import { useVoiceSession } from './useVoiceSession';
import { useSessionLive } from './useSessionLive';
import { Facts } from './SessionPanel';
import { Console } from './Console';
import './styles.css';

const languages: { code: Language; title: string; sub: string }[] = [
  { code: 'hi-IN', title: 'हिन्दी', sub: 'Hindi' },
  { code: 'en-IN', title: 'English', sub: 'English · India' },
  { code: 'ta-IN', title: 'தமிழ்', sub: 'Tamil' },
];
export default function App() {
  return <>
    <header className="site-header"><a className="brand" href="/"><span className="brand-mark" aria-hidden="true">e</span>EchoSphere<span className="brand-label">ASSISTANCE</span></a>
      <nav aria-label="Main navigation"><a href="/demo/call" aria-current={location.pathname !== '/console' ? 'page' : undefined}>Get assistance</a><a href="/console" aria-current={location.pathname === '/console' ? 'page' : undefined}>Operator workspace <span aria-hidden="true">↗</span></a></nav>
    </header>
    {location.pathname === '/console' ? <Console /> : <Caller />}
    <footer><span>EchoSphere · A human option, always within reach.</span><span>Synthetic demonstration · No audio recording</span></footer>
  </>;
}
function Caller() {
  const [language, setLanguage] = useState<Language>('hi-IN');
  const [capabilities, setCapabilities] = useState<{ voice_ready: boolean; speech_provider: string; voice_requirements?: { checks: Record<string, boolean> } } | null>(null);
  const [notice, setNotice] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const voice = useVoiceSession();
  const { snapshot, reconnecting } = useSessionLive(voice.session?.session_id, voice.session?.caller_capability);
  const session = snapshot ?? voice.session;
  const active = !['idle', 'ended', 'error', 'cleanup_pending'].includes(voice.state);
  useEffect(() => { void api<{ voice_ready: boolean; speech_provider: string; voice_requirements?: { checks: Record<string, boolean> } }>('/capabilities').then(setCapabilities).catch(() => setNotice('The service is offline. Start the backend and try again.')); }, []);
  useEffect(() => {
    if (snapshot?.status === 'ended' && active) void voice.end();
  }, [snapshot?.status, active, voice.end]);
  async function human() {
    if (!session || !voice.session) return;
    setNotice('');
    try { await api('/sessions/' + session.session_id + '/escalations', voice.session.caller_capability, { trigger: 'human_request' }); }
    catch (cause) { setNotice((cause as Error).message); }
  }
  async function sendText(event: React.FormEvent) {
    event.preventDefault();
    if (!voice.session || !message.trim()) return;
    setSending(true); setNotice('');
    try { await api('/sessions/' + voice.session.session_id + '/messages', voice.session.caller_capability, { text: message.trim() }); setMessage(''); }
    catch (cause) { setNotice((cause as Error).message); }
    finally { setSending(false); }
  }
  const transfer = session?.conversation.escalation;
  const connected = !!session && voice.members.includes(session.agent_uid);
  return <main className="page caller-page">
    <div className="page-heading"><p className="eyebrow">A little clarity. A helpful next step.</p><h1>Let’s take it<br />one question at a time.</h1><p className="lead">Tell us what’s happening, in the language that feels right.<br className="desktop-only" /> We’ll gather the details and help you reach a person when needed.</p></div>
    <div className="caller-grid">
      <aside className="panel call-controls">
        <div className="section-title"><h2>Your assistance session</h2><span className="badge">AI assistant</span></div>
        <fieldset disabled={active}><legend>Choose your starting language</legend><div className="language-options">{languages.map(item => <label className={'language-option ' + (language === item.code ? 'selected' : '')} key={item.code}>
          <input type="radio" name="language" checked={language === item.code} onChange={() => setLanguage(item.code)} /><strong lang={item.code}>{item.title}</strong><small>{item.sub}</small>
        </label>)}</div></fieldset>
        <div className="privacy-note"><span aria-hidden="true">◌</span><p>Please use <strong>sample information only</strong>. Audio is sent to Agora and its speech providers during voice calls. EchoSphere does not record audio.</p></div>
        {!active ? <div className="start-actions">
          <button className="primary" disabled={!capabilities} onClick={() => void voice.start(language)}><span aria-hidden="true">◉</span> Start voice assistance</button>
          {capabilities && !capabilities.voice_ready && <div className="warning small"><strong>Voice setup is incomplete.</strong><p>Configure the missing items, then restart the backend:</p><ul>{Object.entries(capabilities.voice_requirements?.checks ?? {}).filter(([, ok]) => !ok).map(([name]) => <li key={name}>{name.replaceAll('_', ' ')}</li>)}</ul></div>}
        </div> : <>
          <div className="call-status" role="status"><span className="status-dot" /><div><strong>{transfer ? session?.status.replaceAll('_', ' ') : voice.state === 'requesting-permission' ? 'Allow microphone access' : connected ? 'AI audio connected' : voice.state.replaceAll('_', ' ')}</strong><small>{reconnecting ? 'Reconnecting live updates…' : 'You can pause or ask for a person at any time.'}</small></div></div>
          <div className="actions stacked"><button className="primary" onClick={() => void human()} disabled={!!transfer}>Talk to a person</button>
            {session?.mode === 'voice' && <button className="secondary" onClick={() => void voice.toggleMute()}>{voice.muted ? 'Unmute microphone' : 'Mute microphone'}</button>}
            <button className="quiet danger" onClick={() => void voice.end()}>End session</button>
          </div>
        </>}
        {(notice || voice.error) && <p className="error" role="alert">{notice || voice.error}</p>}
        {voice.state === 'ended' && <p className="success" role="status">Your session has ended. Thank you.</p>}
        <div className="boundary-note"><strong>A clear boundary</strong><p>We help with support intake. We don’t provide medical, legal, financial, or emergency advice.</p></div>
      </aside>
      <div className="conversation-column">
        {session && voice.session ? <><section className="panel audio-session" aria-live="polite"><div className="section-title"><h2>Voice conversation</h2><span className="badge">Voice primary</span></div><p className="muted">Speak naturally. EchoSphere listens through Agora and replies with audio. Use the optional text box if your microphone is unavailable.</p><div className="audio-state"><span className="status-dot" /><strong>{connected ? "Listening and speaking" : "Connecting audio..."}</strong></div></section><form className="composer panel" onSubmit={sendText}><label htmlFor="customer-message">Optional text message</label><div className="composer-input"><textarea id="customer-message" value={message} onChange={event => setMessage(event.target.value)} maxLength={600} rows={2} placeholder="Type a message if you cannot speak" /><button disabled={sending || !message.trim()}>{sending ? "Sending..." : "Send"}</button></div></form><Facts session={session} token={voice.session.caller_capability} />{transfer && <p className="muted small">Your confirmed context is being shared with the operator. Continue speaking normally.</p>}</> : <section className="welcome panel">
          <p className="eyebrow">How we’ll help</p><h2>Space to explain.<br />Someone to listen.</h2><ol className="steps"><li><span>01</span><div><h3>Speak naturally</h3><p>Start in Hindi, English, or Tamil. Tell us what you need help with.</p></div></li><li><span>02</span><div><h3>Check the important details</h3><p>We’ll read them back. Confirm or correct anything before it becomes part of your case.</p></div></li><li><span>03</span><div><h3>Continue with a person</h3><p>Ask at any point. Your assistant receives the context so you don’t have to start over.</p></div></li></ol>
          <div className="welcome-bottom"><span lang="hi">आपकी भाषा।</span><span>Your pace.</span><span lang="ta">உங்கள் குரல்.</span></div>
        </section>}
      </div>
    </div>
  </main>;
}
