# Phase 3 - Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Step 1: Install Dependencies (2 min)
```bash
cd frontend
npm install
```

### Step 2: Update Root Layout (1 min)
**File:** `app/layout.tsx`

```typescript
'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/lib/auth-context';
import { Toaster } from 'sonner';
import './globals.css';

const queryClient = new QueryClient();

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            {children}
            <Toaster position="top-right" richColors />
          </AuthProvider>
        </QueryClientProvider>
      </body>
    </html>
  );
}
```

### Step 3: Update Dashboard Layout (1 min)
**File:** `app/(dashboard)/layout.tsx`

```typescript
import { Sidebar } from '@/components/navigation/Sidebar';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#0b1326]">
      <Sidebar />
      <main className="flex-1 ml-64">
        {children}
      </main>
    </div>
  );
}
```

### Step 4: Run Dev Server (1 min)
```bash
npm run dev
```

Visit: `http://localhost:3000`

---

## ✅ Test It Works

### As PREPARER:
1. Login
2. Check sidebar shows: Dashboard, Upload, My Submissions, Journal Entries, Settings
3. Go to `/submissions` - should see your receipts grouped by status
4. Try submitting a REVIEWED receipt

### As REVIEWER:
1. Login
2. Check sidebar shows: Dashboard, Approval Queue, Journal Entries, Settings
3. Go to `/approval-queue` - should see pending receipts
4. Try approving or rejecting a receipt

### As ADMIN:
1. Login
2. Check sidebar shows all items including User Management
3. Go to `/admin/users` - should see all users
4. Try changing a user's role

---

## 🐛 Troubleshooting

### "Cannot find module '@/types'"
```bash
# Check tsconfig.json has:
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./*"]
    }
  }
}
```

### API calls failing
1. Check `.env.local` has `NEXT_PUBLIC_FASTAPI_BASE_URL`
2. Verify backend is running
3. Check browser console for errors

### Sidebar not showing
1. Verify user is authenticated
2. Check `/api/v1/auth/me` returns user with role
3. Look for errors in browser console

---

## 📚 Full Documentation

- **Setup Guide:** `SETUP_PHASE3.md`
- **Implementation Details:** `../PHASE_3_IMPLEMENTATION_COMPLETE.md`
- **Summary:** `../PHASE_3_SUMMARY.md`

---

## 🎯 What You Get

✅ Role-based navigation
✅ Approval queue for reviewers
✅ Submissions tracking for preparers
✅ User management for admins
✅ Real-time updates
✅ Toast notifications
✅ Loading states
✅ Error handling
✅ Beautiful UI with glassmorphism

---

**That's it! You're ready to go.** 🎉
