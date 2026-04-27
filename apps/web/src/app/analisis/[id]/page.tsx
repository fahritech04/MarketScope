"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { ChartsSection } from "@/components/ChartsSection";
import { LoadingState } from "@/components/LoadingState";
import { StatCard } from "@/components/StatCard";
import { getAnalysis, getInsights, getItems, getSources, runAnalysis } from "@/lib/api";
import { formatCurrency, formatDate, statusColor, statusLabel } from "@/lib/format";
import type { Analysis, Insight, ScrapedItem, Source } from "@/lib/types";

export default function AnalysisDetailPage() {
  const params = useParams<{ id: string }>();
  const analysisId = params.id;

  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [sources, setSources] = useState<Source[]>([]);
  const [items, setItems] = useState<ScrapedItem[]>([]);
  const [insight, setInsight] = useState<Insight | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const activeStatuses = useMemo(() => new Set(["pending", "crawling", "scraping", "analyzing"]), []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [analysisData, sourcesData, itemsData, insightData] = await Promise.all([
        getAnalysis(analysisId),
        getSources(analysisId),
        getItems(analysisId),
        getInsights(analysisId)
      ]);
      setAnalysis(analysisData);
      setSources(sourcesData);
      setItems(itemsData);
      setInsight(insightData);
      setError("");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Gagal memuat detail analisis.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleRun = async () => {
    try {
      setRunning(true);
      await runAnalysis(analysisId);
      await loadData();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Gagal menjalankan analisis.";
      setError(message);
    } finally {
      setRunning(false);
    }
  };

  useEffect(() => {
    loadData().catch(() => undefined);
  }, [analysisId]);

  useEffect(() => {
    if (!analysis || !activeStatuses.has(analysis.status)) return;
    const timer = setInterval(() => {
      loadData().catch(() => undefined);
    }, 6000);
    return () => clearInterval(timer);
  }, [analysis, activeStatuses]);

  const averagePrice = useMemo(() => {
    const values = items.map((item) => item.price_min).filter((value): value is number => value !== null);
    if (!values.length) return null;
    return values.reduce((acc, cur) => acc + cur, 0) / values.length;
  }, [items]);

  const averageRating = useMemo(() => {
    const values = items.map((item) => item.rating).filter((value): value is number => value !== null);
    if (!values.length) return null;
    return values.reduce((acc, cur) => acc + cur, 0) / values.length;
  }, [items]);

  if (loading && !analysis) {
    return <LoadingState message="Memuat detail analisis..." />;
  }

  if (error && !analysis) {
    return <p className="rounded-xl bg-rose-100 px-4 py-3 text-sm text-rose-700">{error}</p>;
  }

  return (
    <main className="space-y-5">
      {analysis ? (
        <section className="glass-panel rounded-2xl p-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-xs uppercase tracking-wider text-slate-500">Detail Analisis</p>
              <h1 className="mt-1 font-[var(--font-heading)] text-2xl font-semibold text-slate-900">{analysis.topic}</h1>
              <p className="mt-1 text-sm text-slate-600">
                Lokasi: {analysis.location || "-"} | Kategori: {analysis.category || "-"}
              </p>
              <p className="mt-1 text-xs text-slate-500">Dibuat: {formatDate(analysis.created_at)}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${statusColor(analysis.status)}`}>{statusLabel(analysis.status)}</span>
              <button
                type="button"
                onClick={handleRun}
                disabled={running || activeStatuses.has(analysis.status)}
                className="rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {running ? "Menjalankan..." : "Jalankan Ulang"}
              </button>
            </div>
          </div>
          {error ? <p className="mt-4 rounded-lg bg-rose-100 px-3 py-2 text-sm text-rose-700">{error}</p> : null}
        </section>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Jumlah Sumber" value={sources.length} />
        <StatCard label="Data Berhasil Diambil" value={items.length} />
        <StatCard label="Rata-rata Harga" value={formatCurrency(averagePrice)} />
        <StatCard label="Rata-rata Rating" value={averageRating ? averageRating.toFixed(2) : "-"} />
      </section>

      <ChartsSection sources={sources} items={items} />

      <section className="grid gap-4 lg:grid-cols-2">
        <article className="glass-panel rounded-2xl p-5">
          <h2 className="font-[var(--font-heading)] text-lg font-semibold text-slate-900">Insight AI</h2>
          <p className="mt-3 text-sm leading-6 text-slate-700">{insight?.summary || "Insight belum tersedia."}</p>

          <h3 className="mt-5 text-sm font-semibold text-slate-900">Peluang</h3>
          <ul className="mt-2 space-y-1 text-sm text-slate-700">
            {(insight?.opportunities || []).map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>

          <h3 className="mt-5 text-sm font-semibold text-slate-900">Strategi Rekomendasi</h3>
          <ul className="mt-2 space-y-1 text-sm text-slate-700">
            {(insight?.strategy_recommendations || []).map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </article>

        <article className="glass-panel rounded-2xl p-5">
          <h2 className="font-[var(--font-heading)] text-lg font-semibold text-slate-900">Sinyal Kompetitor & Pain Points</h2>
          <h3 className="mt-4 text-sm font-semibold text-slate-900">Kompetitor</h3>
          <ul className="mt-2 space-y-1 text-sm text-slate-700">
            {(insight?.competitors || []).map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>

          <h3 className="mt-4 text-sm font-semibold text-slate-900">Pricing Insight</h3>
          <p className="mt-2 text-sm text-slate-700">{insight?.pricing_insight || "-"}</p>

          <h3 className="mt-4 text-sm font-semibold text-slate-900">Pain Points Pelanggan</h3>
          <ul className="mt-2 space-y-1 text-sm text-slate-700">
            {(insight?.customer_pain_points || []).map((item) => (
              <li key={item}>- {item}</li>
            ))}
          </ul>
        </article>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <article className="glass-panel overflow-x-auto rounded-2xl p-5">
          <h2 className="mb-3 font-[var(--font-heading)] text-lg font-semibold text-slate-900">Tabel Sumber Data</h2>
          <table className="w-full min-w-[520px] text-left text-sm">
            <thead className="text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="pb-2">Judul</th>
                <th className="pb-2">URL</th>
                <th className="pb-2">Status</th>
              </tr>
            </thead>
            <tbody className="text-slate-700">
              {sources.map((source) => (
                <tr key={source.id} className="border-t border-slate-100">
                  <td className="py-2">{source.title || "-"}</td>
                  <td className="py-2">
                    <a href={source.url} target="_blank" rel="noreferrer" className="text-brand-700 underline underline-offset-2">
                      Buka
                    </a>
                  </td>
                  <td className="py-2">{source.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>

        <article className="glass-panel overflow-x-auto rounded-2xl p-5">
          <h2 className="mb-3 font-[var(--font-heading)] text-lg font-semibold text-slate-900">Tabel Hasil Scraping</h2>
          <table className="w-full min-w-[620px] text-left text-sm">
            <thead className="text-xs uppercase tracking-wider text-slate-500">
              <tr>
                <th className="pb-2">Nama</th>
                <th className="pb-2">Alamat</th>
                <th className="pb-2">Harga</th>
                <th className="pb-2">Rating</th>
              </tr>
            </thead>
            <tbody className="text-slate-700">
              {items.map((item) => (
                <tr key={item.id} className="border-t border-slate-100">
                  <td className="py-2">{item.name || "-"}</td>
                  <td className="py-2">{item.address || "-"}</td>
                  <td className="py-2">{item.price_text || "-"}</td>
                  <td className="py-2">{item.rating ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </article>
      </section>
    </main>
  );
}

