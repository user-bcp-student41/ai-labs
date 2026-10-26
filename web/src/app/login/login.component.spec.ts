import '@angular/compiler';
import { readFileSync } from 'node:fs';
import axios from 'axios';
import type { Router } from '@angular/router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthService } from '../services/auth.service';
import { LoginComponent } from './login.component';

vi.mock('axios', () => ({ default: { post: vi.fn() } }));

const storage = new Map<string, string>();
const getItem = vi.fn((key: string) => storage.get(key) ?? null);
const setItem = vi.fn((key: string, value: string) => storage.set(key, value));
const removeItem = vi.fn((key: string) => storage.delete(key));

function normalizedMessage(message: string): string {
  return message.replace(/<\/?strong>/g, '').replace(/<br\s*\/?\s*>/g, '\n');
}

describe('LoginComponent characterization', () => {
  let router: { navigate: ReturnType<typeof vi.fn> };
  let component: LoginComponent;

  beforeEach(() => {
    storage.clear();
    getItem.mockClear();
    setItem.mockClear();
    removeItem.mockClear();
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: { getItem, setItem, removeItem }
    });
    router = { navigate: vi.fn().mockResolvedValue(true) };
    vi.mocked(axios.post).mockReset();
    component = new LoginComponent(router as unknown as Router, new AuthService());
  });

  it('shows the username validation message without making a request', async () => {
    await component.login();

    expect(normalizedMessage(component.message)).toBe('Ingrese un usuario.');
    expect(axios.post).not.toHaveBeenCalled();
  });

  it('shows the password validation message without making a request', async () => {
    component.username = 'student';

    await component.login();

    expect(normalizedMessage(component.message)).toBe('Ingrese una contraseña.');
    expect(axios.post).not.toHaveBeenCalled();
  });

  it('posts login credentials, persists the response and navigates to dashboard', async () => {
    component.username = 'student';
    component.password = 'Workshop123!';
    vi.mocked(axios.post).mockResolvedValue({
      data: { token: 'test-token', user: { username: 'student' } }
    } as never);

    await component.login();

    expect(axios.post).toHaveBeenCalledWith(
      'http://localhost:8080/auth/login',
      { username: 'student', password: 'Workshop123!', client: 'angular-workshop' },
      { timeout: 5000 }
    );
    expect(setItem).toHaveBeenCalledWith('workshop_token', 'test-token');
    expect(setItem).toHaveBeenCalledWith('workshop_user', '{"username":"student"}');
    expect(setItem).toHaveBeenCalledWith('workshop_preferences', JSON.stringify(component.preferences));
    expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
    expect(component.busy).toBe(false);
  });

  it('shows a readable backend error and resets the busy state', async () => {
    component.username = 'student';
    component.password = 'invalid';
    vi.mocked(axios.post).mockRejectedValue({
      response: { data: { message: 'Invalid credentials' } }
    });
    vi.spyOn(console, 'error').mockImplementation(() => undefined);

    await component.login();

    expect(normalizedMessage(component.message)).toBe('No se pudo autenticar a student.\nInvalid credentials');
    expect(component.busy).toBe(false);
  });

  it('shows the network error when the authentication service is unavailable', async () => {
    component.username = 'student';
    component.password = 'Workshop123!';
    vi.mocked(axios.post).mockRejectedValue(new Error('Network Error'));
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined);

    await component.login();

    expect(normalizedMessage(component.message)).toBe('No se pudo autenticar a student.\nNetwork Error');
    expect(component.busy).toBe(false);
    expect(storage.has('workshop_token')).toBe(false);
    consoleError.mockRestore();
  });

  it('shows the configured request timeout error', async () => {
    component.username = 'student';
    component.password = 'Workshop123!';
    vi.mocked(axios.post).mockRejectedValue(new Error('timeout of 5000ms exceeded'));
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => undefined);

    await component.login();

    expect(normalizedMessage(component.message))
      .toBe('No se pudo autenticar a student.\ntimeout of 5000ms exceeded');
    expect(component.busy).toBe(false);
    consoleError.mockRestore();
  });

  it('shows a response-without-token message', async () => {
    component.username = 'student';
    component.password = 'Workshop123!';
    vi.mocked(axios.post).mockResolvedValue({ data: {} } as never);

    await component.login();

    expect(normalizedMessage(component.message)).toBe('El backend respondió sin token.');
    expect(router.navigate).not.toHaveBeenCalled();
  });

  it('renders dynamic messages as text instead of HTML', () => {
    const template = readFileSync(new URL('./login.component.html', import.meta.url), 'utf8');

    expect(template).toContain('{{ message }}');
    expect(template).not.toContain('[innerHTML]');
  });
});