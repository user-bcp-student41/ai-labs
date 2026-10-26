import '@angular/compiler';
import axios from 'axios';
import type { ChangeDetectorRef, NgZone } from '@angular/core';
import type { Router } from '@angular/router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthService } from '../services/auth.service';
import { TasksService } from '../services/tasks.service';
import { DashboardComponent } from './dashboard.component';

vi.mock('axios', () => ({ default: { get: vi.fn() } }));

const storage = new Map<string, string>();
const getItem = vi.fn((key: string) => storage.get(key) ?? null);
const setItem = vi.fn((key: string, value: string) => storage.set(key, value));
const removeItem = vi.fn((key: string) => storage.delete(key));

describe('DashboardComponent characterization', () => {
  let router: { navigate: ReturnType<typeof vi.fn> };
  let detectChanges: ReturnType<typeof vi.fn>;
  let component: DashboardComponent;

  function createComponent(): DashboardComponent {
    const zone = { run: (callback: () => void) => callback() };
    return new DashboardComponent(
      router as unknown as Router,
      { detectChanges } as unknown as ChangeDetectorRef,
      zone as unknown as NgZone,
      new AuthService(),
      new TasksService()
    );
  }

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
    detectChanges = vi.fn();
    vi.mocked(axios.get).mockReset();
    component = createComponent();
  });

  it('redirects to login when no token is stored', async () => {
    await component.ngOnInit();

    expect(router.navigate).toHaveBeenCalledWith(['/login']);
    expect(axios.get).not.toHaveBeenCalled();
  });

  it('maps known task statuses to their display labels', () => {
    expect(component.statusLabel('IN_PROGRESS')).toBe('En progreso');
  });

  it('preserves unknown task statuses as their display label', () => {
    expect(component.statusLabel('CUSTOM_STATUS')).toBe('CUSTOM_STATUS');
  });

  it('loads tasks with the bearer token, filters archived tasks and sorts visible tasks', async () => {
    storage.set('workshop_token', 'test-token');
    storage.set('workshop_user', JSON.stringify({ username: 'student' }));
    const tasks = [
      { id: 1, status: 'TODO', priority: 'LOW', owner: 'student' },
      { id: 2, status: 'ARCHIVED', priority: 'HIGH', owner: 'student' },
      { id: 3, status: 'IN_PROGRESS', priority: 'HIGH', owner: 'student' }
    ];
    vi.mocked(axios.get).mockResolvedValue({ data: tasks } as never);

    await component.ngOnInit();

    expect(axios.get).toHaveBeenCalledWith(
      'http://localhost:8000/api/tasks?owner=student',
      { headers: { Authorization: 'Bearer test-token' } }
    );
    expect(component.tasks).toBe(tasks);
    expect(component.visibleTasks.map((task) => task.id)).toEqual([1, 3]);
    expect(component.visibleTasks[0].label).toBe('LOW · STUDENT');
    expect(component.loading).toBe(false);
    expect(detectChanges).toHaveBeenCalledOnce();
  });

  it('shows the backend error when task loading fails', async () => {
    storage.set('workshop_token', 'test-token');
    storage.set('workshop_user', JSON.stringify({ username: 'student' }));
    vi.mocked(axios.get).mockRejectedValue({ response: { data: { detail: 'Unavailable' } } });

    await component.ngOnInit();

    expect(component.error).toBe('Unavailable');
    expect(component.loading).toBe(false);
    expect(detectChanges).toHaveBeenCalledOnce();
  });

  it('keeps the session and displays an invalid-token error without redirecting', async () => {
    storage.set('workshop_token', 'invalid-token');
    storage.set('workshop_user', JSON.stringify({ username: 'student' }));
    vi.mocked(axios.get).mockRejectedValue({
      response: { status: 401, data: { detail: 'Token inválido' } }
    });

    await component.ngOnInit();

    expect(component.error).toBe('Token inválido');
    expect(storage.get('workshop_token')).toBe('invalid-token');
    expect(router.navigate).not.toHaveBeenCalled();
    expect(component.loading).toBe(false);
  });

  it('displays an adapter timeout error and keeps the current session', async () => {
    storage.set('workshop_token', 'test-token');
    storage.set('workshop_user', JSON.stringify({ username: 'student' }));
    vi.mocked(axios.get).mockRejectedValue(new Error('timeout of 10000ms exceeded'));

    await component.ngOnInit();

    expect(component.error).toBe('timeout of 10000ms exceeded');
    expect(storage.get('workshop_token')).toBe('test-token');
    expect(router.navigate).not.toHaveBeenCalled();
    expect(component.loading).toBe(false);
  });

  it('uses a readable fallback for unknown task errors', async () => {
    storage.set('workshop_token', 'test-token');
    storage.set('workshop_user', JSON.stringify({ username: 'student' }));
    vi.mocked(axios.get).mockRejectedValue(null);

    await component.ngOnInit();

    expect(component.error).toBe('No se pudo cargar el dashboard');
  });

  it('removes the stored token and user and navigates to login on logout', async () => {
    storage.set('workshop_token', 'test-token');
    storage.set('workshop_user', '{"username":"student"}');
    storage.set('workshop_preferences', '{"theme":"light"}');

    await component.logout();

    expect(removeItem).toHaveBeenCalledWith('workshop_token');
    expect(removeItem).toHaveBeenCalledWith('workshop_user');
    expect(storage.has('workshop_token')).toBe(false);
    expect(storage.has('workshop_user')).toBe(false);
    expect(storage.has('workshop_preferences')).toBe(true);
    expect(router.navigate).toHaveBeenCalledWith(['/login']);
  });
});