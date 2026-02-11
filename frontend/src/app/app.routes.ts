import { Routes } from '@angular/router';

import { LoginComponent } from './components/login/login.component';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { SchemaDesignerComponent } from './components/schema-designer/schema-designer.component';
import { AgentWorkspaceComponent } from './components/agent-workspace/agent-workspace.component';
import { EmployeeTrackerComponent } from './components/employee-tracker/employee-tracker.component';
import { authGuard, roleGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  {
    path: '',
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      { path: 'dashboard', component: DashboardComponent },
      {
        path: 'designer',
        component: SchemaDesignerComponent,
        canActivate: [roleGuard('admin', 'supervisor')],
      },
      { path: 'workspace', component: AgentWorkspaceComponent },
      {
        path: 'employees',
        component: EmployeeTrackerComponent,
        canActivate: [roleGuard('admin', 'supervisor')],
      },
    ],
  },
];
