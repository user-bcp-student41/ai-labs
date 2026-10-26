import '@angular/compiler';
import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { TasksService } from './tasks.service';

vi.mock('axios', () => ({ default: { get: vi.fn() } }));

describe('TasksService', () => {
  let service: TasksService;

  beforeEach(() => {
    vi.mocked(axios.get).mockReset();
    service = new TasksService();
  });

  it('requests tasks with the owner query and bearer token', async () => {
    const tasks = [{ id: 1, status: 'TODO', priority: 'HIGH', owner: 'student' }];
    vi.mocked(axios.get).mockResolvedValue({ data: tasks } as never);

    await expect(service.getTasks('student', 'test-token')).resolves.toBe(tasks);

    expect(axios.get).toHaveBeenCalledWith(
      'http://localhost:8000/api/tasks?owner=student',
      { headers: { Authorization: 'Bearer test-token' } }
    );
  });
});