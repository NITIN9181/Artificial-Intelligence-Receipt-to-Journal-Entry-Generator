import Link from "next/link";
import { Bell, BarChart3, Receipt, Settings, FileText } from "lucide-react";
import { SidebarNav } from "@/components/sidebar-nav";
import AdminBanner from "@/components/admin-banner";
import { createClient } from "@/utils/supabase/server";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  return (
    <div className="flex-1 w-full flex flex-col md:flex-row relative z-10 min-h-screen overflow-x-hidden">
      {/* SideNavBar (WEB) */}
      <SidebarNav userEmail={user?.email || undefined} />


      {/* Main Content + Top Nav Wrapper */}
      <div className="flex-1 flex flex-col md:ml-64 w-full relative z-10">
        {/* TopNavBar (WEB) */}
        <header className="hidden md:flex w-full justify-between items-center px-8 h-20">
          <div className="flex space-x-8"></div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-4 text-white/60">
              <Bell className="w-5 h-5 cursor-pointer hover:text-white hover:bg-white/5 transition-colors p-1.5 box-content rounded-full active:scale-95 duration-200" />
              <Link href="/settings">
                <Settings className="w-5 h-5 cursor-pointer hover:text-white hover:bg-white/5 transition-colors p-1.5 box-content rounded-full active:scale-95 duration-200" />
              </Link>
            </div>
          </div>
        </header>

        {/* Admin Banner (only visible to admins when threshold hit) */}
        <AdminBanner />

        {/* Main Content Area */}
        <main className="flex-1 w-full pb-20 md:pb-0">
          {children}
        </main>
      </div>

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
      
      {/* BottomNavBar (MOBILE) */}
      <nav className="md:hidden fixed bottom-0 left-0 w-full z-50 flex justify-around items-center px-6 pb-6 pt-3 bg-background/80 backdrop-blur-[30px] border-t border-white/10 rounded-t-[32px] shadow-[0_-10px_40px_rgba(0,0,0,0.5)]">
        <Link href="/dashboard" className="flex flex-col items-center justify-center text-white/40 p-3 hover:text-primary active:scale-90 transition-transform">
          <BarChart3 className="w-6 h-6 mb-1" />
          <span className="font-heading text-[10px] font-bold">Stats</span>
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
