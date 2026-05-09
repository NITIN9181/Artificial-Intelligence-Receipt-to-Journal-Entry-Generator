# Phase 3 Frontend Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

This will install all required packages including:
- @tanstack/react-query (server state management)
- @radix-ui/* (UI primitives)
- class-variance-authority, clsx, tailwind-merge (styling utilities)
- zustand (client state management)

### 2. Update Root Layout

**File:** `frontend/app/layout.tsx`

Add these imports at the top:
```typescript
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '@/lib/auth-context';
import { Toaster } from 'sonner';
```

Create QueryClient instance:
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      refetchOnWindowFocus: false,
    },
  },
});
```

Wrap your app:
```typescript
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

### 3. Update Dashboard Layout

**File:** `frontend/app/(dashboard)/layout.tsx`

Replace the existing layout with:
```typescript
import { Sidebar } from '@/components/navigation/Sidebar';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen bg-[#0b1326]">
      <Sidebar />
      <main className="flex-1 ml-64 pt-16">
        {children}
      </main>
    </div>
  );
}
```

### 4. Verify Backend Endpoints

Ensure your backend has these endpoints:

#### Auth
- `GET /api/v1/auth/me` → Returns `{ id, full_name, company_name, role, created_at, email }`

#### Receipts
- `GET /api/v1/receipts/pending-review` → Returns `Receipt[]`
- `GET /api/v1/receipts/my` → Returns `Receipt[]`
- `POST /api/v1/receipts/{id}/approve` → Returns `Receipt`
- `POST /api/v1/receipts/{id}/reject` → Body: `{ comment: string }`, Returns `Receipt`
- `POST /api/v1/receipts/{id}/submit` → Returns `Receipt`

#### Admin
- `GET /api/v1/admin/users` → Returns `{ users: User[], total: number }`
- `PUT /api/v1/admin/users/{id}/role` → Body: `{ role: UserRole }`, Returns `User`

### 5. Environment Variables

Ensure these are set in `.env.local`:
```env
NEXT_PUBLIC_FASTAPI_BASE_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 6. Run Development Server

```bash
npm run dev
```

Visit `http://localhost:3000`

---

## Testing Checklist

### As PREPARER:
- [ ] Can see: Dashboard, Upload, My Submissions, Journal Entries, Settings
- [ ] Can upload receipts
- [ ] Can view submissions grouped by status
- [ ] Can submit REVIEWED receipts for approval
- [ ] Can see rejection comments on REJECTED receipts
- [ ] Cannot access /approval-queue
- [ ] Cannot access /admin/users

### As REVIEWER:
- [ ] Can see: Dashboard, Approval Queue, Journal Entries, Settings
- [ ] Can see pending count badge on Approval Queue
- [ ] Can approve receipts
- [ ] Can reject receipts with comments
- [ ] Cannot access /admin/users

### As ADMIN:
- [ ] Can see all navigation items
- [ ] Can access User Management
- [ ] Can change user roles
- [ ] Can approve/reject receipts
- [ ] Can upload receipts

---

## Troubleshooting

### "Cannot find module '@/types'"
- Ensure `frontend/types/index.ts` exists
- Check `tsconfig.json` has `"@/*": ["./"]` in paths

### "useAuth must be used within AuthProvider"
- Ensure AuthProvider wraps your app in root layout
- Check QueryClientProvider is also wrapping AuthProvider

### API calls failing
- Check `NEXT_PUBLIC_FASTAPI_BASE_URL` is set correctly
- Verify backend is running
- Check browser console for CORS errors
- Verify JWT token is being sent in Authorization header

### Sidebar not showing
- Check user is authenticated
- Verify `/api/v1/auth/me` returns user with role
- Check browser console for errors

### Pending count not showing
- Verify `/api/v1/receipts/pending-review` endpoint exists
- Check user has REVIEWER or ADMIN role
- Look for query errors in React Query DevTools

---

## Optional: React Query DevTools

For debugging, add DevTools to your root layout:

```bash
npm install @tanstack/react-query-devtools
```

```typescript
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

// In your layout:
<QueryClientProvider client={queryClient}>
  <AuthProvider>
    {children}
    <ReactQueryDevtools initialIsOpen={false} />
  </AuthProvider>
</QueryClientProvider>
```

---

## File Structure

```
frontend/
├── app/
│   ├── (dashboard)/
│   │   ├── admin/
│   │   │   └── users/
│   │   │       └── page.tsx          ← User Management
│   │   ├── approval-queue/
│   │   │   └── page.tsx              ← Approval Queue
│   │   ├── submissions/
│   │   │   └── page.tsx              ← My Submissions
│   │   └── layout.tsx                ← Update this
│   └── layout.tsx                    ← Update this
├── components/
│   ├── approval/
│   │   ├── ApprovalCard.tsx
│   │   └── ReviewCommentModal.tsx
│   ├── navigation/
│   │   └── Sidebar.tsx
│   └── ui/                           ← shadcn components
│       ├── button.tsx
│       ├── badge.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       ├── dropdown-menu.tsx
│       ├── form.tsx
│       ├── input.tsx
│       ├── label.tsx
│       ├── loading-spinner.tsx
│       ├── select.tsx
│       ├── table.tsx
│       └── textarea.tsx
├── lib/
│   ├── api-client.ts                 ← Already exists
│   ├── auth-context.tsx              ← New
│   └── utils.ts                      ← New
└── types/
    └── index.ts                      ← New
```

---

## Next Steps

After Phase 3 core is working:

1. **Implement GnuCash Export** (Task 7)
   - Add export dropdown to journal entries page
   - Implement download handlers

2. **Implement COA Mapping** (Task 8)
   - Add mapping CRUD to settings page
   - Create mapping form component

3. **Add Tests**
   - Unit tests for components
   - Integration tests for workflows
   - E2E tests for critical paths

4. **Performance Optimization**
   - Add pagination to large lists
   - Implement virtual scrolling
   - Optimize image loading

5. **Accessibility Audit**
   - Keyboard navigation
   - Screen reader support
   - ARIA labels

---

**Need Help?** Check the implementation document: `PHASE_3_IMPLEMENTATION_COMPLETE.md`
