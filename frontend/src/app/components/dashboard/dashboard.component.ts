import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription, interval, switchMap, startWith } from 'rxjs';

import { ApiService } from '../../services/api.service';
import {
  TeamAHT,
  AgentStates,
  LeaderboardEntry,
  ProjectQueueStats,
} from '../../models/workspace.models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit, OnDestroy {
  teamAHT: TeamAHT | null = null;
  agentStates: AgentStates | null = null;
  leaderboard: LeaderboardEntry[] = [];
  queueStats: ProjectQueueStats[] = [];
  isLoading = true;

  private pollSub: Subscription | null = null;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    // Poll every 10 seconds
    this.pollSub = interval(10_000)
      .pipe(startWith(0))
      .subscribe(() => this.refresh());
  }

  ngOnDestroy(): void {
    this.pollSub?.unsubscribe();
  }

  refresh(): void {
    this.api.getTeamAHT().subscribe((r) => (this.teamAHT = r));
    this.api.getAgentStates().subscribe((r) => (this.agentStates = r));
    this.api.getLeaderboard().subscribe((r) => (this.leaderboard = r));
    this.api.getAllQueueStats().subscribe((r) => {
      this.queueStats = r;
      this.isLoading = false;
    });
  }

  formatSeconds(seconds: number): string {
    if (!seconds) return '0m 0s';
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  }

  stateLabel(state: string): string {
    const map: Record<string, string> = {
      available: 'Available',
      in_task: 'In Task',
      break: 'Break',
      wrap_up: 'Wrap-up',
    };
    return map[state] || state;
  }

  stateBadgeClass(state: string): string {
    const map: Record<string, string> = {
      available: 'badge-available',
      in_task: 'badge-in-task',
      break: 'badge-break',
      wrap_up: 'badge-wrap-up',
    };
    return 'badge ' + (map[state] || '');
  }

  queueCompletionPct(q: ProjectQueueStats): number {
    if (!q.total) return 0;
    return Math.round((q.completed / q.total) * 100);
  }
}
