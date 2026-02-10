export interface InferredColumn {
  original_name: string;
  inferred_type: DataType;
  suggested_display_name: string;
  is_primary_key_candidate: boolean;
}

export interface SchemaInferenceResponse {
  filename: string;
  row_count: number;
  columns: InferredColumn[];
}

export type DataType = 'STRING' | 'INTEGER' | 'FLOAT' | 'BOOLEAN' | 'DATE';

export interface FinalizedColumn {
  original_name: string;
  display_name: string;
  data_type: DataType;
  is_unique_id: boolean;
}

export interface ProvisionRequest {
  project_name: string;
  screen_pop_url_template: string | null;
  columns: FinalizedColumn[];
}

export interface ProvisionResponse {
  project_name: string;
  table_name: string;
  source_id: string;
  column_count: number;
}

export interface DataLoadResponse {
  source_id: string;
  rows_loaded: number;
  rows_failed: number;
  errors: string[];
}
