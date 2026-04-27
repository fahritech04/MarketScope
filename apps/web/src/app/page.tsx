import Link from "next/link";

export default function HomePage() {
  return (
    <main className="space-y-8">
      <section className="glass-panel relative overflow-hidden rounded-3xl p-8 sm:p-12">
        <div className="absolute -right-10 -top-8 h-32 w-32 rounded-full bg-brand-200/70 blur-2xl" />
        <div className="absolute bottom-0 left-0 h-24 w-24 rounded-full bg-emerald-200/50 blur-2xl" />
        <div className="relative max-w-3xl space-y-4">
          <p className="inline-flex rounded-full bg-brand-100 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-brand-700">
            Market Intelligence untuk UMKM
          </p>
          <h1 className="font-[var(--font-heading)] text-3xl font-semibold leading-tight text-slate-900 sm:text-5xl">
            Temukan peluang pasar lebih cepat dengan scraping + AI.
          </h1>
          <p className="text-base text-slate-600 sm:text-lg">
            MarketScope AI membantu kamu menganalisis kompetitor, harga, review, dan peluang bisnis dari berbagai sumber web publik.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link href="/analisis/baru" className="rounded-xl bg-brand-600 px-5 py-3 text-sm font-semibold text-white hover:bg-brand-700">
              Mulai Analisis
            </Link>
            <Link href="/analisis" className="rounded-xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
              Lihat Daftar Analisis
            </Link>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="glass-panel rounded-2xl p-5">
          <h2 className="font-[var(--font-heading)] text-xl font-semibold text-slate-900">Topik Bebas</h2>
          <p className="mt-4 text-sm text-slate-700">
            Masukkan topik apa pun sesuai kebutuhanmu. Sistem akan menyesuaikan discovery, scraping, dan analisis secara dinamis berdasarkan input terbaru.
          </p>
        </article>
        <article className="glass-panel rounded-2xl p-5">
          <h2 className="font-[var(--font-heading)] text-xl font-semibold text-slate-900">Cara Kerja Singkat</h2>
          <ol className="mt-4 space-y-2 text-sm text-slate-700">
            <li>1. Masukkan topik yang ingin dianalisis.</li>
            <li>2. Sistem menemukan sumber web publik relevan.</li>
            <li>3. Data dibersihkan, dianalisis AI, lalu ditampilkan dalam dashboard.</li>
          </ol>
        </article>
      </section>
    </main>
  );
}
