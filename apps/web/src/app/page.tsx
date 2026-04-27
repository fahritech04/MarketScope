 "use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

function pad2(value: number): string {
  return String(value).padStart(2, "0");
}

export default function HomePage() {
  const [now, setNow] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const monthLabel = useMemo(
    () =>
      new Intl.DateTimeFormat("en-US", {
        month: "long",
        year: "numeric"
      }).format(now),
    [now]
  );

  const fullDateLabel = useMemo(
    () =>
      new Intl.DateTimeFormat("id-ID", {
        weekday: "long",
        day: "2-digit",
        month: "long",
        year: "numeric"
      }).format(now),
    [now]
  );

  const clockLabel = useMemo(
    () =>
      `${pad2(now.getHours())}:${pad2(now.getMinutes())}:${pad2(now.getSeconds())}`,
    [now]
  );

  const calendarDays = useMemo(() => {
    const year = now.getFullYear();
    const month = now.getMonth();
    const firstOfMonth = new Date(year, month, 1);
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const mondayStartOffset = (firstOfMonth.getDay() + 6) % 7;

    const grid: Array<number | null> = [];
    for (let i = 0; i < mondayStartOffset; i += 1) grid.push(null);
    for (let day = 1; day <= daysInMonth; day += 1) grid.push(day);
    while (grid.length % 7 !== 0) grid.push(null);
    return grid;
  }, [now]);

  const timeSlotA = useMemo(() => {
    const start = new Date(now.getTime());
    const end = new Date(now.getTime() + 30 * 60 * 1000);
    return `${pad2(start.getHours())}:${pad2(start.getMinutes())}-${pad2(end.getHours())}:${pad2(end.getMinutes())}`;
  }, [now]);

  const timeSlotB = useMemo(() => {
    const start = new Date(now.getTime() + 60 * 60 * 1000);
    const end = new Date(now.getTime() + 120 * 60 * 1000);
    return `${pad2(start.getHours())}:${pad2(start.getMinutes())}-${pad2(end.getHours())}:${pad2(end.getMinutes())}`;
  }, [now]);

  return (
    <main className="space-y-4">
      <section className="grid gap-4 lg:grid-cols-[1.5fr_1fr]">
        <article className="surface-card p-6 sm:p-8">
          <p className="chip inline-flex">Creative Dashboard</p>
          <h1 className="section-title mt-4 text-3xl leading-tight sm:text-5xl">
            Oyy, Alex!
            <br />
            Apa rencana analisismu hari ini?
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-muted sm:text-base">Satu workspace untuk discovery sumber, scraping data, insight AI, dan rekomendasi strategi. Semua topik bisa dianalisis secara dinamis sesuai input kamu.</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link href="/analisis/baru" className="ms-btn-primary">
              Mulai Analisis
            </Link>
            <Link href="/analisis" className="ms-btn-ghost">
              Lihat Semua Analisis
            </Link>
          </div>
        </article>

        <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
          <article className="surface-card p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Discovery</p>
            <h3 className="mt-2 section-title text-lg">Stay organized</h3>
            <p className="mt-1 text-sm text-muted">Temukan sumber relevan lintas domain publik dengan scoring adaptif.</p>
          </article>
          <article className="surface-card p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Scraping</p>
            <h3 className="mt-2 section-title text-lg">Sync your notes</h3>
            <p className="mt-1 text-sm text-muted">Scrapy + fallback parser menjaga pipeline tetap jalan saat sumber dinamis.</p>
          </article>
          <article className="surface-card p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">AI Insight</p>
            <h3 className="mt-2 section-title text-lg">Collaborate and share</h3>
            <p className="mt-1 text-sm text-muted">Gemini merangkum peluang, kompetitor, pricing, dan rekomendasi aksi.</p>
          </article>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <article className="surface-card p-5 xl:col-span-1">
          <div className="flex items-center justify-between">
            <h2 className="section-title text-lg">Notifications</h2>
            <span className="text-xs text-muted">Clear</span>
          </div>
          <div className="surface-soft mt-4 p-4">
            <p className="text-sm font-semibold text-slate-800">Upcoming Event</p>
            <p className="mt-1 text-xs text-muted">Analisis batch dijadwalkan berjalan tiap 30 menit.</p>
          </div>
          <div className="surface-soft mt-3 p-4">
            <p className="text-sm font-semibold text-slate-800">Message Product Design</p>
            <p className="mt-1 text-xs text-muted">UI sudah diperbarui dengan layout modern dan responsif.</p>
          </div>
        </article>

        <article className="surface-card p-5 xl:col-span-1">
          <div className="flex items-center justify-between">
            <h2 className="section-title text-lg">Assignments</h2>
            <span className="text-xs text-muted">Edit</span>
          </div>
          <div className="space-y-3 pt-4">
            <div className="surface-soft p-4">
              <p className="text-xs text-muted">Motion design - Logo</p>
              <p className="mt-1 text-sm font-semibold text-slate-800">Design query planner dashboard</p>
              <div className="mt-3 flex items-center gap-2">
                <span className="chip">Pending</span>
                <span className="text-xs text-muted">Due 14:00</span>
              </div>
            </div>
            <Link href="/analisis/baru" className="block rounded-xl border border-dashed border-violet-300 bg-violet-50 px-4 py-3 text-center text-sm font-semibold text-violet-700">
              Add new assignment
            </Link>
          </div>
        </article>

        <article className="surface-card p-5 xl:col-span-1">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="section-title text-lg">{monthLabel}</h2>
              <p className="mt-1 text-xs text-muted">{fullDateLabel}</p>
            </div>
            <p className="chip">{clockLabel}</p>
          </div>
          <div className="mt-4 grid grid-cols-7 gap-1 text-center text-xs">
            {["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"].map((day) => (
              <div key={day} className="py-1 text-muted">
                {day}
              </div>
            ))}
            {calendarDays.map((day, index) => {
              const isToday = day === now.getDate();
              if (day === null) {
                return <div key={`blank-${index}`} className="rounded-lg py-2" />;
              }
              return (
                <div key={`date-${day}`} className={`rounded-lg py-2 ${isToday ? "primary-gradient font-semibold" : "surface-soft"}`}>
                  {day}
                </div>
              );
            })}
          </div>
          <div className="mt-4 space-y-2 text-sm">
            <div className="surface-soft p-3">
              <p className="font-semibold text-slate-800">{timeSlotA}</p>
              <p className="text-muted">Sinkronisasi status analisis</p>
            </div>
            <div className="surface-soft p-3">
              <p className="font-semibold text-slate-800">{timeSlotB}</p>
              <p className="text-muted">Review insight terbaru</p>
            </div>
          </div>
        </article>
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.6fr_1fr]">
        <article className="surface-card p-5">
          <div className="flex items-center justify-between">
            <h2 className="section-title text-lg">Today Tasks</h2>
            <div className="flex items-center gap-2 text-xs text-muted">
              <span>2 Edit</span>
              <span>1 Share</span>
            </div>
          </div>
          <div className="mt-4 space-y-3">
            {["Conduct research", "Schedule a meeting", "Send out reminders"].map((task) => (
              <div key={task} className="surface-soft flex flex-wrap items-center justify-between gap-3 p-3">
                <p className="text-sm font-semibold text-slate-800">{task}</p>
                <div className="h-2 w-32 overflow-hidden rounded-full bg-slate-200">
                  <div className="h-full w-[50%] rounded-full bg-violet-500" />
                </div>
              </div>
            ))}
          </div>
        </article>

        <div className="grid gap-4">
          <article className="surface-card primary-gradient p-5">
            <h3 className="section-title text-xl text-white">Go premium!</h3>
            <p className="mt-3 text-sm text-white/85">Naikkan limit, otomatisasi scheduler, dan pantau performa scraping lebih detail.</p>
            <Link href="/analisis/baru" className="mt-4 inline-flex rounded-full border border-white/30 bg-white/15 px-4 py-2 text-xs font-semibold text-white">
              Find out more
            </Link>
          </article>
          <article className="surface-card p-5">
            <div className="flex items-center justify-between">
              <h3 className="section-title text-lg">Board Meeting</h3>
              <span className="text-xs text-muted">Edit</span>
            </div>
            <p className="mt-2 text-sm text-muted">Review flow insight, validasi sumber, dan finalisasi rekomendasi.</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button className="ms-btn-ghost" type="button">
                Reschedule
              </button>
              <button className="ms-btn-primary" type="button">
                Accept Invite
              </button>
            </div>
          </article>
        </div>
      </section>
    </main>
  );
}
