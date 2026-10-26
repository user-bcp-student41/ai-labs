import '@angular/compiler';
import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthService } from './auth.service';

vi.mock('axios', () => ({ default: { post: vi.fn() } }));

const storage = new Map<string, string>();
const getItem = vi.fn((key: string) => storage.get(key) ?? null);
const setItem = vi.fn((key: string, value: string) => storage.set(key, value));
const removeItem = vi.fn((key: string) => storage.delete(key));

describe('AuthService', () => {
  let service: AuthService;

  beforeEach(() => {
    storage.clear();
    getItem.mockClear();
    setItem.mockClear();
    removeItem.mockClear();
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: { getItem, setItem, removeItem }
    });
    vi.mocked(axios.post).mockReset();
    service = new AuthService();
  });

  it('merges saved preferences with defaults', () => {
    storage.set('workshop_preferences', '{"theme":"dark"}');

    expect(service.getPreferences()).toEqual({ theme: 'dark', showTips: true, compact: false });
  });

  it('uses defaults and logs when saved preferences are malformed', () => {
    storage.set('workshop_preferences', '{invalid');
    vi.spyOn(console, 'log').mockImplementation(() => undefined);

    expect(service.getPreferences()).toEqual({ theme: 'light', showTips: true, compact: false });
    expect(console.log).toHaveBeenCalledOnce();
  });

  it('posts login and stores token, user and preferences when a token is returned', async () => {
    const preferences = { theme: 'dark', showTips: false, compact: true };
    vi.mocked(axios.post).mockResolvedValue({
      data: { token: 'test-token', user: { username: 'student' } }
    } as never);

    await service.login('student', 'Workshop123!', preferences);

    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:8080/auth/login',
      { username: 'student', password: 'Workshop123!', client: 'angular-workshop' },
      { timeout: 5000 }
    );
    expect(storage.get('workshop_token')).toBe('test-token');
    expect(storage.get('workshop_user')).toBe('{"username":"student"}');
    expect(storage.get('workshop_preferences')).toBe(JSON.stringify(preferences));
  });

  it('does not store a session when the response has no token', async () => {
    vi.mocked(axios.post).mockResolvedValue({ data: { user: { username: 'student' } } } as never);

    await service.login('student', 'Workshop123!', { theme: 'light', showTips: true, compact: false });

    expect(setItem).not.toHaveBeenCalled();
  });

  it('reads user and token and removes only session values on logout', () => {
    storage.set('workshop_token', 'test-token');
    storage.set('workshop_user', '{"username":"student"}');
    storage.set('workshop_preferences', '{"theme":"dark"}');

    expect(service.getToken()).toBe('test-token');
    expect(service.getUser()).toEqual({ username: 'student' });
    service.logout();

    expect(storage.has('workshop_token')).toBe(false);
    expect(storage.has('workshop_user')).toBe(false);
    expect(storage.has('workshop_preferences')).toBe(true);
  });
});