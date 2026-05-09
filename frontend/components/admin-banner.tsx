'use client'

import { useState, useMemo } from 'react'
import Link from 'next/link'
import { AlertTriangle, X } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api-client'

type UsageFlagResponse = {
  threshold_hit: boolean;
  postgres_mb: number;
  postgres_percent: number;
  requests_today: number;
  requests_percent: number;
  alert_message: string;
}

export default function AdminBanner() {
  const [dismissed, setDismissed] = useState(false)

  const { data: usage, isError } = useQuery<UsageFlagResponse>({
    queryKey: ['admin-usage'],
    queryFn: async () => {
      return await apiClient<UsageFlagResponse>('/admin/usage/flag')
    },
    // Don't refetch if the user is not admin and it throws 403
    retry: (failureCount, error: any) => {
      if (error?.status === 403) return false;
      return failureCount < 3;
    },
    refetchInterval: 60000,
  })

  const dateBefore = useMemo(() => {
    const d = new Date()
    d.setDate(d.getDate() - 90)
    return d.toISOString().split('T')[0]
  }, [])

  if (dismissed || !usage?.threshold_hit || isError) return null

  return (
    <div className="w-full bg-[#F59E0B] text-[#1f1a0d] px-4 py-3 flex items-center justify-between gap-3 shadow-md">
      <div className="flex items-center gap-3 flex-wrap">
        <AlertTriangle size={20} className="text-[#1f1a0d]" />
        <p className="font-sans text-sm font-semibold">
          {usage.alert_message || `⚠ Database usage at ${usage.postgres_percent}%. Export old data to free up space.`}
        </p>
        <Link
          href={`/journal-entries?date_to=${dateBefore}`}
          className="inline-flex items-center rounded-md bg-[#D97706] px-3 py-1.5 text-xs font-semibold text-white hover:opacity-90 transition-opacity"
        >
          Export Now
        </Link>
      </div>
      <button
        type="button"
        aria-label="Dismiss banner"
        onClick={() => setDismissed(true)}
        className="p-1 rounded hover:bg-[#D97706]/20 transition-colors"
      >
        <X size={16} />
      </button>
    </div>
  )
}
