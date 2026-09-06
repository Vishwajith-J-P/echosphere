import { type SessionStatus } from './api';

export const fieldLabels: Record<string, string> = { intent: 'Reason for calling', issue_details: 'Issue details',
  location_or_service_area: 'Service area', contact_name: 'Contact name', callback_number: 'Callback number', preferred_language: 'Preferred language' };

export function Transcript({ session }: { session: SessionStatus }) {
  return <section className="transcript panel" aria-labelledby="transcript-title">
    <div className="section-title"><h2 id="transcript-title">Audio conversation record</h2><span className="badge">Live voice</span></div>
    <p className="muted small">Speech is carried through Agora. This record is operational context for the authorized operator, not a caller input control.</p>
    <ol className="messages" aria-label="Conversation transcript" aria-live="polite" aria-relevant="additions">
      {session.transcript.map(turn => <li key={turn.sequence} className={'message ' + turn.speaker}>
        <div className="message-meta"><strong>{turn.speaker === 'ai' ? 'EchoSphere · AI' : turn.speaker === 'human' ? 'Human assistant' : 'You · Caller'}</strong><span>{turn.language.slice(0, 2).toUpperCase()}</span></div>
        <p lang={turn.language}>{turn.text}</p>
        {turn.delivery !== 'text' && <small className="muted">{turn.delivery === 'unknown' ? 'Audio delivery unverified' : 'Interrupted · delivery uncertain'}</small>}
      </li>)}
      {!session.transcript.length && <li className="empty">Your conversation will appear here once the assistant receives your first turn.</li>}
    </ol>
  </section>;
}

export function Facts({ session }: { session: SessionStatus; token?: string; editable?: boolean }) {
  return <section className="panel facts" aria-labelledby="facts-title">
    <div className="section-title"><h2 id="facts-title">Your case details</h2><span className="badge">{Object.values(session.conversation.fields).filter(f => f.state === 'confirmed').length} confirmed</span></div>
    <p className="muted small">Only details you explicitly confirm are marked confirmed.</p>
    {!Object.keys(session.conversation.fields).length && <p className="empty">Details will appear as you share them.</p>}
    {Object.entries(session.conversation.fields).map(([name, fact]) => <div className="fact" key={name}>
      <div className="fact-heading"><strong>{fieldLabels[name] ?? name}</strong><span className={'badge ' + fact.state}>{fact.state === 'confirmed' ? '✓ Confirmed' : '○ Unconfirmed'}</span></div>
      <p dir="auto">{fact.value}</p>
    </div>)}
    <div className="detail-row"><span>Understanding</span><strong>{session.conversation.confidence.overall_band}</strong></div>
    <details><summary>Why this status?</summary><p className="small muted">{session.conversation.confidence.reason_codes.map(code => code.toLowerCase().replaceAll('_', ' ')).join('; ')}.</p></details>
  </section>;
}
