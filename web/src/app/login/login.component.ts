import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { UserPreferences } from '../models';
import { AuthService } from '../services/auth.service';
import { getApiErrorMessage } from '../utils/api-error';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css'
})
export class LoginComponent {
  username = '';
  password = '';
  busy = false;
  message = '';
  preferences: UserPreferences;

  constructor(private router: Router, private authService: AuthService) {
    this.preferences = this.authService.getPreferences();
  }

  async login(): Promise<void> {
    this.message = '';
    if (typeof this.username !== 'string' || this.username.trim() === '') {
      this.message = 'Ingrese un usuario.';
      return;
    }
    if (typeof this.password !== 'string' || this.password.trim() === '') {
      this.message = 'Ingrese una contraseña.';
      return;
    }

    this.busy = true;
    try {
      const response = await this.authService.login(this.username, this.password, this.preferences);
      if (!response.token) {
        this.message = 'El backend respondió sin token.';
        return;
      }

      await this.router.navigate(['/dashboard']);
    } catch (error: unknown) {
      const backendMessage = getApiErrorMessage(error, 'message', 'Error desconocido');
      this.message = `No se pudo autenticar a ${this.username}.\n${backendMessage}`;
      console.error(error);
    } finally {
      this.busy = false;
    }
  }
}
