import type {
  AskResponse,
  SearchResult,
  CommandDetail,
  Category,
  HealthResponse,
} from './types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public statusText: string,
    public body?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message: string, public originalError: unknown) {
    super(message);
    this.name = 'NetworkError';
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  let response: Response;
  try {
    response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });
  } catch (error) {
    throw new NetworkError(
      `Network request failed for ${endpoint}: ${error instanceof Error ? error.message : String(error)}`,
      error,
    );
  }

  if (!response.ok) {
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      body = await response.text().catch(() => undefined);
    }
    throw new ApiError(
      `API request failed: ${response.status} ${response.statusText} for ${endpoint}`,
      response.status,
      response.statusText,
      body,
    );
  }

  return response.json() as Promise<T>;
}

export async function askCommand(query: string): Promise<AskResponse> {
  return fetchApi<AskResponse>('/api/v1/ask', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
}

export async function getCommands(
  technology?: string,
): Promise<SearchResult[]> {
  const params = technology
    ? `?technology=${encodeURIComponent(technology)}`
    : '';
  return fetchApi<SearchResult[]>(`/api/v1/commands${params}`);
}

export async function getCommand(id: string): Promise<CommandDetail> {
  return fetchApi<CommandDetail>(
    `/api/v1/commands/${encodeURIComponent(id)}`,
  );
}

export async function getCategories(): Promise<Category[]> {
  return fetchApi<Category[]>('/api/v1/categories');
}

export async function checkHealth(): Promise<HealthResponse> {
  return fetchApi<HealthResponse>('/api/v1/health');
}

export async function getTechnologies(): Promise<Record<string, number>> {
  return fetchApi<Record<string, number>>('/api/v1/technologies');
}

export async function searchCommands(
  query: string,
  topK: number = 10,
  mode: string = 'hybrid',
): Promise<AskResponse> {
  return fetchApi<AskResponse>('/api/v1/ask', {
    method: 'POST',
    body: JSON.stringify({ query, top_k: topK, mode, explain: true }),
  });
}

// Unified client object
export const apiClient = {
  ask: askCommand,
  search: searchCommands,
  getCommands,
  getCommand,
  getCategories,
  getTechnologies,
  checkHealth,
};
