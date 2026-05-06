import { redirect } from 'next/navigation'
import { createClient } from '@/utils/supabase/server'
import LoginForm from './LoginForm'

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>
}) {
  const supabase = await createClient()

  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (user) {
    return redirect('/')
  }

  const awaitedSearchParams = await searchParams;
  const message = awaitedSearchParams.message as string;
  const error = awaitedSearchParams.error as string;

  return (
    <div className="flex-1 flex items-center justify-center min-h-[calc(100vh-64px)] px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 glass-panel p-8 sm:p-10 rounded-2xl relative overflow-hidden">
        <div className="text-center relative z-10">
          <h2 className="mt-6 font-heading text-3xl font-bold text-white tracking-tight">
            LedgerFlow
          </h2>
          <p className="mt-2 font-sans text-sm text-foreground/70">
            Sign in with your email to continue. We'll send you a magic link. No passwords required.
          </p>
        </div>

        <LoginForm message={message} error={error} />
      </div>
    </div>
  )
}
