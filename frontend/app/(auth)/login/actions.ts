'use server'

import { createClient } from '@/utils/supabase/server'
import { redirect } from 'next/navigation'
import { headers } from 'next/headers'

export async function login(formData: FormData) {
  const email = formData.get('email') as string
  const supabase = await createClient()

  const originList = await headers()
  const origin = originList.get('origin') || 'http://localhost:3000'

  // --- DEVELOPER BYPASS ---
  if (email === 'test@example.com') {
    const { error: testError } = await supabase.auth.signInWithPassword({
      email: 'test@example.com',
      password: 'password123',
    });
    
    if (testError) {
      console.error("Test Login Error:", testError.message);
      return redirect(`/login?error=${encodeURIComponent("Test account not configured. See instructions.")}`);
    }
    
    return redirect('/'); // Instantly log in!
  }
  // ------------------------

  const { error } = await supabase.auth.signInWithOtp({
    email,
    options: {
      shouldCreateUser: true,
      emailRedirectTo: `${origin}/api/auth/callback`,
    },
  })

  if (error) {
    console.error("Supabase Auth Error:", error.message);
    return redirect(`/login?error=${encodeURIComponent(error.message)}`)
  }

  return redirect('/login?message=Check your email for the magic link')
}

export async function loginWithPassword(formData: FormData) {
  const email = formData.get('email') as string
  const password = formData.get('password') as string
  
  const supabase = await createClient()

  const { error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (error) {
    console.error("Password Login Error:", error.message);
    return redirect(`/login?error=${encodeURIComponent(error.message)}`)
  }

  return redirect('/dashboard')
}
