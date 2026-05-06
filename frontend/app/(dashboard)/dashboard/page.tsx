'use client'

import React, { useState, useEffect, useMemo } from 'react'
import { fetchApi } from '@/utils/apiClient'
import { toast } from 'sonner'
import { 
  Receipt, TrendingUp, Clock, PieChart, 
  ArrowUpRight, ArrowDownRight, Loader2 
} from 'lucide-react'

type ReceiptItem = {
  id: string
  status: string
  created_at: string | null
  extracted_at: string | null
  extracted_data: any
}

export default function DashboardPage() {
  const [receipts, setReceipts] = useState<ReceiptItem[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const data = await fetchApi('/receipts?limit=100')
      setReceipts(data.items || [])
    } catch (err: any) {
      toast.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  // KPI: Receipts this month
  const receiptsThisMonth = useMemo(() => {
    const now = new Date()
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1)
    return receipts.filter(r => {
      if (!r.created_at) return false
      return new Date(r.created_at) >= startOfMonth
    }).length
  }, [receipts])

  // KPI: Total spend (sum of total_amount from extracted_data)
  const totalSpend = useMemo(() => {
    return receipts.reduce((sum, r) => {
      const amount = r.extracted_data?.total_amount || 0
      return sum + Number(amount)
    }, 0)
  }, [receipts])

  // KPI: Avg processing time (extracted_at - created_at)
  const avgProcessingTime = useMemo(() => {
    const times: number[] = []
    receipts.forEach(r => {
      if (r.extracted_at && r.created_at) {
        const diff = new Date(r.extracted_at).getTime() - new Date(r.created_at).getTime()
        if (diff > 0) times.push(diff)
      }
    })
    if (times.length === 0) return null
    const avgMs = times.reduce((a, b) => a + b, 0) / times.length
    return avgMs / 1000 // seconds
  }, [receipts])

  // KPI: Spend by category
  const spendByCategory = useMemo(() => {
    const map: Record<string, number> = {}
    receipts.forEach(r => {
      const cat = r.extracted_data?.expense_category || 'Uncategorized'
      const amt = Number(r.extracted_data?.total_amount || 0)
      map[cat] = (map[cat] || 0) + amt
    })
    return Object.entries(map)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
  }, [receipts])

  const maxCategorySpend = useMemo(() => {
    if (spendByCategory.length === 0) return 1
    return Math.max(...spendByCategory.map(([, v]) => v))
  }, [spendByCategory])

  // Category colors
  const categoryColors = [
    'from-primary to-secondary',
    'from-tertiary to-primary',
    'from-success to-tertiary',
    'from-secondary to-tertiary',
    'from-primary/80 to-success',
    'from-tertiary/80 to-primary/60',
  ]

  const formatTime = (seconds: number) => {
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    const mins = Math.floor(seconds / 60)
    const secs = Math.round(seconds % 60)
    return `${mins}m ${secs}s`
  }

  if (loading) {
    return (
      <div className="flex-1 w-full max-w-6xl mx-auto flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center gap-4">
          <Loader2 size={40} className="text-primary animate-spin" />
          <p className="font-sans text-white/60 text-sm">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 w-full max-w-6xl mx-auto p-6 md:p-10 animate-fade-in">
      {/* Header */}
      <div className="mb-10">
        <h1 className="font-heading text-3xl md:text-4xl font-bold text-white tracking-tight mb-2">Dashboard</h1>
        <p className="font-sans text-white/50">Real-time analytics from your receipt pipeline.</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
        
        {/* Receipts This Month */}
        <div className="glass-panel rounded-2xl p-6 border border-white/5 relative overflow-hidden group hover:border-primary/20 transition-all duration-300">
          <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -translate-y-1/2 translate-x-1/2 group-hover:scale-150 transition-transform duration-500"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2.5 rounded-xl bg-primary/10 border border-primary/20">
                <Receipt size={20} className="text-primary" />
              </div>
              <div className="flex items-center gap-1 text-success text-xs font-mono">
                <ArrowUpRight size={14} />
                <span>this month</span>
              </div>
            </div>
            <h3 className="font-mono text-4xl font-bold text-white mb-1">{receiptsThisMonth}</h3>
            <p className="font-sans text-xs text-white/40 uppercase tracking-wider">Receipts Processed</p>
          </div>
        </div>

        {/* Total Spend */}
        <div className="glass-panel rounded-2xl p-6 border border-white/5 relative overflow-hidden group hover:border-tertiary/20 transition-all duration-300">
          <div className="absolute top-0 right-0 w-32 h-32 bg-tertiary/5 rounded-full -translate-y-1/2 translate-x-1/2 group-hover:scale-150 transition-transform duration-500"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2.5 rounded-xl bg-tertiary/10 border border-tertiary/20">
                <TrendingUp size={20} className="text-tertiary" />
              </div>
              <div className="flex items-center gap-1 text-white/40 text-xs font-mono">
                all time
              </div>
            </div>
            <h3 className="font-mono text-4xl font-bold text-white mb-1">
              ${totalSpend.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </h3>
            <p className="font-sans text-xs text-white/40 uppercase tracking-wider">Total Spend</p>
          </div>
        </div>

        {/* Avg Processing Time */}
        <div className="glass-panel rounded-2xl p-6 border border-white/5 relative overflow-hidden group hover:border-success/20 transition-all duration-300">
          <div className="absolute top-0 right-0 w-32 h-32 bg-success/5 rounded-full -translate-y-1/2 translate-x-1/2 group-hover:scale-150 transition-transform duration-500"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="p-2.5 rounded-xl bg-success/10 border border-success/20">
                <Clock size={20} className="text-success" />
              </div>
              <div className="flex items-center gap-1 text-success text-xs font-mono">
                <ArrowDownRight size={14} />
                avg
              </div>
            </div>
            <h3 className="font-mono text-4xl font-bold text-white mb-1">
              {avgProcessingTime !== null ? formatTime(avgProcessingTime) : '—'}
            </h3>
            <p className="font-sans text-xs text-white/40 uppercase tracking-wider">Avg Processing Time</p>
          </div>
        </div>
      </div>

      {/* Spend by Category */}
      <div className="glass-panel rounded-2xl p-6 border border-white/5">
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
            <PieChart size={18} className="text-primary" />
          </div>
          <h2 className="font-heading text-xl font-bold text-white">Spend by Category</h2>
        </div>

        {spendByCategory.length === 0 ? (
          <p className="font-sans text-sm text-white/40 text-center py-8">No categorized expenses yet. Upload receipts to see breakdowns.</p>
        ) : (
          <div className="space-y-4">
            {spendByCategory.map(([category, amount], idx) => (
              <div key={category} className="group">
                <div className="flex justify-between items-center mb-1.5">
                  <span className="font-sans text-sm text-white/80 font-medium">{category}</span>
                  <span className="font-mono text-sm text-white font-bold">
                    ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </span>
                </div>
                <div className="w-full bg-white/5 rounded-full h-2 overflow-hidden border border-white/5">
                  <div 
                    className={`h-full rounded-full bg-gradient-to-r ${categoryColors[idx % categoryColors.length]} transition-all duration-700 ease-out`}
                    style={{ width: `${(amount / maxCategorySpend) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Activity */}
      <div className="mt-8 glass-panel rounded-2xl p-6 border border-white/5">
        <h2 className="font-heading text-xl font-bold text-white mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {receipts.slice(0, 5).map(r => (
            <div key={r.id} className="flex items-center justify-between py-2 border-b border-white/5 last:border-0">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
                  <Receipt size={14} className="text-primary" />
                </div>
                <div>
                  <p className="font-sans text-sm text-white font-medium">
                    {r.extracted_data?.vendor_name || 'Unknown Vendor'}
                  </p>
                  <p className="font-mono text-[10px] text-white/40">
                    {r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-mono text-sm text-white font-bold">
                  ${(Number(r.extracted_data?.total_amount) || 0).toFixed(2)}
                </p>
                <span className={`font-mono text-[10px] uppercase tracking-wider ${
                  r.status === 'POSTED' ? 'text-success' : 
                  r.status === 'EXTRACTED' || r.status === 'REVIEWED' ? 'text-tertiary' : 
                  'text-white/40'
                }`}>{r.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
