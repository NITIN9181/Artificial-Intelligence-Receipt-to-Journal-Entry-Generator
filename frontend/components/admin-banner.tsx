'use client'

import { useEffect, useMemo, useState } from 'react'
import Link from 'next/link'
import { X } from 'lucide-react'
import { ApiError, apiClient } from '@/lib/api-client'

type UsagePayload = {
  storage_percent?: number
  requests_percent?: number
  db_size_percent?: number
}

function getMessage(usage: UsagePayload): string | null {
  const candidates = [
    { key: 'storage', value: usage.storage_percent ?? 0, label: 'Storage usage' },
    { key: 'requests', value: usage.requests_percent ?? 0, label: 'API request usage' },
    { key: 'db', value: usage.db_size_percent ?? 0, label: 'Database usage' },
  ]
  const breach = candidates.filter((c) => c.value >= 80).sort((a, b) => b.value - a.value)[0]
  if (!breach) return null
  return `⚠ ${breach.label} at ${Math.round(breach.value)}%. Export old data to free up space.`
}

export default function AdminBanner() {
  const [usage, setUsage] = useState<UsagePayload | null>(null)
  const [dismissed, setDismissed] = useState(false)
  const [shouldPoll, setShouldPoll] = useState(true)

  const dateBefore = useMemo(() => {
    const d = new Date()
    d.setDate(d.getDate() - 90)
    return d.toISOString().split('T')[0]
  }, [])

  useEffect(() => {
    let mounted = true

    const loadUsage = async () => {
      try {
        const data = await apiClient<UsagePayload>('/admin/usage')
        if (!mounted) return
        setUsage(data)
      } catch (error) {
        if (error instanceof ApiError && error.status === 403) {
          if (!mounted) return
          setShouldPoll(false)
          return
        }
      }
    }

    loadUsage()
    if (!shouldPoll) {
      return () => {
        mounted = false
      }
    }

    const interval = setInterval(loadUsage, 60_000)
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [shouldPoll])

  if (dismissed || !usage) return null

  const message = getMessage(usage)
  if (!message) return null

  return (
    <div className="w-full bg-[#F59E0B] text-[#1f1a0d] px-4 py-3 flex items-center justify-between gap-3">
      <div className="flex items-center gap-3 flex-wrap">
        <p className="font-sans text-sm font-semibold">{message}</p>
        <Link
          href={`/journal-entries?date_before=${dateBefore}`}
          className="inline-flex items-center rounded-md bg-[#D97706] px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90 transition-opacity"
        >
          Export Old Entries
        </Link>
      </div>
      <button
        type="button"
        aria-label="Dismiss banner"
        onClick={() => setDismissed(true)}
        className="p-1 rounded hover:bg-[#D97706]/20"
      >
        <X size={16} />
      </button>
    </div>
  )
}
