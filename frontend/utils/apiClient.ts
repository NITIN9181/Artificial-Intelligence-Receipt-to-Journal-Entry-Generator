import { createClient } from '@/utils/supabase/client'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export async function fetchApi<T = any>(endpoint: string, options: RequestInit = {}): Promise<T> {
  // Use browser client to get the session token
  const supabase = createClient()
  const { data } = await supabase.auth.getSession()

  const headers = new Headers(options.headers)
  if (data.session?.access_token) {
    headers.set('Authorization', `Bearer ${data.session.access_token}`)
  }

  // Don't set Content-Type for FormData (browser sets boundary automatically)
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => null)
    throw new Error(errorData?.detail || response.statusText || 'API request failed')
  }

  return response.json()
}
