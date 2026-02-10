import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import {
  SchemaInferenceResponse,
  ProvisionRequest,
  ProvisionResponse,
} from '../models/schema.models';
import { ProjectInfo, TaskRecord } from '../models/workspace.models';
import {
  Employee,
  EmployeeCreate,
  EmployeeState,
  TaskLog,
  AHTMetric,
} from '../models/employee.models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private base = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // --- Schema ---

  inferSchema(file: File): Observable<SchemaInferenceResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<SchemaInferenceResponse>(
      `${this.base}/schema/infer`,
      formData
    );
  }

  provisionTable(
    request: ProvisionRequest
  ): Observable<ProvisionResponse> {
    return this.http.post<ProvisionResponse>(
      `${this.base}/schema/provision`,
      request
    );
  }

  // --- Workspace ---

  getProjects(): Observable<ProjectInfo[]> {
    return this.http.get<ProjectInfo[]>(`${this.base}/workspace/projects`);
  }

  getProject(sourceId: string): Observable<ProjectInfo> {
    return this.http.get<ProjectInfo>(
      `${this.base}/workspace/projects/${sourceId}`
    );
  }

  getRecords(
    sourceId: string,
    limit = 50,
    offset = 0
  ): Observable<TaskRecord[]> {
    const params = new HttpParams()
      .set('limit', limit)
      .set('offset', offset);
    return this.http.get<TaskRecord[]>(
      `${this.base}/workspace/projects/${sourceId}/records`,
      { params }
    );
  }

  getRecord(sourceId: string, recordId: number): Observable<TaskRecord> {
    return this.http.get<TaskRecord>(
      `${this.base}/workspace/projects/${sourceId}/records/${recordId}`
    );
  }

  // --- Employees ---

  getEmployees(): Observable<Employee[]> {
    return this.http.get<Employee[]>(`${this.base}/employees`);
  }

  createEmployee(data: EmployeeCreate): Observable<Employee> {
    return this.http.post<Employee>(`${this.base}/employees`, data);
  }

  changeState(
    employeeId: string,
    newState: EmployeeState
  ): Observable<Employee> {
    return this.http.put<Employee>(
      `${this.base}/employees/${employeeId}/state`,
      { new_state: newState }
    );
  }

  assignTask(
    employeeId: string,
    sourceId: string,
    recordId: string
  ): Observable<TaskLog> {
    return this.http.post<TaskLog>(
      `${this.base}/employees/${employeeId}/tasks`,
      { source_id: sourceId, record_id: recordId }
    );
  }

  completeTask(taskId: string): Observable<TaskLog> {
    return this.http.post<TaskLog>(
      `${this.base}/employees/tasks/${taskId}/complete`,
      {}
    );
  }

  getAHT(
    employeeId: string,
    sourceId?: string
  ): Observable<AHTMetric> {
    let params = new HttpParams();
    if (sourceId) {
      params = params.set('source_id', sourceId);
    }
    return this.http.get<AHTMetric>(
      `${this.base}/employees/${employeeId}/metrics/aht`,
      { params }
    );
  }
}
