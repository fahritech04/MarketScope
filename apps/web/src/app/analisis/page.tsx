"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { LoadingState } from "@/components/LoadingState";
import { listAnalyses } from "@/lib/api";
import { formatDate, statusColor, statusLabel } from "@/lib/format";
import type { Analysis } from "@/lib/types";

export default function AnalysesPage() {
  const [analyses, setAnalyses] = useState<Analysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadData = async () => {
    try {
      setLoading(true);
      const result = await listAnalyses();
      setAnalyses(result);
      setError("");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Gagal memuat daftar analisis.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData().catch(() => undefined);
  }, []);

  return (
    <main className="space-y-6">
      <section className="glass-panel rounded-2xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="font-[var(--font-heading)] text-2xl font-semibold text-slate-900">Daftar Analisis</h1>
            <p className="mt-1 text-sm text-slate-600">Pantau status crawling, scraping, dan insight AI secara real-time.</p>
          </div>
          <Link href="/analisis/baru" className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700">
            Analisis Baru
          </Link>
        </div>
      </section>

      {loading ? <LoadingState message="Mengambil daftar analisis..." /> : null}
      {error ? <p className="rounded-xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      {!loading && !error && analyses.length === 0 ? (
        <section className="glass-panel rounded-2xl p-6 text-sm text-slate-600">
          Belum ada analisis. Klik <strong>Analisis Baru</strong> untuk memulai.
        </section>
      ) : null}

      <section className="grid gap-4">
        {analyses.map((analysis) => (
          <article key={analysis.id} className="glass-panel rounded-2xl p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="font-[var(--font-heading)] text-lg font-semibold text-slate-900">{analysis.topic}</h2>
                <p className="mt-1 text-sm text-slate-600">
                  Lokasi: {analysis.location || "-"} | Kategori: {analysis.category || "-"}
                </p>
                <p className="mt-1 text-xs text-slate-500">Dibuat: {formatDate(analysis.created_at)}</p>
              </div>
              <div className="flex items-center gap-3">
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusColor(analysis.status)}`}>{statusLabel(analysis.status)}</span>
                <Link href={`/analisis/${analysis.id}`} className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                  Lihat Detail
                </Link>
              </div>
            </div>
            <div className="mt-4 grid gap-3 text-sm text-slate-700 sm:grid-cols-2">
              <div className="rounded-lg bg-white/80 px-3 py-2">Jumlah sumber: {analysis.sources_count ?? 0}</div>
              <div className="rounded-lg bg-white/80 px-3 py-2">Data terambil: {analysis.items_count ?? 0}</div>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}

