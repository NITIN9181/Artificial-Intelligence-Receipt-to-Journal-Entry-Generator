import Link from "next/link";
import { Receipt, Settings, UserCircle, LogOut, Home, FileText, HelpCircle, Bell } from "lucide-react";
import { createClient } from "@/utils/supabase/server";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  return (
    <div className="flex-1 w-full flex flex-col md:flex-row relative z-10">
      {/* SideNavBar (WEB) */}
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
              <h2 className="font-sans text-sm text-white font-medium truncate w-32">{user?.email || "User"}</h2>
              <span className="font-mono text-[10px] text-tertiary uppercase tracking-widest">Premium Tier</span>
            </div>
          </div>
        </div>

        <div className="flex-1 px-4 space-y-2">
          <Link href="/" className="flex items-center gap-4 px-4 py-3 rounded-lg text-white/40 hover:bg-white/5 hover:text-white transition-all duration-300 ease-in-out font-heading text-sm font-semibold tracking-wide">
            <Home className="w-5 h-5" />
            Home
          </Link>
          <Link href="/upload" className="flex items-center gap-4 px-4 py-3 rounded-lg bg-gradient-to-r from-primary-container/20 to-secondary-container/20 text-white border-r-2 border-secondary transition-all duration-300 ease-in-out font-heading text-sm font-semibold tracking-wide">
            <Receipt className="w-5 h-5" />
            Receipts
          </Link>
          <Link href="/journal-entries" className="flex items-center gap-4 px-4 py-3 rounded-lg text-white/40 hover:bg-white/5 hover:text-white transition-all duration-300 ease-in-out font-heading text-sm font-semibold tracking-wide">
            <FileText className="w-5 h-5" />
            Journal Entries
          </Link>
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

      {/* TopNavBar (WEB) */}
      <header className="hidden md:flex fixed top-0 w-full z-30 justify-between items-center px-8 h-16 bg-background/40 backdrop-blur-[20px] border-b border-white/10 shadow-[0_8px_32px_0_rgba(0,0,0,0.37)] pl-[calc(16rem+2rem)]">
        <div className="flex space-x-8"></div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4 text-white/60">
            <Bell className="w-5 h-5 cursor-pointer hover:text-white hover:bg-white/5 transition-colors p-1.5 box-content rounded-full active:scale-95 duration-200" />
            <Link href="/settings">
              <Settings className="w-5 h-5 cursor-pointer hover:text-white hover:bg-white/5 transition-colors p-1.5 box-content rounded-full active:scale-95 duration-200" />
            </Link>
          </div>
          <button className="px-5 py-2 rounded-full border border-white/20 text-white font-sans text-sm hover:bg-white/10 transition-colors">
            Upgrade
          </button>
        </div>
      </header>

      {/* Mobile NavBar */}
      <header className="md:hidden flex items-center justify-between p-4 bg-background/80 backdrop-blur-md border-b border-white/10 fixed top-0 w-full z-30">
        <h1 className="font-heading text-lg font-bold text-white tracking-tighter flex items-center gap-2">
          <Receipt className="text-primary w-5 h-5" />
          LedgerFlow
        </h1>
        <Link href="/settings" className="text-white/60 p-2">
          <Settings size={20} />
        </Link>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 w-full flex flex-col md:ml-64 md:pt-16 pt-16 relative z-10 pb-20 md:pb-0 min-h-screen">
        {children}
      </main>
      
      {/* BottomNavBar (MOBILE) */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-6 pb-6 pt-3 bg-background/80 backdrop-blur-[30px] border-t border-white/10 rounded-t-[32px] shadow-[0_-10px_40px_rgba(0,0,0,0.5)]">
        <Link href="/" className="flex flex-col items-center justify-center text-white/40 p-3 hover:text-primary active:scale-90 transition-transform">
          <Home className="w-6 h-6 mb-1" />
          <span className="font-heading text-[10px] font-bold">Home</span>
        </Link>
        <Link href="/upload" className="flex flex-col items-center justify-center bg-gradient-to-r from-primary to-secondary text-background rounded-2xl p-4 shadow-[0_0_15px_rgba(192,193,255,0.4)] active:scale-90 transition-transform -mt-6 border border-white/20">
          <Receipt className="w-6 h-6" />
        </Link>
        <Link href="/journal-entries" className="flex flex-col items-center justify-center text-white/40 p-3 hover:text-primary active:scale-90 transition-transform">
          <FileText className="w-6 h-6 mb-1" />
          <span className="font-heading text-[10px] font-bold">Entries</span>
        </Link>
      </nav>
    </div>
  );
}
