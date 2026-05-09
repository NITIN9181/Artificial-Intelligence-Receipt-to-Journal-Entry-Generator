'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Edit2, CheckCircle2, X } from 'lucide-react'
import { toast } from 'sonner'
import { apiClient } from '@/lib/api-client'

type Mapping = {
  id: string;
  internal_account_code: string;
  gnucash_account_path: string;
}

export default function GnuCashMappings() {
  const queryClient = useQueryClient()
  const [showNew, setShowNew] = useState(false)
  const [newCode, setNewCode] = useState('')
  const [newPath, setNewPath] = useState('')

  const [editingId, setEditingId] = useState<string | null>(null)
  const [editCode, setEditCode] = useState('')
  const [editPath, setEditPath] = useState('')

  const { data: mappings = [], isLoading } = useQuery<Mapping[]>({
    queryKey: ['gnucash-mappings'],
    queryFn: async () => {
      return await apiClient<Mapping[]>('/gnucash/mappings')
    }
  })

  const createMutation = useMutation({
    mutationFn: async (newMapping: Omit<Mapping, 'id'>) => {
      return await apiClient<Mapping>('/gnucash/mappings', {
        method: 'POST',
        body: JSON.stringify(newMapping)
      })
    },
    onMutate: async (newMapping) => {
      await queryClient.cancelQueries({ queryKey: ['gnucash-mappings'] })
      const previous = queryClient.getQueryData<Mapping[]>(['gnucash-mappings'])
      queryClient.setQueryData<Mapping[]>(['gnucash-mappings'], old => [...(old || []), { id: 'temp', ...newMapping }])
      return { previous }
    },
    onError: (err, newMapping, context) => {
      queryClient.setQueryData(['gnucash-mappings'], context?.previous)
      toast.error('Failed to create mapping')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['gnucash-mappings'] })
      setShowNew(false)
      setNewCode('')
      setNewPath('')
      toast.success('Mapping added')
    }
  })

  const updateMutation = useMutation({
    mutationFn: async (mapping: Mapping) => {
      return await apiClient<Mapping>(`/gnucash/mappings/${mapping.id}`, {
        method: 'PUT',
        body: JSON.stringify({ internal_account_code: mapping.internal_account_code, gnucash_account_path: mapping.gnucash_account_path })
      })
    },
    onMutate: async (updatedMapping) => {
      await queryClient.cancelQueries({ queryKey: ['gnucash-mappings'] })
      const previous = queryClient.getQueryData<Mapping[]>(['gnucash-mappings'])
      queryClient.setQueryData<Mapping[]>(['gnucash-mappings'], old => 
        (old || []).map(m => m.id === updatedMapping.id ? updatedMapping : m)
      )
      return { previous }
    },
    onError: (err, newMapping, context) => {
      queryClient.setQueryData(['gnucash-mappings'], context?.previous)
      toast.error('Failed to update mapping')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['gnucash-mappings'] })
      setEditingId(null)
      toast.success('Mapping updated')
    }
  })

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return await apiClient(`/gnucash/mappings/${id}`, { method: 'DELETE' })
    },
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: ['gnucash-mappings'] })
      const previous = queryClient.getQueryData<Mapping[]>(['gnucash-mappings'])
      queryClient.setQueryData<Mapping[]>(['gnucash-mappings'], old => (old || []).filter(m => m.id !== id))
      return { previous }
    },
    onError: (err, id, context) => {
      queryClient.setQueryData(['gnucash-mappings'], context?.previous)
      toast.error('Failed to delete mapping')
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['gnucash-mappings'] })
      toast.success('Mapping deleted')
    }
  })

  const handleAdd = () => {
    if (!newCode || !newPath) return toast.error('Both fields are required')
    createMutation.mutate({ internal_account_code: newCode, gnucash_account_path: newPath })
  }

  const handleUpdate = (id: string) => {
    if (!editCode || !editPath) return toast.error('Both fields are required')
    updateMutation.mutate({ id, internal_account_code: editCode, gnucash_account_path: editPath })
  }

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this mapping?')) {
      deleteMutation.mutate(id)
    }
  }

  return (
    <div className="glass-panel p-6 rounded-2xl mt-8">
      <div className="flex justify-between items-center border-b border-white/10 pb-4 mb-6">
        <div>
          <h2 className="font-heading text-xl font-bold text-white">GnuCash Account Mappings</h2>
        </div>
        <button 
          onClick={() => setShowNew(true)}
          className="px-4 py-2 bg-gradient-to-r from-primary to-secondary text-background font-sans text-sm font-bold rounded-xl shadow-[0_0_15px_rgba(192,193,255,0.3)] hover:shadow-[0_0_25px_rgba(192,193,255,0.5)] transition-all flex items-center gap-2"
        >
          <Plus size={16} /> Add Mapping
        </button>
      </div>

      {showNew && (
        <div className="flex gap-4 items-center bg-primary/10 border border-primary/30 p-4 rounded-xl mb-6 animate-fade-in shadow-inner">
          <div className="flex-1">
            <input 
              placeholder="Internal Account Code (e.g. 5100)"
              value={newCode}
              onChange={(e) => setNewCode(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white font-sans text-sm focus:border-primary focus:outline-none transition-colors"
            />
          </div>
          <div className="flex-1">
            <input 
              placeholder="GnuCash Account Path (e.g. Expenses:Office Supplies)"
              value={newPath}
              onChange={(e) => setNewPath(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white font-sans text-sm focus:border-primary focus:outline-none transition-colors"
            />
          </div>
          <div className="flex gap-2">
            <button onClick={handleAdd} disabled={createMutation.isPending} className="p-2 bg-success/20 text-success rounded-lg hover:bg-success/30 transition-colors border border-success/30 disabled:opacity-50">
              <CheckCircle2 size={18} />
            </button>
            <button onClick={() => setShowNew(false)} className="p-2 bg-white/5 text-foreground/50 rounded-lg hover:text-white hover:bg-white/10 transition-colors border border-white/10">
              <X size={18} />
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-4 text-foreground/50 text-sm">Loading mappings...</div>
      ) : (
        <div className="space-y-3">
          {mappings.map(mapping => (
            <div key={mapping.id} className="flex items-center justify-between p-4 bg-white/5 border border-white/5 rounded-xl hover:bg-white/10 transition-colors group">
              <div className="flex gap-4 flex-1">
                {editingId === mapping.id ? (
                  <>
                    <input 
                      value={editCode}
                      onChange={(e) => setEditCode(e.target.value)}
                      className="flex-1 bg-black/40 border border-primary/50 rounded-lg px-3 py-1.5 text-white font-sans text-sm focus:outline-none shadow-[0_0_10px_rgba(192,193,255,0.2)]"
                    />
                    <input 
                      value={editPath}
                      onChange={(e) => setEditPath(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleUpdate(mapping.id)}
                      className="flex-[2] bg-black/40 border border-primary/50 rounded-lg px-3 py-1.5 text-white font-sans text-sm focus:outline-none shadow-[0_0_10px_rgba(192,193,255,0.2)]"
                    />
                  </>
                ) : (
                  <>
                    <div className="flex-1 font-mono text-sm text-primary">{mapping.internal_account_code}</div>
                    <div className="flex-[2] font-sans text-sm text-white">{mapping.gnucash_account_path}</div>
                  </>
                )}
              </div>

              <div className="flex gap-2 ml-4">
                {editingId === mapping.id ? (
                  <>
                    <button onClick={() => handleUpdate(mapping.id)} disabled={updateMutation.isPending} className="p-2 text-success hover:bg-success/10 rounded-lg transition-colors disabled:opacity-50">
                      <CheckCircle2 size={16} />
                    </button>
                    <button onClick={() => setEditingId(null)} className="p-2 text-foreground/50 hover:bg-white/5 rounded-lg transition-colors">
                      <X size={16} />
                    </button>
                  </>
                ) : (
                  <>
                    <button 
                      onClick={() => { setEditingId(mapping.id); setEditCode(mapping.internal_account_code); setEditPath(mapping.gnucash_account_path); }} 
                      className="p-2 text-foreground/40 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button 
                      onClick={() => handleDelete(mapping.id)}
                      disabled={deleteMutation.isPending}
                      className="p-2 text-foreground/40 hover:text-error hover:bg-error/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100 disabled:opacity-50"
                    >
                      <Trash2 size={16} />
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
          {mappings.length === 0 && !showNew && (
            <div className="text-center py-4 text-foreground/50 text-sm">No mappings configured.</div>
          )}
        </div>
      )}
    </div>
  )
}
