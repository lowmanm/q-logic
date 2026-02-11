export interface ColumnInfo {
  physical_name: string;
  display_name: string;
  data_type: string;
  is_unique_id: boolean;
}

export interface ProjectInfo {
  source_id: string;
  project_name: string;
  table_name: string;
  screen_pop_url_template: string | null;
  columns: ColumnInfo[];
}

export interface TaskRecord {
  record: Record<string, unknown>;
  screen_pop_url: string | null;
}

export interface EnqueueResponse {
  source_id: string;
  records_enqueued: number;
}

export interface QueueStatsResponse {
  source_id: string;
  pending: number;
  assigned: number;
  completed: number;
  skipped: number;
  total: number;
}

export interface NextTaskResponse {
  queue_id: string;
  source_id: string;
  record_id: number;
  record: Record<string, unknown>;
  screen_pop_url: string | null;
  queue_depth: number;
}

export interface QueueActionResponse {
  queue_id: string;
  status: string;
}

// Dashboard models
export interface TeamAHT {
  average_handle_time_seconds: number;
  task_count: number;
}

export interface AgentStates {
  available: number;
  in_task: number;
  break: number;
  wrap_up: number;
  total: number;
}

export interface LeaderboardEntry {
  employee_id: string;
  name: string;
  current_state: string;
  task_count: number;
  average_handle_time_seconds: number;
}

export interface ProjectQueueStats {
  source_id: string;
  project_name: string;
  pending: number;
  assigned: number;
  completed: number;
  skipped: number;
  total: number;
}
