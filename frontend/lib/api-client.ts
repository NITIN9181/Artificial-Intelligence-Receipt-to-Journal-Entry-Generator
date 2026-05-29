export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, body: unknown) {
    super(`API Error ${status}`)
    this.status = status
    this.body = body
    this.name = 'ApiError'
  }
}

export function getBaseUrl(): string {
  // Prioritize the standard variable we used in deployment
  const envBase =
    process.env.NEXT_PUBLIC_API_URL ||
    process.env.NEXT_PUBLIC_FASTAPI_BASE_URL ||
    process.env.FASTAPI_BASE_URL

  // If the URL already ends with /api/v1, strip it so the endpoint joining works correctly
  if (envBase) {
    return envBase.replace(/\/api\/v1\/?$/, '')
  }

  return 'http://localhost:8000'
}

export async function apiClient<T = unknown>(endpoint: string, options: RequestInit = {}): Promise<T> {
  try {
    const headers = new Headers(options.headers)

    if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json')
    }

    const normalizedEndpoint = endpoint.startsWith('/api/v1') ? endpoint : `/api/v1${endpoint}`
    const response = await fetch(`${getBaseUrl()}${normalizedEndpoint}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const body = await response.json().catch(() => ({ error: response.statusText }))
      throw new ApiError(response.status, body)
    }

    return response.json()
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }

    throw new ApiError(0, { error: 'Network error' })
  }
}
