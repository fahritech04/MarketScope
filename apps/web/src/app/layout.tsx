import type { Metadata } from "next";
import { Manrope, Sora } from "next/font/google";
import Link from "next/link";

import "./globals.css";

const bodyFont = Manrope({
  subsets: ["latin"],
  variable: "--font-body"
});

const headingFont = Sora({
  subsets: ["latin"],
  variable: "--font-heading"
});

export const metadata: Metadata = {
  title: "MarketScope AI",
  description: "Dashboard intelijen pasar multi-topik berbasis scraping dan AI."
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="id">
      <body className={`${bodyFont.variable} ${headingFont.variable} font-[var(--font-body)]`}>
        <div className="mx-auto min-h-screen max-w-7xl px-4 pb-16 pt-6 sm:px-6 lg:px-8">
          <header className="mb-8 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/70 bg-white/70 px-5 py-4 shadow-soft backdrop-blur-sm">
            <Link href="/" className="font-[var(--font-heading)] text-lg font-semibold tracking-tight text-brand-800">
              MarketScope AI
            </Link>
            <nav className="flex items-center gap-4 text-sm font-medium text-slate-600">
              <Link href="/analisis">Daftar Analisis</Link>
              <Link href="/analisis/baru" className="rounded-xl bg-brand-600 px-3 py-2 text-white hover:bg-brand-700">
                Mulai Analisis
              </Link>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
