import type { AnalysisStatus } from "@/lib/types";

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("id-ID", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

export function formatCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "-";
  return new Intl.NumberFormat("id-ID", {
    style: "currency",
    currency: "IDR",
    maximumFractionDigits: 0
  }).format(value);
}

export function statusLabel(status: AnalysisStatus): string {
  const map: Record<AnalysisStatus, string> = {
    pending: "Pending",
    crawling: "Crawling",
    scraping: "Scraping",
    analyzing: "Analyzing",
    completed: "Selesai",
    failed: "Gagal"
  };
  return map[status] ?? status;
}

export function statusColor(status: AnalysisStatus): string {
  const map: Record<AnalysisStatus, string> = {
    pending: "bg-slate-100 text-slate-700",
    crawling: "bg-blue-100 text-blue-700",
    scraping: "bg-amber-100 text-amber-700",
    analyzing: "bg-indigo-100 text-indigo-700",
    completed: "bg-emerald-100 text-emerald-700",
    failed: "bg-rose-100 text-rose-700"
  };
  return map[status] ?? "bg-slate-100 text-slate-700";
}

