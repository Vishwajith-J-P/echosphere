import type { IAgoraRTCClient, IMicrophoneAudioTrack } from 'agora-rtc-sdk-ng';
import type { Rtc } from './api';

export interface MediaSession { close: () => Promise<void>; mute: (muted: boolean) => Promise<void> }
export async function joinMedia(rtc: Rtc, signal: AbortSignal,
  onPresence: (uids: number[]) => void, onConnection: (state: string) => void,
  renew: () => Promise<Rtc>, onReady?: () => void): Promise<MediaSession> {
  const { default: AgoraRTC } = await import('agora-rtc-sdk-ng');
  AgoraRTC.setLogLevel(3);
  let microphone: IMicrophoneAudioTrack | undefined;
  let client: IAgoraRTCClient | undefined;
  let closed = false;
  const members = new Set<number>();
  async function close() {
    closed = true;
    microphone?.stop(); microphone?.close();
    client?.removeAllListeners();
    await client?.leave().catch(() => undefined);
    onPresence([]);
  }
  const cancelled = () => { if (signal.aborted || closed) throw new DOMException('Session cancelled', 'AbortError'); };
  const onAbort = () => void close();
  signal.addEventListener('abort', onAbort, { once: true });
  try {
    cancelled();
    microphone = await AgoraRTC.createMicrophoneAudioTrack({ AEC: true, ANS: true, AGC: true });
    cancelled();
    client = AgoraRTC.createClient({ mode: 'rtc', codec: 'vp8' });
    client.on('connection-state-change', state => onConnection(state));
    client.on('user-published', async (user, mediaType) => {
      try {
        if (closed || signal.aborted || mediaType !== 'audio') return;
        await client!.subscribe(user, mediaType);
        if (closed || signal.aborted) return;
        user.audioTrack?.play(); members.add(Number(user.uid)); onPresence([...members]); onReady?.();
      } catch { if (!closed) onConnection('AUDIO_ERROR'); }
    });
    client.on('user-left', user => { members.delete(Number(user.uid)); onPresence([...members]); });
    client.on('user-unpublished', user => { members.delete(Number(user.uid)); onPresence([...members]); });
    client.on('token-privilege-will-expire', () => {
      void renew().then(value => client?.renewToken(value.token)).catch(() => onConnection('TOKEN_ERROR'));
    });
    client.on('token-privilege-did-expire', () => onConnection('TOKEN_ERROR'));
    await client.join(rtc.app_id, rtc.channel, rtc.token, rtc.uid);
    cancelled();
    await client.publish(microphone);
    cancelled();
    return { close: async () => { signal.removeEventListener('abort', onAbort); await close(); },
      mute: async muted => { await microphone?.setMuted(muted); } };
  } catch (error) {
    await close(); signal.removeEventListener('abort', onAbort); throw error;
  }
}
