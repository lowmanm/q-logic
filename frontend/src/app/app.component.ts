import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <nav>
      <ul>
        <li><a routerLink="/dashboard" routerLinkActive="active">Dashboard</a></li>
        <li><a routerLink="/designer" routerLinkActive="active">Schema Designer</a></li>
        <li><a routerLink="/workspace" routerLinkActive="active">Agent Workspace</a></li>
        <li><a routerLink="/employees" routerLinkActive="active">Employee Tracker</a></li>
      </ul>
    </nav>
    <main class="container">
      <router-outlet />
    </main>
  `,
})
export class AppComponent {}
