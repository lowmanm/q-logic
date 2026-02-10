import { Routes } from '@angular/router';

import { SchemaDesignerComponent } from './components/schema-designer/schema-designer.component';
import { AgentWorkspaceComponent } from './components/agent-workspace/agent-workspace.component';
import { EmployeeTrackerComponent } from './components/employee-tracker/employee-tracker.component';

export const routes: Routes = [
  { path: '', redirectTo: '/designer', pathMatch: 'full' },
  { path: 'designer', component: SchemaDesignerComponent },
  { path: 'workspace', component: AgentWorkspaceComponent },
  { path: 'employees', component: EmployeeTrackerComponent },
];
