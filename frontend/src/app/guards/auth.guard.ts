import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);

  if (auth.isAuthenticated) {
    return true;
  }
  return router.createUrlTree(['/login']);
};

export const roleGuard =
  (...allowedRoles: string[]): CanActivateFn =>
  () => {
    const auth = inject(AuthService);
    const router = inject(Router);

    if (!auth.isAuthenticated) {
      return router.createUrlTree(['/login']);
    }
    if (!auth.hasRole(...allowedRoles)) {
      return router.createUrlTree(['/dashboard']);
    }
    return true;
  };
