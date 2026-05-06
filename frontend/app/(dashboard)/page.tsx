import { redirect } from 'next/navigation'

export default function DashboardIndexPage() {
  // Redirect immediately to /dashboard
  redirect('/dashboard')
}
