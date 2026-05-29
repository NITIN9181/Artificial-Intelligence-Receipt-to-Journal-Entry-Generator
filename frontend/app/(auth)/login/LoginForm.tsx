'use client'

import { Mail, ArrowRight, Loader2, Lock, Eye, EyeOff } from 'lucide-react'
import { useState } from 'react'
import { loginWithPassword } from './actions'

export default function LoginForm({ message, error }: { message?: string; error?: string }) {
  const [isPending, setIsPending] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const handlePasswordSubmit = () => {
    setIsPending(true)
  }

  return (
    <div className="mt-8 space-y-6 relative z-10 animate-fade-in">
      {/* Email/Password Form */}
      <form action={loginWithPassword} onSubmit={handlePasswordSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block font-mono text-xs font-medium text-foreground/80 mb-2 ml-1 tracking-widest uppercase">
            Email address
          </label>
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-colors">
              <Mail className="h-5 w-5 text-foreground/40 group-focus-within:text-primary transition-colors" />
            </div>
            <input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              required
              className="appearance-none rounded-xl relative block w-full px-4 py-3 pl-12 border border-white/10 bg-white/5 backdrop-blur-sm placeholder-foreground/30 text-white focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary sm:text-sm transition-all hover:border-white/20 font-sans"
              placeholder="you@company.com"
            />
          </div>
        </div>

        <div>
          <label htmlFor="password" className="block font-mono text-xs font-medium text-foreground/80 mb-2 ml-1 tracking-widest uppercase">
            Password
          </label>
          <div className="relative group">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none transition-colors">
              <Lock className="h-5 w-5 text-foreground/40 group-focus-within:text-primary transition-colors" />
            </div>
            <input
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              required
              className="appearance-none rounded-xl relative block w-full px-4 py-3 pl-12 pr-12 border border-white/10 bg-white/5 backdrop-blur-sm placeholder-foreground/30 text-white focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary sm:text-sm transition-all hover:border-white/20 font-sans"
              placeholder="••••••••"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-4 flex items-center text-foreground/40 hover:text-foreground/70 transition-colors"
            >
              {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {error && (
          <div className="text-error bg-error-container/30 border border-error/30 rounded-xl p-4 text-sm flex items-center gap-3 animate-fade-in font-sans">
            <div className="h-2 w-2 rounded-full bg-error flex-shrink-0 animate-pulse" />
            {error}
          </div>
        )}
        
        <button
          type="submit"
          disabled={isPending}
          className="group relative w-full flex justify-center items-center py-3 px-4 border border-transparent text-sm font-bold rounded-xl text-background bg-gradient-to-r from-primary to-secondary hover:from-primary/90 hover:to-secondary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary focus:ring-offset-background transition-all shadow-[0_0_20px_rgba(192,193,255,0.3)] hover:shadow-[0_0_30px_rgba(192,193,255,0.5)] hover:-translate-y-0.5 disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:translate-y-0 overflow-hidden font-heading tracking-wide"
        >
          <span className="relative flex items-center gap-2">
            {isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Signing in...
              </>
            ) : (
              <>
                Sign In
                <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
              </>
            )}
          </span>
        </button>
      </form>
    </div>
  )
}
