import { Injectable } from '@angular/core';
import axios from 'axios';
import merge from 'lodash/merge';
import { environment } from '../../environments/environment';
import { LoginResponse, LoginUser, UserPreferences } from '../models';

const STORAGE_KEYS = {
  token: 'workshop_token',
  user: 'workshop_user',
  preferences: 'workshop_preferences'
} as const;

const DEFAULT_PREFERENCES: UserPreferences = {
  theme: 'light',
  showTips: true,
  compact: false
};

const CLIENT_NAME = 'angular-workshop';
const LOGIN_TIMEOUT_MS = 5000;

@Injectable({ providedIn: 'root' })
export class AuthService {
  async login(username: string, password: string, preferences: UserPreferences): Promise<LoginResponse> {
    const response = await axios.post<LoginResponse>(
      environment.authUrl,
      { username, password, client: CLIENT_NAME },
      { timeout: LOGIN_TIMEOUT_MS }
    );

    if (response.data.token) {
      this.saveSession(response.data.token, response.data.user, preferences);
    }

    return response.data;
  }

  getPreferences(): UserPreferences {
    try {
      const savedPreferences = JSON.parse(localStorage.getItem(STORAGE_KEYS.preferences) || '{}') as Partial<UserPreferences>;
      return merge({}, DEFAULT_PREFERENCES, savedPreferences);
    } catch (error) {
      console.log('Preferences could not be loaded', error);
      return { ...DEFAULT_PREFERENCES };
    }
  }

  getToken(): string | null {
    return localStorage.getItem(STORAGE_KEYS.token);
  }

  getUser(): LoginUser {
    return JSON.parse(localStorage.getItem(STORAGE_KEYS.user) || '{}') as LoginUser;
  }

  logout(): void {
    localStorage.removeItem(STORAGE_KEYS.token);
    localStorage.removeItem(STORAGE_KEYS.user);
  }

  private saveSession(token: string, user: LoginUser, preferences: UserPreferences): void {
    localStorage.setItem(STORAGE_KEYS.token, token);
    localStorage.setItem(STORAGE_KEYS.user, JSON.stringify(user));
    localStorage.setItem(STORAGE_KEYS.preferences, JSON.stringify(preferences));
  }
}