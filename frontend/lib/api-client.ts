import { createClient } from '@/utils/supabase/client'

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

function getBaseUrl(): string {
  const envBase =
    (typeof window === 'undefined'
      ? process.env.FASTAPI_BASE_URL
      : process.env.NEXT_PUBLIC_FASTAPI_BASE_URL) ??
    process.env.NEXT_PUBLIC_FASTAPI_BASE_URL

  return envBase || 'http://localhost:8000'
}

export async function apiClient<T = unknown>(endpoint: string, options: RequestInit = {}): Promise<T> {
  try {
    const supabase = createClient()
    const { data } = await supabase.auth.getSession()

    const headers = new Headers(options.headers)
    if (data.session?.access_token) {
      headers.set('Authorization', `Bearer ${data.session.access_token}`)
    }

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
