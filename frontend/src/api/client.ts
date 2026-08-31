// frontend/src/api/client.ts

const API_BASE_URL = (import.meta.env && import.meta.env.VITE_API_BASE_URL) || '/api/v1';

export async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorDetail = response.statusText;
      try {
        const errJson = await response.json();
        errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
      } catch {
        // Ignored
      }
      throw new Error(`API Error [${response.status}]: ${errorDetail}`);
    }

    return response.json() as Promise<T>;
  } catch (err: any) {
    if (err.message && err.message.startsWith('API Error')) {
      throw err;
    }
    throw new Error(
      `Network Communication Error (${err.message || 'Failed to fetch'}). Please ensure Sovereign-X backend is running at http://127.0.0.1:8000.`
    );
  }
}
