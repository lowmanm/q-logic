import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, Observable, tap } from 'rxjs';
import { Router } from '@angular/router';

import { environment } from '../../environments/environment';
import { LoginRequest, TokenResponse, UserProfile } from '../models/auth.models';

const TOKEN_KEY = 'qlogic_token';
const USER_KEY = 'qlogic_user';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private base = environment.apiUrl;
  private userSubject = new BehaviorSubject<UserProfile | null>(this.loadUser());

  user$ = this.userSubject.asObservable();

  constructor(private http: HttpClient, private router: Router) {}

  get token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  }

  get isAuthenticated(): boolean {
    return !!this.token;
  }

  get currentUser(): UserProfile | null {
    return this.userSubject.value;
  }

  login(credentials: LoginRequest): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>(`${this.base}/auth/login`, credentials)
      .pipe(
        tap((res) => {
          localStorage.setItem(TOKEN_KEY, res.access_token);
          this.fetchProfile();
        })
      );
  }

  fetchProfile(): void {
    this.http.get<UserProfile>(`${this.base}/auth/me`).subscribe({
      next: (user) => {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        this.userSubject.next(user);
      },
      error: () => this.logout(),
    });
  }

  logout(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    this.userSubject.next(null);
    this.router.navigate(['/login']);
  }

  hasRole(...roles: string[]): boolean {
    const user = this.currentUser;
    return user !== null && roles.includes(user.role);
  }

  private loadUser(): UserProfile | null {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as UserProfile;
    } catch {
      return null;
    }
  }
}
