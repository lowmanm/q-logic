import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';

import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    @if (auth.isAuthenticated) {
      <nav>
        <ul>
          <li><a routerLink="/dashboard" routerLinkActive="active">Dashboard</a></li>
          @if (auth.hasRole('admin', 'supervisor')) {
            <li><a routerLink="/designer" routerLinkActive="active">Schema Designer</a></li>
          }
          <li><a routerLink="/workspace" routerLinkActive="active">Agent Workspace</a></li>
          @if (auth.hasRole('admin', 'supervisor')) {
            <li><a routerLink="/employees" routerLinkActive="active">Employee Tracker</a></li>
          }
        </ul>
        <div class="user-info">
          <span class="user-name">{{ (auth.user$ | async)?.name }}</span>
          <span class="user-role">{{ (auth.user$ | async)?.role }}</span>
          <button class="logout-btn" (click)="auth.logout()">Logout</button>
        </div>
      </nav>
    }
    <main class="container">
      <router-outlet />
    </main>
  `,
  styles: [
    `
      nav {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 1rem;
      }
      .user-info {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.875rem;
      }
      .user-name {
        font-weight: 500;
      }
      .user-role {
        color: #666;
        text-transform: uppercase;
        font-size: 0.75rem;
      }
      .logout-btn {
        background: none;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 0.25rem 0.5rem;
        cursor: pointer;
        font-size: 0.8rem;
      }
    `,
  ],
})
export class AppComponent {
  constructor(public auth: AuthService) {}
}
