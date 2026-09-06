import { useCallback, useEffect, useRef, useState } from 'react';
import { api, createSession, endSession, startAgent, type Language, type Rtc, type SessionCreated } from './api';
import { joinMedia, type MediaSession } from './media';

export function useVoiceSession() {
  const [session, setSession] = useState<SessionCreated | null>(null);
  const [state, setState] = useState('idle');
  const [error, setError] = useState('');
  const [members, setMembers] = useState<number[]>([]);
  const [muted, setMuted] = useState(false);
  const current = useRef<SessionCreated | null>(null);
  const media = useRef<MediaSession | null>(null);
  const controller = useRef<AbortController | null>(null);
  const busy = useRef(false);
  const epoch = useRef(0);

  const end = useCallback(async () => {
    epoch.current++; controller.current?.abort(); busy.current = false;
    const active = current.current;
    current.current = null;
    setState('ending');
    await media.current?.close(); media.current = null;
    if (active) {
      try {
        const result = await endSession(active);
        setState(result.status === 'ended' ? 'ended' : 'cleanup_pending');
      } catch { setState('cleanup_pending'); setError('Local audio has stopped. Server cleanup is pending.'); }
    } else setState('ended');
  }, []);

  const start = useCallback(async (language: Language) => {
    if (busy.current) return;
    busy.current = true;
    const generation = ++epoch.current;
    const abort = new AbortController();
    controller.current = abort;
    setError(''); setMuted(false); setSession(null); setState('connecting');
    let created: SessionCreated | null = null;
    try {
      created = await createSession(language);
      if (generation !== epoch.current) { await endSession(created); return; }
      current.current = created; setSession(created);
      if (created.rtc) {
        setState('requesting-permission');
        media.current = await joinMedia(created.rtc, abort.signal, setMembers,
          value => { if (generation === epoch.current) setState(value.toLowerCase()); },
          async () => (await api<{ rtc: Rtc }>('/sessions/' + created!.session_id + '/token', created!.caller_capability, {})).rtc);
        if (generation !== epoch.current) { await media.current.close(); await endSession(created); return; }
        await startAgent(created);
      }
      if (generation === epoch.current) setState('waiting_for_audio');
    } catch (cause) {
      abort.abort();
      if (created) await endSession(created).catch(() => undefined);
      if (generation === epoch.current) {
        busy.current = false; current.current = null;
        setState('error'); setError(cause instanceof Error ? cause.message : 'Could not start the session.');
      }
    }
  }, []);

  const toggleMute = useCallback(async () => {
    await media.current?.mute(!muted); setMuted(!muted);
  }, [muted]);

  useEffect(() => () => {
    epoch.current++; controller.current?.abort();
    void media.current?.close();
    if (current.current) void endSession(current.current).catch(() => undefined);
  }, []);
  return { session, state, error, members, start, end, muted, toggleMute };
}
