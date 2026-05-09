import { NextResponse } from 'next/server'
import { createClient } from '@/utils/supabase/server'

export async function GET(request: Request) {
  const requestUrl = new URL(request.url)
  const code = requestUrl.searchParams.get('code')
  const next = requestUrl.searchParams.get('next') ?? '/dashboard'

  if (code) {
    const supabase = await createClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    
    if (!error) {
      // Use the origin from the request URL as a base fallback
      const origin = requestUrl.origin
      
      // Handle Docker/Reverse Proxy headers
      const forwardedHost = request.headers.get('x-forwarded-host')
      const forwardedProto = request.headers.get('x-forwarded-proto') || 'http'
      
      if (forwardedHost) {
        return NextResponse.redirect(`${forwardedProto}://${forwardedHost}${next}`)
      }
      
      return NextResponse.redirect(`${origin}${next}`)
    } else {
      console.error('Auth callback error:', error.message)
    }
  }

  // Return the user to a login page with an error message
  const loginUrl = new URL('/login', request.url)
  loginUrl.searchParams.set('error', 'Authentication failed or link expired.')
  return NextResponse.redirect(loginUrl)
}
