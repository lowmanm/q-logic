import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';
import { ProjectInfo, TaskRecord } from '../../models/workspace.models';

@Component({
  selector: 'app-agent-workspace',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './agent-workspace.component.html',
  styleUrl: './agent-workspace.component.css',
})
export class AgentWorkspaceComponent implements OnInit {
  projects: ProjectInfo[] = [];
  selectedProject: ProjectInfo | null = null;
  records: TaskRecord[] = [];
  selectedRecord: TaskRecord | null = null;
  isLoading = false;
  error = '';

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.loadProjects();
  }

  loadProjects(): void {
    this.isLoading = true;
    this.api.getProjects().subscribe({
      next: (projects) => {
        this.projects = projects;
        this.isLoading = false;
      },
      error: () => {
        this.error = 'Failed to load projects.';
        this.isLoading = false;
      },
    });
  }

  selectProject(project: ProjectInfo): void {
    this.selectedProject = project;
    this.selectedRecord = null;
    this.loadRecords();
  }

  loadRecords(): void {
    if (!this.selectedProject) return;
    this.isLoading = true;
    this.api.getRecords(this.selectedProject.source_id).subscribe({
      next: (records) => {
        this.records = records;
        this.isLoading = false;
      },
      error: () => {
        this.error = 'Failed to load records.';
        this.isLoading = false;
      },
    });
  }

  selectRecord(record: TaskRecord): void {
    this.selectedRecord = record;
  }

  openScreenPop(): void {
    if (this.selectedRecord?.screen_pop_url) {
      window.open(this.selectedRecord.screen_pop_url, '_blank');
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
    this.records = [];
    this.selectedRecord = null;
  }
}
