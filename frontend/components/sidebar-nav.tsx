'use client'

import Link from "next/link"
import { usePathname } from "next/navigation"
import { Receipt, Settings, UserCircle, LogOut, FileText, BarChart3 } from "lucide-react"

interface NavItem {
  label: string
  href: string
  icon: any
  activePattern?: string
}

const navItems: NavItem[] = [
  { 
    label: "Dashboard", 
    href: "/dashboard", 
    icon: BarChart3,
    activePattern: "/dashboard"
  },
  { 
    label: "Receipts", 
    href: "/upload", 
    icon: Receipt,
    activePattern: "/upload"
  },
  { 
    label: "Journal Entries", 
    href: "/journal-entries", 
    icon: FileText,
    activePattern: "/journal-entries"
  },
]

export function SidebarNav({ userEmail }: { userEmail?: string }) {
  const pathname = usePathname()

  return (
    <nav className="hidden md:flex flex-col fixed left-0 top-0 h-full w-64 bg-black/40 backdrop-blur-[40px] border-r border-white/5 shadow-[20px_0_40px_rgba(0,0,0,0.5)] z-40 py-8 transition-all duration-300 ease-in-out">
      <div className="px-8 mb-12">
        <h1 className="font-heading text-2xl font-black text-white tracking-tighter drop-shadow-[0_0_10px_rgba(192,193,255,0.5)] flex items-center gap-2">
          <Receipt className="text-primary w-6 h-6" />
          LedgerFlow
        </h1>
        <div className="mt-6 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center text-white/80 border border-white/20">
            <UserCircle size={24} />
          </div>
          <div>
            <h2 className="font-sans text-sm text-white font-medium truncate w-32">{userEmail || "User"}</h2>
          </div>
        </div>
      </div>

      <div className="flex-1 px-4 space-y-2">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.activePattern || item.href)
          
          return (
            <Link 
              key={item.href}
              href={item.href} 
              className={`flex items-center gap-4 px-4 py-3 rounded-lg transition-all duration-300 ease-in-out font-heading text-sm font-semibold tracking-wide ${
                isActive 
                  ? "bg-gradient-to-r from-primary-container/20 to-secondary-container/20 text-white border-r-2 border-secondary" 
                  : "text-white/40 hover:bg-white/5 hover:text-white"
              }`}
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </Link>
          )
        })}
      </div>

      <div className="px-6 mt-8">
        <Link href="/upload" className="flex justify-center w-full py-3 rounded-xl bg-gradient-to-r from-primary to-secondary text-background font-heading text-sm font-bold tracking-wide shadow-[0_0_20px_rgba(192,193,255,0.3)] hover:shadow-[0_0_30px_rgba(192,193,255,0.5)] transition-shadow">
          Quick Scan
        </Link>
      </div>

      <div className="px-4 mt-8">
        <form action="/api/auth/signout" method="post">
          <button type="submit" className="flex items-center gap-4 px-4 py-3 w-full rounded-lg text-white/40 hover:bg-white/5 hover:text-white transition-all duration-300 ease-in-out font-heading text-sm font-semibold tracking-wide">
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </form>
      </div>
    </nav>
  )
}
