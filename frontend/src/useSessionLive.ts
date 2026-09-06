import { useEffect, useState } from 'react';
import { watchSession, type SessionStatus } from './api';

export function useSessionLive(id: string | undefined, token: string | undefined) {
  const [snapshot, setSnapshot] = useState<SessionStatus | null>(null);
  const [reconnecting, setReconnecting] = useState(false);
  // React effect cleanup owns both the network stream and reconnect timer.
  // https://react.dev/reference/react/useEffect
  useEffect(() => {
    setSnapshot(null);
    if (!id || !token) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function connect() {
      try {
        await watchSession(id!, token!, controller.signal, state => {
          setSnapshot(state); setReconnecting(false);
        });
      } catch {
        if (!controller.signal.aborted) setReconnecting(true);
      }
      if (!controller.signal.aborted) timer = setTimeout(() => void connect(), 1500);
    }
    void connect();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [id, token]);
  return { snapshot, reconnecting };
}
