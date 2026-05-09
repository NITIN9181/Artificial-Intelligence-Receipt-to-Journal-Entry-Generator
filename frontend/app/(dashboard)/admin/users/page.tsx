'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { toast } from 'sonner'
import { Users, ChevronLeft, ChevronRight } from 'lucide-react'
import { apiClient } from '@/lib/api-client'
import { useAuth } from '@/lib/auth-context'

type UserData = {
  id: string
  full_name: string | null
  company_name: string | null
  role: 'PREPARER' | 'REVIEWER' | 'ADMIN'
  created_at: string
}

type UsersResponse = {
  users: UserData[]
  total: number
}

export default function AdminUsersPage() {
  const router = useRouter()
  const { user, isLoading } = useAuth()
  
  const [users, setUsers] = useState<UserData[]>([])
  const [total, setTotal] = useState(0)
  const [skip, setSkip] = useState(0)
  const [isFetching, setIsFetching] = useState(true)
  const limit = 25

  useEffect(() => {
    if (!isLoading && user?.role !== 'ADMIN') {
      router.replace('/dashboard')
    }
  }, [user, isLoading, router])

  const fetchUsers = async () => {
    setIsFetching(true)
    try {
      const data = await apiClient<UsersResponse>(`/admin/users?skip=${skip}&limit=${limit}`)
      setUsers(data.users)
      setTotal(data.total)
    } catch (err) {
      toast.error('Failed to fetch users')
    } finally {
      setIsFetching(false)
    }
  }

  useEffect(() => {
    if (user?.role === 'ADMIN') {
      fetchUsers()
    }
  }, [user, skip])

  const handleRoleChange = async (id: string, newRole: string, userName: string | null) => {
    try {
      await apiClient(`/admin/users/${id}/role`, {
        method: 'PUT',
        body: JSON.stringify({ role: newRole })
      })
      toast.success(`Updated ${userName || 'user'} to ${newRole}`)
      setUsers(prev => prev.map(u => u.id === id ? { ...u, role: newRole as any } : u))
    } catch (err) {
      toast.error('Failed to update role')
    }
  }

  if (isLoading || isFetching && users.length === 0) {
    return (
      <div className="flex-1 p-8 flex items-center justify-center animate-fade-in">
        <div className="animate-spin w-8 h-8 border-2 border-t-primary border-primary/20 rounded-full"></div>
      </div>
    )
  }

  if (user?.role !== 'ADMIN') {
    return null
  }

  return (
    <div className="flex-1 w-full max-w-6xl mx-auto p-4 md:p-6 lg:p-8 animate-fade-in pb-32">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="font-heading text-2xl md:text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            <Users className="text-primary" /> User Management
          </h1>
          <p className="font-sans text-foreground/60 mt-1">Manage system users and access roles.</p>
        </div>
      </div>

      <div className="glass-panel rounded-2xl overflow-hidden border border-white/5">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 bg-white/5">
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50">Full Name</th>
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50">Company</th>
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50">Role</th>
                <th className="px-6 py-4 font-mono text-[10px] uppercase tracking-widest text-foreground/50">Created At</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                  <td className="px-6 py-4 font-sans text-sm text-white">{u.full_name || 'N/A'}</td>
                  <td className="px-6 py-4 font-sans text-sm text-foreground/80">{u.company_name || 'N/A'}</td>
                  <td className="px-6 py-4 font-sans text-sm">
                    <select 
                      value={u.role}
                      onChange={(e) => handleRoleChange(u.id, e.target.value, u.full_name)}
                      className="bg-black/40 border border-white/10 rounded-lg px-2 py-1.5 text-white focus:border-primary focus:outline-none transition-colors text-xs uppercase tracking-wider font-mono font-bold appearance-none"
                    >
                      <option value="PREPARER">PREPARER</option>
                      <option value="REVIEWER">REVIEWER</option>
                      <option value="ADMIN">ADMIN</option>
                    </select>
                  </td>
                  <td className="px-6 py-4 font-sans text-sm text-foreground/80">
                    {u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-foreground/50 font-sans text-sm">
                    No users found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        
        {total > limit && (
          <div className="p-4 border-t border-white/5 flex justify-between items-center bg-white/5">
            <span className="font-sans text-xs text-foreground/50">
              Showing {skip + 1} to {Math.min(skip + limit, total)} of {total} users
            </span>
            <div className="flex gap-2">
              <button 
                onClick={() => setSkip(s => Math.max(0, s - limit))}
                disabled={skip === 0}
                className="px-3 py-1.5 rounded-lg border border-white/10 text-white font-sans text-xs hover:bg-white/5 disabled:opacity-50 flex items-center gap-1"
              >
                <ChevronLeft size={14} /> Prev
              </button>
              <button 
                onClick={() => setSkip(s => s + limit)}
                disabled={skip + limit >= total}
                className="px-3 py-1.5 rounded-lg border border-white/10 text-white font-sans text-xs hover:bg-white/5 disabled:opacity-50 flex items-center gap-1"
              >
                Next <ChevronRight size={14} />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
