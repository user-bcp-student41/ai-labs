import { Injectable } from '@angular/core';
import axios from 'axios';
import { environment } from '../../environments/environment';
import { Task } from '../models';

@Injectable({ providedIn: 'root' })
export class TasksService {
  async getTasks(owner: string, token: string): Promise<Task[]> {
    const response = await axios.get<Task[]>(`${environment.tasksUrl}?owner=${owner}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    return response.data;
  }
}