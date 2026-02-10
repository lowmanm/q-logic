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
