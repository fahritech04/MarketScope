"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { createAnalysis, runAnalysis } from "@/lib/api";

export default function NewAnalysisPage() {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const [location, setLocation] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!topic.trim()) {
      setError("Topik analisis wajib diisi.");
      return;
    }

    try {
      setLoading(true);
      setError("");
      const analysis = await createAnalysis({
        topic: topic.trim(),
        location: location.trim() || undefined,
        category: category.trim() || undefined
      });
      await runAnalysis(analysis.id);
      router.push(`/analisis/${analysis.id}`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Gagal membuat analisis.";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto max-w-3xl space-y-6">
      <section className="glass-panel rounded-2xl p-6">
        <h1 className="font-[var(--font-heading)] text-2xl font-semibold text-slate-900">Buat Analisis Baru</h1>
        <p className="mt-2 text-sm text-slate-600">
          Masukkan topik bisnis yang ingin dianalisis. Sistem akan langsung menjalankan discovery, scraping, cleaning, dan AI insight.
        </p>
      </section>

      <form onSubmit={handleSubmit} className="glass-panel space-y-5 rounded-2xl p-6">
        <div className="space-y-2">
          <label htmlFor="topic" className="text-sm font-semibold text-slate-700">
            Topik Analisis
          </label>
          <input
            id="topic"
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Masukkan topik analisis apa pun"
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none ring-brand-300 transition focus:ring-2"
          />
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label htmlFor="location" className="text-sm font-semibold text-slate-700">
              Lokasi (opsional)
            </label>
            <input
              id="location"
              value={location}
              onChange={(event) => setLocation(event.target.value)}
              placeholder="Masukkan area/lokasi (opsional)"
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none ring-brand-300 transition focus:ring-2"
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="category" className="text-sm font-semibold text-slate-700">
              Kategori (opsional)
            </label>
            <input
              id="category"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              placeholder="Masukkan kategori (opsional)"
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none ring-brand-300 transition focus:ring-2"
            />
          </div>
        </div>

        {error ? <p className="rounded-lg bg-rose-100 px-3 py-2 text-sm text-rose-700">{error}</p> : null}

        <button
          disabled={loading}
          type="submit"
          className="w-full rounded-xl bg-brand-600 px-4 py-3 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Memproses..." : "Mulai Analisis"}
        </button>
      </form>
    </main>
  );
}
