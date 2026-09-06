import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, parseSseFrame } from './api';

afterEach(() => vi.unstubAllGlobals());
describe('API boundary', () => {
  it('sends the voice session request without caller text', async () => {
    const fetch = vi.fn().mockResolvedValue(new Response(JSON.stringify({ session_id: 'voice-session' })));
    vi.stubGlobal('fetch', fetch);
    expect(await api('/sessions', undefined, { requested_language: 'ta-IN' })).toEqual({ session_id: 'voice-session' });
    expect(fetch.mock.calls[0][1].body).not.toContain('text');
  });
  it('returns a safe API error with a correlation reference', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ error: { message: 'Session ended.', correlation_id: 'abc' } }), { status: 409 })));
    await expect(api('/sessions/example')).rejects.toThrow('Session ended.');
  });
  it('parses snapshots and ignores heartbeat comments', () => {
    expect(parseSseFrame(': heartbeat')).toBeNull();
    expect(parseSseFrame('event: snapshot\nid: 3\ndata: {"status":"collecting"}')).toEqual({ status: 'collecting' });
  });
});
