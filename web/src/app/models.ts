export interface UserPreferences {
  theme: string;
  showTips: boolean;
  compact: boolean;
}

export interface LoginUser {
  username?: string;
  displayName?: string;
  role?: string;
}

export interface LoginResponse {
  token?: string;
  expiresIn?: number;
  user: LoginUser;
}

export interface TaskLabelInput {
  priority?: string;
  owner?: string;
}

export interface Task extends TaskLabelInput {
  id?: number | string;
  status?: string;
  label?: string;
  title?: string;
  description?: string;
}