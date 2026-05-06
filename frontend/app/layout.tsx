import type { Metadata } from "next";
import { Inter, Manrope, Space_Grotesk } from "next/font/google";
import "./globals.css";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"], variable: '--font-inter' });
const manrope = Manrope({ subsets: ["latin"], variable: '--font-manrope' });
const spaceGrotesk = Space_Grotesk({ subsets: ["latin"], variable: '--font-space-grotesk' });

export const metadata: Metadata = {
  title: "LedgerFlow - Atmospheric Bookkeeping",
  description: "Automated bookkeeping with Atmospheric Intelligence.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} ${manrope.variable} ${spaceGrotesk.variable} antialiased min-h-screen flex flex-col relative overflow-x-hidden`}>
        {/* Ambient Background Glows */}
        <div className="ambient-glow bg-primary w-[500px] h-[500px] top-[-100px] left-[-100px]"></div>
        <div className="ambient-glow bg-secondary w-[600px] h-[600px] bottom-[-200px] right-[-100px]"></div>
        
        {children}
        
        <Toaster position="bottom-right" richColors theme="dark" />
      </body>
    </html>
  );
}
