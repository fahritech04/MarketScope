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
    <main className="space-y-4">
      <section className="surface-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="chip inline-flex">Workflow Board</p>
            <h1 className="section-title mt-3 text-3xl sm:text-4xl">Daftar Analisis</h1>
            <p className="mt-1 text-sm text-muted">Pantau status crawling, scraping, dan AI insight secara real-time.</p>
          </div>
          <Link href="/analisis/baru" className="ms-btn-primary">
            Analisis Baru
          </Link>
        </div>
      </section>

      {loading ? <LoadingState message="Mengambil daftar analisis..." /> : null}
      {error ? <p className="surface-card border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">{error}</p> : null}

      {!loading && !error && analyses.length === 0 ? (
        <section className="surface-card p-6 text-sm text-muted">
          Belum ada analisis. Klik <strong>Analisis Baru</strong> untuk memulai.
        </section>
      ) : null}

      <section className="grid gap-4">
        {analyses.map((analysis) => (
          <article key={analysis.id} className="surface-card p-5">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <h2 className="section-title text-xl">{analysis.topic}</h2>
                <p className="mt-1 text-sm text-muted">
                  Lokasi: {analysis.location || "-"} | Kategori: {analysis.category || "-"}
                </p>
                <p className="mt-2 text-xs text-muted">Dibuat: {formatDate(analysis.created_at)}</p>
              </div>
              <div className="flex items-center gap-2">
                <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusColor(analysis.status)}`}>
                  {statusLabel(analysis.status)}
                </span>
                <Link href={`/analisis/${analysis.id}`} className="ms-btn-ghost">
                  Lihat Detail
                </Link>
              </div>
            </div>
            <div className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
              <div className="surface-soft px-3 py-2 text-slate-700">Jumlah sumber: {analysis.sources_count ?? 0}</div>
              <div className="surface-soft px-3 py-2 text-slate-700">Data terambil: {analysis.items_count ?? 0}</div>
            </div>
          </article>
        ))}
      </section>
    </main>
  );
}
