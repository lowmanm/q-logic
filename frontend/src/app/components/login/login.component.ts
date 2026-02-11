import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';

import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="login-container">
      <div class="login-card">
        <h1>Q-Logic</h1>
        <p class="subtitle">Dynamic Schema Orchestration</p>

        <form (ngSubmit)="onSubmit()" class="login-form">
          <div class="field">
            <label for="email">Email</label>
            <input
              id="email"
              type="email"
              [(ngModel)]="email"
              name="email"
              placeholder="you{'@'}company.com"
              required
              autocomplete="email"
            />
          </div>

          <div class="field">
            <label for="password">Password</label>
            <input
              id="password"
              type="password"
              [(ngModel)]="password"
              name="password"
              placeholder="Password"
              required
              autocomplete="current-password"
            />
          </div>

          @if (error) {
            <div class="error">{{ error }}</div>
          }

          <button type="submit" [disabled]="loading">
            {{ loading ? 'Signing in...' : 'Sign In' }}
          </button>
        </form>
      </div>
    </div>
  `,
  styles: [
    `
      .login-container {
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 80vh;
      }
      .login-card {
        background: #fff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 2rem;
        width: 100%;
        max-width: 400px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
      }
      h1 {
        margin: 0 0 0.25rem;
        font-size: 1.5rem;
      }
      .subtitle {
        color: #666;
        margin: 0 0 1.5rem;
        font-size: 0.9rem;
      }
      .field {
        margin-bottom: 1rem;
      }
      label {
        display: block;
        margin-bottom: 0.25rem;
        font-weight: 500;
        font-size: 0.875rem;
      }
      input {
        width: 100%;
        padding: 0.5rem;
        border: 1px solid #ccc;
        border-radius: 4px;
        font-size: 1rem;
        box-sizing: border-box;
      }
      button {
        width: 100%;
        padding: 0.65rem;
        background: #1a73e8;
        color: #fff;
        border: none;
        border-radius: 4px;
        font-size: 1rem;
        cursor: pointer;
        margin-top: 0.5rem;
      }
      button:disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      .error {
        color: #d32f2f;
        background: #fdecea;
        padding: 0.5rem;
        border-radius: 4px;
        font-size: 0.875rem;
        margin-bottom: 0.5rem;
      }
    `,
  ],
})
export class LoginComponent {
  email = '';
  password = '';
  error = '';
  loading = false;

  constructor(private auth: AuthService, private router: Router) {
    if (auth.isAuthenticated) {
      this.router.navigate(['/dashboard']);
    }
  }

  onSubmit(): void {
    this.error = '';
    this.loading = true;

    this.auth.login({ email: this.email, password: this.password }).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/dashboard']);
      },
      error: (err) => {
        this.loading = false;
        this.error =
          err.error?.detail || 'Login failed. Check your credentials.';
      },
    });
  }
}
