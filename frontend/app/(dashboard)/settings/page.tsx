'use client'

import { useState } from 'react'
import { Plus, Settings2, Trash2, Edit2, CheckCircle2, X } from 'lucide-react'
import { toast } from 'sonner'

type COAEntry = {
  id: string;
  name: string;
  type: 'ASSET' | 'LIABILITY' | 'EQUITY' | 'REVENUE' | 'EXPENSE';
  isSystem: boolean; // Cannot be deleted if system
}

const DEFAULT_COA: COAEntry[] = [
  { id: '1', name: 'Cash', type: 'ASSET', isSystem: true },
  { id: '2', name: 'Accounts Payable', type: 'LIABILITY', isSystem: true },
  { id: '3', name: 'Operating Expense', type: 'EXPENSE', isSystem: true },
  { id: '4', name: 'Travel & Meals', type: 'EXPENSE', isSystem: false },
  { id: '5', name: 'Software Subscriptions', type: 'EXPENSE', isSystem: false },
]

export default function SettingsPage() {
  const [coa, setCoa] = useState<COAEntry[]>(DEFAULT_COA)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [showNew, setShowNew] = useState(false)
  const [newName, setNewName] = useState('')
  const [newType, setNewType] = useState<COAEntry['type']>('EXPENSE')

  const handleSaveEdit = (id: string) => {
    if (!editName.trim()) {
      toast.error('Name cannot be empty')
      return
    }
    setCoa(coa.map(entry => entry.id === id ? { ...entry, name: editName } : entry))
    setEditingId(null)
    toast.success('Account updated successfully')
  }

  const handleAdd = () => {
    if (!newName.trim()) {
      toast.error('Name cannot be empty')
      return
    }
    const newEntry: COAEntry = {
      id: Math.random().toString(),
      name: newName,
      type: newType,
      isSystem: false
    }
    setCoa([...coa, newEntry])
    setShowNew(false)
    setNewName('')
    setNewType('EXPENSE')
    toast.success('Account added to ledger')
  }

  const handleDelete = (id: string) => {
    setCoa(coa.filter(entry => entry.id !== id))
    toast.success('Account deleted')
  }

  const getTypeBadge = (type: string) => {
    switch(type) {
      case 'ASSET': return <span className="px-2 py-0.5 bg-success/10 text-success border border-success/20 rounded font-mono text-[10px] uppercase tracking-wider font-bold">Asset</span>
      case 'LIABILITY': return <span className="px-2 py-0.5 bg-error/10 text-error border border-error/20 rounded font-mono text-[10px] uppercase tracking-wider font-bold">Liability</span>
      case 'EXPENSE': return <span className="px-2 py-0.5 bg-warning/10 text-warning border border-warning/20 rounded font-mono text-[10px] uppercase tracking-wider font-bold">Expense</span>
      default: return <span className="px-2 py-0.5 bg-white/10 text-white border border-white/20 rounded font-mono text-[10px] uppercase tracking-wider font-bold">{type}</span>
    }
  }

  return (
    <div className="flex-1 w-full max-w-4xl mx-auto p-4 md:p-6 lg:p-8 animate-fade-in pb-32">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="font-heading text-2xl md:text-3xl font-bold text-white tracking-tight">Settings</h1>
          <p className="font-sans text-foreground/60 mt-1">Manage your ledger configurations and Chart of Accounts.</p>
        </div>
      </div>

      <div className="glass-panel p-6 rounded-2xl">
        <div className="flex justify-between items-center border-b border-white/10 pb-4 mb-6">
          <div className="flex items-center gap-3">
            <Settings2 className="text-primary w-5 h-5" />
            <h2 className="font-heading text-xl font-bold text-white">Chart of Accounts</h2>
          </div>
          <button 
            onClick={() => setShowNew(true)}
            className="px-4 py-2 bg-gradient-to-r from-primary to-secondary text-background font-sans text-sm font-bold rounded-xl shadow-[0_0_15px_rgba(192,193,255,0.3)] hover:shadow-[0_0_25px_rgba(192,193,255,0.5)] transition-all flex items-center gap-2"
          >
            <Plus size={16} /> Add Account
          </button>
        </div>

        {/* Add New Row */}
        {showNew && (
          <div className="flex gap-4 items-center bg-primary/10 border border-primary/30 p-4 rounded-xl mb-6 animate-fade-in shadow-inner">
            <div className="flex-1">
              <input 
                autoFocus
                placeholder="Account Name..."
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white font-sans text-sm focus:border-primary focus:outline-none transition-colors"
              />
            </div>
            <div className="w-48">
              <select 
                value={newType} 
                onChange={(e) => setNewType(e.target.value as any)}
                className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white font-sans text-sm focus:border-primary focus:outline-none transition-colors appearance-none"
              >
                <option value="EXPENSE">Expense</option>
                <option value="ASSET">Asset</option>
                <option value="LIABILITY">Liability</option>
                <option value="REVENUE">Revenue</option>
                <option value="EQUITY">Equity</option>
              </select>
            </div>
            <div className="flex gap-2">
              <button onClick={handleAdd} className="p-2 bg-success/20 text-success rounded-lg hover:bg-success/30 transition-colors border border-success/30">
                <CheckCircle2 size={18} />
              </button>
              <button onClick={() => setShowNew(false)} className="p-2 bg-white/5 text-foreground/50 rounded-lg hover:text-white hover:bg-white/10 transition-colors border border-white/10">
                <X size={18} />
              </button>
            </div>
          </div>
        )}

        {/* COA List */}
        <div className="space-y-3">
          {coa.map(entry => (
            <div key={entry.id} className="flex items-center justify-between p-4 bg-white/5 border border-white/5 rounded-xl hover:bg-white/10 transition-colors group">
              
              <div className="flex items-center gap-4 flex-1">
                {getTypeBadge(entry.type)}
                {editingId === entry.id ? (
                  <input 
                    autoFocus
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSaveEdit(entry.id)}
                    className="flex-1 bg-black/40 border border-primary/50 rounded-lg px-3 py-1.5 text-white font-sans text-sm focus:outline-none shadow-[0_0_10px_rgba(192,193,255,0.2)]"
                  />
                ) : (
                  <span className="font-sans text-white font-medium">{entry.name}</span>
                )}
                {entry.isSystem && (
                  <span className="font-mono text-[10px] text-foreground/40 uppercase tracking-widest ml-2 px-2 py-0.5 border border-white/10 rounded-full">System Required</span>
                )}
              </div>

              <div className="flex gap-2 ml-4">
                {editingId === entry.id ? (
                  <>
                    <button onClick={() => handleSaveEdit(entry.id)} className="p-2 text-success hover:bg-success/10 rounded-lg transition-colors">
                      <CheckCircle2 size={16} />
                    </button>
                    <button onClick={() => setEditingId(null)} className="p-2 text-foreground/50 hover:bg-white/5 rounded-lg transition-colors">
                      <X size={16} />
                    </button>
                  </>
                ) : (
                  <>
                    <button 
                      onClick={() => { setEditingId(entry.id); setEditName(entry.name); }} 
                      className="p-2 text-foreground/40 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Edit2 size={16} />
                    </button>
                    {!entry.isSystem && (
                      <button 
                        onClick={() => handleDelete(entry.id)}
                        className="p-2 text-foreground/40 hover:text-error hover:bg-error/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
