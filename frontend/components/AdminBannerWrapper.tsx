'use client'

import dynamic from 'next/dynamic'

const AdminBanner = dynamic(() => import('@/components/AdminBanner'), { ssr: false })

export default function AdminBannerWrapper() {
  return <AdminBanner />
}
