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

type RailIconName = "grid" | "user" | "clock" | "rocket" | "calendar" | "mail" | "list" | "circle";

function RailIcon({ name }: { name: RailIconName }) {
  const shared = { fill: "none", stroke: "currentColor", strokeWidth: 1.8, strokeLinecap: "round" as const, strokeLinejoin: "round" as const };
  switch (name) {
    case "grid":
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden>
          <rect x="4" y="4" width="6" height="6" rx="1.2" {...shared} />
          <rect x="14" y="4" width="6" height="6" rx="1.2" {...shared} />
          <rect x="4" y="14" width="6" height="6" rx="1.2" {...shared} />
          <rect x="14" y="14" width="6" height="6" rx="1.2" {...shared} />
        </svg>
      );
    case "user":
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden>
          <circle cx="12" cy="8" r="3.2" {...shared} />
          <path d="M5.5 19c1.8-3 4-4.4 6.5-4.4s4.7 1.4 6.5 4.4" {...shared} />
        </svg>
      );
    case "clock":
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden>
          <circle cx="12" cy="12" r="8" {...shared} />
          <path d="M12 8v4.5l2.8 1.7" {...shared} />
        </svg>
      );
    case "rocket":
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden>
          <path d="M12 4l5 7-5 9-5-9 5-7z" {...shared} />
          <circle cx="12" cy="11" r="1.5" {...shared} />
        </svg>
      );
    case "calendar":
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden>
          <rect x="4" y="6" width="16" height="14" rx="2" {...shared} />
          <path d="M8 4v4M16 4v4M4 10h16" {...shared} />
        </svg>
      );
    case "mail":
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden>
          <rect x="4" y="6" width="16" height="12" rx="2" {...shared} />
          <path d="M5.5 8l6.5 5 6.5-5" {...shared} />
        </svg>
      );
    case "list":
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden>
          <path d="M8 7h10M8 12h10M8 17h10" {...shared} />
          <circle cx="5" cy="7" r="1" fill="currentColor" />
          <circle cx="5" cy="12" r="1" fill="currentColor" />
          <circle cx="5" cy="17" r="1" fill="currentColor" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 24 24" className="h-4 w-4" aria-hidden>
          <circle cx="12" cy="12" r="8" {...shared} />
        </svg>
      );
  }
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  const railItems: Array<{ href: string; label: string; icon: RailIconName; active?: boolean; badge?: string }> = [
    { href: "/", label: "Dashboard", icon: "grid", active: true },
    { href: "/analisis", label: "Profil", icon: "user" },
    { href: "/analisis", label: "Activity", icon: "clock", badge: "new" },
    { href: "/analisis/baru", label: "Insight", icon: "rocket" },
    { href: "/analisis", label: "Kalender", icon: "calendar" },
    { href: "/analisis", label: "Pesan", icon: "mail" },
    { href: "/analisis", label: "Daftar", icon: "list" },
    { href: "/analisis", label: "Lainnya", icon: "circle" }
  ];

  return (
    <html lang="id">
      <body className={`${bodyFont.variable} ${headingFont.variable} font-[var(--font-body)]`}>
        <div className="ms-shell">
          <div className="ms-canvas">
            <div className="ms-layout">
              <aside className="ms-rail" aria-label="Sidebar menu">
                <nav className="ms-rail-nav">
                  {railItems.map((item) => (
                    <Link
                      key={`${item.label}-${item.icon}`}
                      href={item.href}
                      className={`ms-rail-link ${item.active ? "is-active" : ""}`}
                      aria-label={item.label}
                    >
                      <RailIcon name={item.icon} />
                      {item.badge ? <span className="ms-rail-badge">{item.badge}</span> : null}
                    </Link>
                  ))}
                </nav>
              </aside>

              <div className="ms-main">
                <header className="ms-topbar">
                  <div className="ms-topbar-left">
                    <Link href="/" className="ms-nav-link">
                      Dashboard
                    </Link>
                    <Link href="/analisis" className="ms-nav-link">
                      Workflows
                    </Link>
                    <Link href="/analisis/baru" className="ms-nav-link">
                      Integrations
                    </Link>
                    <label className="ms-search">
                      <input type="text" placeholder="Search or type command" aria-label="Search command" />
                    </label>
                  </div>

                  <div className="ms-topbar-right">
                    <span className="ms-pill">Light</span>
                    <span className="ms-pill">Data</span>
                    <Link href="/analisis" className="ms-btn-ghost">
                      Export Data
                    </Link>
                    <Link href="/analisis/baru" className="ms-btn-primary">
                      Add New Board
                    </Link>
                  </div>
                </header>

                <section className="ms-content">{children}</section>
              </div>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
