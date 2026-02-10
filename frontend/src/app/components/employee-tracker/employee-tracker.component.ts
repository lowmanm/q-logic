import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';

import { ApiService } from '../../services/api.service';
import { Employee, EmployeeState, AHTMetric } from '../../models/employee.models';

@Component({
  selector: 'app-employee-tracker',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './employee-tracker.component.html',
  styleUrl: './employee-tracker.component.css',
})
export class EmployeeTrackerComponent implements OnInit {
  employees: Employee[] = [];
  newEmployeeForm: FormGroup;
  showCreateForm = false;
  isLoading = false;
  error = '';
  ahtMetrics: Map<string, AHTMetric> = new Map();

  states: EmployeeState[] = ['available', 'in_task', 'break', 'wrap_up'];

  constructor(
    private api: ApiService,
    private fb: FormBuilder
  ) {
    this.newEmployeeForm = this.fb.group({
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
    });
  }

  ngOnInit(): void {
    this.loadEmployees();
  }

  loadEmployees(): void {
    this.isLoading = true;
    this.api.getEmployees().subscribe({
      next: (employees) => {
        this.employees = employees;
        this.isLoading = false;
        // Load AHT for each employee
        for (const emp of employees) {
          this.loadAHT(emp.id);
        }
      },
      error: () => {
        this.error = 'Failed to load employees.';
        this.isLoading = false;
      },
    });
  }

  createEmployee(): void {
    if (this.newEmployeeForm.invalid) return;

    this.api
      .createEmployee({
        name: this.newEmployeeForm.get('name')!.value,
        email: this.newEmployeeForm.get('email')!.value,
      })
      .subscribe({
        next: () => {
          this.showCreateForm = false;
          this.newEmployeeForm.reset();
          this.loadEmployees();
        },
        error: (err) => {
          this.error = err.error?.detail || 'Failed to create employee.';
        },
      });
  }

  changeState(employeeId: string, newState: EmployeeState): void {
    this.api.changeState(employeeId, newState).subscribe({
      next: (updated) => {
        const idx = this.employees.findIndex((e) => e.id === employeeId);
        if (idx >= 0) this.employees[idx] = updated;
      },
      error: (err) => {
        this.error = err.error?.detail || 'Failed to change state.';
      },
    });
  }

  loadAHT(employeeId: string): void {
    this.api.getAHT(employeeId).subscribe({
      next: (metric) => this.ahtMetrics.set(employeeId, metric),
      error: () => {
        // No tasks yet — ignore
      },
    });
  }

  getAHT(employeeId: string): AHTMetric | undefined {
    return this.ahtMetrics.get(employeeId);
  }

  formatSeconds(seconds: number): string {
    if (!seconds) return '--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.round(seconds % 60);
    return `${mins}m ${secs}s`;
  }

  getStateBadgeClass(state: EmployeeState): string {
    const map: Record<EmployeeState, string> = {
      available: 'badge-available',
      in_task: 'badge-in-task',
      break: 'badge-break',
      wrap_up: 'badge-wrap-up',
    };
    return 'badge ' + map[state];
  }

  stateLabel(state: EmployeeState): string {
    const map: Record<EmployeeState, string> = {
      available: 'Available',
      in_task: 'In Task',
      break: 'Break',
      wrap_up: 'Wrap-up',
    };
    return map[state];
  }
}
