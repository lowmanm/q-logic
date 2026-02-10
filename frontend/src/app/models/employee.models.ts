export type EmployeeState = 'available' | 'in_task' | 'break' | 'wrap_up';

export interface Employee {
  id: string;
  name: string;
  email: string;
  current_state: EmployeeState;
  created_at: string;
}

export interface EmployeeCreate {
  name: string;
  email: string;
}

export interface TaskLog {
  id: string;
  employee_id: string;
  source_id: string;
  record_id: string;
  started_at: string;
  completed_at: string | null;
}

export interface AHTMetric {
  employee_id: string;
  employee_name: string;
  source_id: string | null;
  project_name: string | null;
  average_handle_time_seconds: number;
  task_count: number;
}
