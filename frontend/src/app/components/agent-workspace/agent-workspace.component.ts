import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';
import { ProjectInfo, NextTaskResponse, QueueStatsResponse } from '../../models/workspace.models';
import { Employee } from '../../models/employee.models';

@Component({
  selector: 'app-agent-workspace',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './agent-workspace.component.html',
  styleUrl: './agent-workspace.component.css',
})
export class AgentWorkspaceComponent implements OnInit {
  // Setup
  projects: ProjectInfo[] = [];
  employees: Employee[] = [];
  selectedProject: ProjectInfo | null = null;
  selectedEmployeeId = '';

  // Queue state
  queueStats: QueueStatsResponse | null = null;
  currentTask: NextTaskResponse | null = null;

  // UI state
  isLoading = false;
  error = '';
  taskCompleted = false;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.api.getProjects().subscribe({
      next: (p) => (this.projects = p),
      error: () => (this.error = 'Failed to load projects.'),
    });
    this.api.getEmployees().subscribe({
      next: (e) => (this.employees = e),
      error: () => (this.error = 'Failed to load employees.'),
    });
  }

  selectProject(project: ProjectInfo): void {
    this.selectedProject = project;
    this.currentTask = null;
    this.taskCompleted = false;
    this.refreshQueueStats();
  }

  refreshQueueStats(): void {
    if (!this.selectedProject) return;
    this.api.getQueueStats(this.selectedProject.source_id).subscribe({
      next: (stats) => (this.queueStats = stats),
    });
  }

  getNextTask(): void {
    if (!this.selectedProject || !this.selectedEmployeeId) return;

    this.isLoading = true;
    this.error = '';
    this.taskCompleted = false;

    this.api
      .getNextTask(this.selectedProject.source_id, this.selectedEmployeeId)
      .subscribe({
        next: (task) => {
          this.currentTask = task;
          this.isLoading = false;
          this.refreshQueueStats();
        },
        error: (err) => {
          this.error = err.error?.detail || 'No more records in queue.';
          this.currentTask = null;
          this.isLoading = false;
        },
      });
  }

  completeTask(): void {
    if (!this.currentTask) return;
    this.isLoading = true;

    this.api.completeQueueItem(this.currentTask.queue_id).subscribe({
      next: () => {
        this.taskCompleted = true;
        this.isLoading = false;
        this.refreshQueueStats();
      },
      error: (err) => {
        this.error = err.error?.detail || 'Failed to complete task.';
        this.isLoading = false;
      },
    });
  }

  skipTask(): void {
    if (!this.currentTask) return;
    this.isLoading = true;

    this.api.skipQueueItem(this.currentTask.queue_id).subscribe({
      next: () => {
        this.currentTask = null;
        this.isLoading = false;
        this.refreshQueueStats();
        // Auto-pull next
        this.getNextTask();
      },
      error: (err) => {
        this.error = err.error?.detail || 'Failed to skip task.';
        this.isLoading = false;
      },
    });
  }

  openScreenPop(): void {
    if (this.currentTask?.screen_pop_url) {
      window.open(this.currentTask.screen_pop_url, '_blank');
    }
  }

  getDisplayColumns(): { physical: string; display: string }[] {
    if (!this.selectedProject) return [];
    return this.selectedProject.columns.map((c) => ({
      physical: c.physical_name,
      display: c.display_name,
    }));
  }

  backToProjects(): void {
    this.selectedProject = null;
    this.currentTask = null;
    this.queueStats = null;
    this.taskCompleted = false;
    this.error = '';
  }
}
