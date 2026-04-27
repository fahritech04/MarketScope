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
    <main className="space-y-4">
      <section className="surface-card p-6">
        <p className="chip inline-flex">Create Workspace</p>
        <h1 className="section-title mt-3 text-3xl sm:text-4xl">Buat Analisis Baru</h1>
        <p className="mt-2 text-sm text-muted">
          Masukkan topik bisnis yang ingin dianalisis. Sistem akan langsung menjalankan discovery, scraping, cleaning, dan AI insight.
        </p>
      </section>

      <form onSubmit={handleSubmit} className="surface-card space-y-5 p-6">
        <div className="space-y-2">
          <label htmlFor="topic" className="text-sm font-semibold text-slate-700">
            Topik Analisis
          </label>
          <input
            id="topic"
            value={topic}
            onChange={(event) => setTopic(event.target.value)}
            placeholder="Masukkan topik analisis apa pun"
            className="w-full rounded-xl border border-[#e8e8f3] bg-[#fbfbff] px-4 py-3 text-sm outline-none ring-violet-300 transition focus:ring-2"
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
              className="w-full rounded-xl border border-[#e8e8f3] bg-[#fbfbff] px-4 py-3 text-sm outline-none ring-violet-300 transition focus:ring-2"
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
              className="w-full rounded-xl border border-[#e8e8f3] bg-[#fbfbff] px-4 py-3 text-sm outline-none ring-violet-300 transition focus:ring-2"
            />
          </div>
        </div>

        {error ? <p className="rounded-lg bg-rose-100 px-3 py-2 text-sm text-rose-700">{error}</p> : null}

        <button
          disabled={loading}
          type="submit"
          className="w-full rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 px-4 py-3 text-sm font-semibold text-white hover:opacity-95 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Memproses..." : "Mulai Analisis"}
        </button>
      </form>
    </main>
  );
}
