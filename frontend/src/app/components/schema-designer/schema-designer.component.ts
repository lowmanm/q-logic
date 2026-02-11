import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import {
  ReactiveFormsModule,
  FormArray,
  FormBuilder,
  FormGroup,
  Validators,
} from '@angular/forms';

import { ApiService } from '../../services/api.service';
import {
  InferredColumn,
  DataType,
  FinalizedColumn,
  ProvisionResponse,
  DataLoadResponse,
} from '../../models/schema.models';

@Component({
  selector: 'app-schema-designer',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './schema-designer.component.html',
  styleUrl: './schema-designer.component.css',
})
export class SchemaDesignerComponent {
  dataTypes: DataType[] = ['STRING', 'INTEGER', 'FLOAT', 'BOOLEAN', 'DATE'];
  step: 'upload' | 'design' | 'provisioned' | 'loaded' = 'upload';
  filename = '';
  rowCount = 0;
  isLoading = false;
  error = '';

  /** Stash the original file so the user can load data with the same CSV. */
  originalFile: File | null = null;

  projectForm: FormGroup;
  columnsForm: FormArray;
  provisionResult: ProvisionResponse | null = null;
  loadResult: DataLoadResponse | null = null;

  constructor(
    private api: ApiService,
    private fb: FormBuilder
  ) {
    this.columnsForm = this.fb.array([]);
    this.projectForm = this.fb.group({
      projectName: ['', Validators.required],
      screenPopUrlTemplate: [''],
      columns: this.columnsForm,
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files?.length) return;

    const file = input.files[0];
    this.originalFile = file;
    this.isLoading = true;
    this.error = '';

    this.api.inferSchema(file).subscribe({
      next: (response) => {
        this.filename = response.filename;
        this.rowCount = response.row_count;
        this.buildFormFromInference(response.columns);
        this.step = 'design';
        this.isLoading = false;
      },
      error: (err) => {
        this.error = err.error?.detail || 'Failed to analyze CSV file.';
        this.isLoading = false;
      },
    });
  }

  private buildFormFromInference(columns: InferredColumn[]): void {
    this.columnsForm.clear();
    for (const col of columns) {
      this.columnsForm.push(
        this.fb.group({
          originalName: [col.original_name],
          displayName: [col.suggested_display_name, Validators.required],
          dataType: [col.inferred_type, Validators.required],
          isUniqueId: [col.is_primary_key_candidate],
        })
      );
    }
  }

  get columnControls(): FormGroup[] {
    return this.columnsForm.controls as FormGroup[];
  }

  provision(): void {
    if (this.projectForm.invalid) return;

    const columns: FinalizedColumn[] = this.columnsForm.controls.map(
      (ctrl) => ({
        original_name: ctrl.get('originalName')!.value,
        display_name: ctrl.get('displayName')!.value,
        data_type: ctrl.get('dataType')!.value,
        is_unique_id: ctrl.get('isUniqueId')!.value,
      })
    );

    this.isLoading = true;
    this.error = '';

    this.api
      .provisionTable({
        project_name: this.projectForm.get('projectName')!.value,
        screen_pop_url_template:
          this.projectForm.get('screenPopUrlTemplate')!.value || null,
        columns,
      })
      .subscribe({
        next: (result) => {
          this.provisionResult = result;
          this.step = 'provisioned';
          this.isLoading = false;
        },
        error: (err) => {
          this.error = err.error?.detail || 'Provisioning failed.';
          this.isLoading = false;
        },
      });
  }

  /** Load data using the original CSV (or a new file). */
  loadData(event?: Event): void {
    let file = this.originalFile;

    if (event) {
      const input = event.target as HTMLInputElement;
      if (input.files?.length) {
        file = input.files[0];
      }
    }

    if (!file || !this.provisionResult) return;

    this.isLoading = true;
    this.error = '';

    this.api.loadData(this.provisionResult.source_id, file).subscribe({
      next: (result) => {
        this.loadResult = result;
        this.step = 'loaded';
        this.isLoading = false;
      },
      error: (err) => {
        this.error = err.error?.detail || 'Data loading failed.';
        this.isLoading = false;
      },
    });
  }

  /** Auto-enqueue after data load. */
  enqueueNow(): void {
    if (!this.provisionResult) return;
    this.isLoading = true;
    this.api.enqueueProject(this.provisionResult.source_id).subscribe({
      next: () => {
        this.isLoading = false;
      },
      error: (err) => {
        this.error = err.error?.detail || 'Failed to enqueue records.';
        this.isLoading = false;
      },
    });
  }

  reset(): void {
    this.step = 'upload';
    this.filename = '';
    this.rowCount = 0;
    this.error = '';
    this.originalFile = null;
    this.provisionResult = null;
    this.loadResult = null;
    this.columnsForm.clear();
    this.projectForm.reset();
  }
}
