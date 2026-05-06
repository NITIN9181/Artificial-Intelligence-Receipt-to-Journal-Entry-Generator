'use client'

import { useState, useEffect } from 'react'
import { fetchApi } from '@/utils/apiClient'
import { AlertTriangle, X, Download } from 'lucide-react'
import Link from 'next/link'

export default function AdminBanner() {
  const [visible, setVisible] = useState(false)
  const [usageData, setUsageData] = useState<any>(null)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    checkUsage()
  }, [])

  const checkUsage = async () => {
    try {
      const data = await fetchApi('/admin/usage')
      setUsageData(data)
      if (data.alert_active) {
        setVisible(true)
      }
    } catch {
      // Non-admin users will get 403 — silently ignore
      setVisible(false)
    }
  }

  if (!visible || dismissed || !usageData) return null

  const highestPct = Math.max(
    usageData.postgres_threshold_pct || 0,
    usageData.storage_threshold_pct || 0,
    usageData.requests_threshold_pct || 0,
  )

  // Build 90-days-ago date for export link filter
  const ninetyDaysAgo = new Date()
  ninetyDaysAgo.setDate(ninetyDaysAgo.getDate() - 90)
  const dateParam = ninetyDaysAgo.toISOString().split('T')[0]

  return (
    <div className="w-full bg-gradient-to-r from-warning/20 via-error/10 to-warning/20 border-b border-warning/30 px-6 py-3 flex items-center justify-between animate-fade-in backdrop-blur-sm">
      <div className="flex items-center gap-3">
        <div className="p-1.5 rounded-lg bg-warning/20 border border-warning/30">
          <AlertTriangle size={16} className="text-warning" />
        </div>
        <p className="font-sans text-sm text-white">
          <span className="font-bold text-warning">⚠ Database usage at {highestPct.toFixed(0)}%.</span>
          {' '}Export old data to free up space.
        </p>
        <Link 
          href={`/journal-entries?export=true&date_to=${dateParam}`}
          className="ml-2 px-3 py-1 rounded-full bg-warning/20 border border-warning/30 text-warning font-sans text-xs font-bold hover:bg-warning/30 transition-colors flex items-center gap-1.5"
        >
          <Download size={12} />
          Export &gt; 90 days
        </Link>
      </div>
      <button 
        onClick={() => setDismissed(true)} 
        className="text-white/40 hover:text-white transition-colors p-1"
        aria-label="Dismiss banner"
      >
        <X size={16} />
      </button>
    </div>
  )
}
