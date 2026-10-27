import '@angular/compiler';
import axios from 'axios';
import type { ChangeDetectorRef, NgZone } from '@angular/core';
import type { Router } from '@angular/router';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { DashboardComponent } from './dashboard/dashboard.component';
import { LoginComponent } from './login/login.component';
import { AuthService } from './services/auth.service';
import { TasksService } from './services/tasks.service';

vi.mock('axios', () => ({ default: { get: vi.fn(), post: vi.fn() } }));

const storage = new Map<string, string>();
const getItem = vi.fn((key: string) => storage.get(key) ?? null);
const setItem = vi.fn((key: string, value: string) => storage.set(key, value));
const removeItem = vi.fn((key: string) => storage.delete(key));

describe('Authentication and task flow', () => {
  beforeEach(() => {
    storage.clear();
    getItem.mockClear();
    setItem.mockClear();
    removeItem.mockClear();
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: { getItem, setItem, removeItem }
    });
    vi.mocked(axios.get).mockReset();
    vi.mocked(axios.post).mockReset();
  });

  it('logs in, stores the session, loads tasks and shows the active task', async () => {
    const router = { navigate: vi.fn().mockResolvedValue(true) };
    const authService = new AuthService();
    const login = new LoginComponent(router as unknown as Router, authService);
    login.username = 'student';
    login.password = 'Workshop123!';
    vi.mocked(axios.post).mockResolvedValue({
      data: { token: 'test-token', user: { username: 'student' } }
    } as never);
    vi.mocked(axios.get).mockResolvedValue({
      data: [{ id: 7, status: 'TODO', priority: 'HIGH', owner: 'student', title: 'Local task' }]
    } as never);

    await login.login();

    const zone = { run: (callback: () => void) => callback() };
    const dashboard = new DashboardComponent(
      router as unknown as Router,
      { detectChanges: vi.fn() } as unknown as ChangeDetectorRef,
      zone as unknown as NgZone,
      authService,
      new TasksService()
    );
    await dashboard.ngOnInit();

    expect(storage.get('workshop_token')).toBe('test-token');
    expect(router.navigate).toHaveBeenCalledWith(['/dashboard']);
    expect(axios.get).toHaveBeenCalledWith(
      'http://localhost:8000/api/tasks?owner=student',
      { headers: { Authorization: 'Bearer test-token' } }
    );
    expect(dashboard.visibleTasks.map((task) => task.title)).toEqual(['Local task']);
    expect(dashboard.loading).toBe(false);
  });
});