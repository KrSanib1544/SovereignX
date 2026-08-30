// frontend/src/types/api.ts

export interface ProblemDetails {
  type?: string;
  title: string;
  status: number;
  detail: string;
  instance?: string;
  error_code?: string;
  timestamp?: string;
}
