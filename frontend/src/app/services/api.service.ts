import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import {
  SchemaInferenceResponse,
  ProvisionRequest,
  ProvisionResponse,
  DataLoadResponse,
} from '../models/schema.models';
import {
  ProjectInfo,
  TaskRecord,
  EnqueueResponse,
  QueueStatsResponse,
  NextTaskResponse,
  QueueActionResponse,
  TeamAHT,
  AgentStates,
  LeaderboardEntry,
  ProjectQueueStats,
} from '../models/workspace.models';
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

  loadData(sourceId: string, file: File): Observable<DataLoadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<DataLoadResponse>(
      `${this.base}/schema/${sourceId}/load`,
      formData
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

  // --- Queue ---

  enqueueProject(sourceId: string): Observable<EnqueueResponse> {
    return this.http.post<EnqueueResponse>(
      `${this.base}/workspace/projects/${sourceId}/enqueue`,
      {}
    );
  }

  getQueueStats(sourceId: string): Observable<QueueStatsResponse> {
    return this.http.get<QueueStatsResponse>(
      `${this.base}/workspace/projects/${sourceId}/queue-stats`
    );
  }

  getNextTask(
    sourceId: string,
    employeeId: string
  ): Observable<NextTaskResponse> {
    const params = new HttpParams().set('employee_id', employeeId);
    return this.http.post<NextTaskResponse>(
      `${this.base}/workspace/projects/${sourceId}/next`,
      {},
      { params }
    );
  }

  completeQueueItem(queueId: string): Observable<QueueActionResponse> {
    return this.http.post<QueueActionResponse>(
      `${this.base}/workspace/queue/${queueId}/complete`,
      {}
    );
  }

  skipQueueItem(queueId: string): Observable<QueueActionResponse> {
    return this.http.post<QueueActionResponse>(
      `${this.base}/workspace/queue/${queueId}/skip`,
      {}
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

  // --- Dashboard Metrics ---

  getTeamAHT(sourceId?: string): Observable<TeamAHT> {
    let params = new HttpParams();
    if (sourceId) {
      params = params.set('source_id', sourceId);
    }
    return this.http.get<TeamAHT>(
      `${this.base}/metrics/team-aht`,
      { params }
    );
  }

  getAgentStates(): Observable<AgentStates> {
    return this.http.get<AgentStates>(`${this.base}/metrics/agent-states`);
  }

  getLeaderboard(sourceId?: string): Observable<LeaderboardEntry[]> {
    let params = new HttpParams();
    if (sourceId) {
      params = params.set('source_id', sourceId);
    }
    return this.http.get<LeaderboardEntry[]>(
      `${this.base}/metrics/leaderboard`,
      { params }
    );
  }

  getAllQueueStats(): Observable<ProjectQueueStats[]> {
    return this.http.get<ProjectQueueStats[]>(
      `${this.base}/metrics/queue-stats`
    );
  }
}
