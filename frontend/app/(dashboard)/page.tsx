import { redirect } from 'next/navigation'

export default function DashboardIndexPage() {
  // Redirect immediately to /upload
  redirect('/upload')
}
