"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/lib/auth-context';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { cn } from '@/lib/utils';
import { UserRole } from '@/types';
import {
  Home,
  Upload,
  FileText,
  BookOpen,
  Settings,
  ClipboardCheck,
  Users,
  Receipt,
} from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  badge?: string | number;
}

const NAV_ITEMS: Record<UserRole, NavItem[]> = {
  PREPARER: [
    { label: 'Dashboard', href: '/dashboard', icon: Home },
    { label: 'Upload', href: '/upload', icon: Upload },
    { label: 'My Submissions', href: '/submissions', icon: FileText },
    { label: 'Journal Entries', href: '/journal-entries', icon: BookOpen },
    { label: 'Settings', href: '/settings', icon: Settings },
  ],
  REVIEWER: [
    { label: 'Dashboard', href: '/dashboard', icon: Home },
    { label: 'Approval Queue', href: '/approval-queue', icon: ClipboardCheck },
    { label: 'Journal Entries', href: '/journal-entries', icon: BookOpen },
    { label: 'Settings', href: '/settings', icon: Settings },
  ],
  ADMIN: [
    { label: 'Dashboard', href: '/dashboard', icon: Home },
    { label: 'Upload', href: '/upload', icon: Upload },
    { label: 'Approval Queue', href: '/approval-queue', icon: ClipboardCheck },
    { label: 'Journal Entries', href: '/journal-entries', icon: BookOpen },
    { label: 'User Management', href: '/admin/users', icon: Users },
    { label: 'Settings', href: '/settings', icon: Settings },
  ],
};

export function Sidebar() {
  const { user, isReviewer } = useAuth();
  const pathname = usePathname();

  // Fetch pending count for reviewer badge
  const { data: pendingCount } = useQuery({
    queryKey: ['pending-review-count'],
    queryFn: async () => {
      if (!isReviewer) return 0;
      try {
        const receipts = await apiClient<any[]>('/receipts/pending-review');
        return receipts?.length || 0;
      } catch {
        return 0;
      }
    },
    enabled: isReviewer,
    refetchInterval: 30000,
  });

  if (!user) return null;

  const items = NAV_ITEMS[user.role] || NAV_ITEMS.PREPARER;

  return (
    <aside className="w-64 h-screen bg-[#0b1326] border-r border-white/10 flex flex-col fixed left-0 top-0 z-40">
      <div className="p-6">
        <h1 className="text-xl font-bold text-[#c0c1ff] font-[Manrope] flex items-center gap-2">
          <Receipt className="w-6 h-6" />
          LedgerFlow
        </h1>
      </div>

      <nav className="flex-1 px-4 space-y-1">
        {items.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                isActive
                  ? "bg-[#c0c1ff]/10 text-[#c0c1ff]"
                  : "text-[#dae2fd]/70 hover:text-[#dae2fd] hover:bg-white/5"
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="flex-1">{item.label}</span>
              {item.href === '/approval-queue' && pendingCount ? (
                <Badge variant="secondary" className="bg-[#ddb7ff] text-[#0b1326]">
                  {pendingCount}
                </Badge>
              ) : null}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-3 px-4 py-2">
          <div className="w-8 h-8 rounded-full bg-[#c0c1ff]/20 flex items-center justify-center">
            <span className="text-xs font-bold text-[#c0c1ff]">
              {user.full_name?.[0] || user.email?.[0] || 'U'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-[#dae2fd] truncate">
              {user.full_name || user.email || 'User'}
            </p>
            <p className="text-xs text-[#dae2fd]/50 capitalize">{user.role.toLowerCase()}</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
