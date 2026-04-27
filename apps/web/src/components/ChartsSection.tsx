"use client";

import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { ScrapedItem, Source } from "@/lib/types";

interface ChartsSectionProps {
  sources: Source[];
  items: ScrapedItem[];
}

const pieColors = ["#1572f5", "#35b0ff", "#00a86b", "#f59e0b", "#ef4444"];

export function ChartsSection({ sources, items }: ChartsSectionProps) {
  const sourceStatusData = [
    { name: "Selesai", value: sources.filter((source) => source.status === "completed").length },
    { name: "Gagal", value: sources.filter((source) => source.status === "failed").length },
    { name: "Lainnya", value: sources.filter((source) => !["completed", "failed"].includes(source.status)).length }
  ].filter((item) => item.value > 0);

  const ratings = items.filter((item) => item.rating !== null && item.rating !== undefined).map((item) => Number(item.rating));
  const ratingBins = [
    { name: "< 3.0", value: ratings.filter((rating) => rating < 3).length },
    { name: "3.0 - 3.9", value: ratings.filter((rating) => rating >= 3 && rating < 4).length },
    { name: "4.0 - 4.4", value: ratings.filter((rating) => rating >= 4 && rating < 4.5).length },
    { name: ">= 4.5", value: ratings.filter((rating) => rating >= 4.5).length }
  ];

  const priceBins = [
    { name: "< 25rb", value: items.filter((item) => (item.price_min ?? 0) > 0 && (item.price_min ?? 0) < 25000).length },
    { name: "25-50rb", value: items.filter((item) => (item.price_min ?? 0) >= 25000 && (item.price_min ?? 0) < 50000).length },
    { name: "50-100rb", value: items.filter((item) => (item.price_min ?? 0) >= 50000 && (item.price_min ?? 0) < 100000).length },
    { name: ">= 100rb", value: items.filter((item) => (item.price_min ?? 0) >= 100000).length }
  ];

  return (
    <section className="grid gap-4 lg:grid-cols-3">
      <article className="surface-card p-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-900">Jumlah Sumber</h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={sourceStatusData} dataKey="value" nameKey="name" innerRadius={45} outerRadius={75} label>
                {sourceStatusData.map((entry, index) => (
                  <Cell key={entry.name} fill={pieColors[index % pieColors.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </article>

      <article className="surface-card p-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-900">Distribusi Rating</h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={ratingBins}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e7e7f1" />
              <XAxis dataKey="name" fontSize={12} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#6759f4" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </article>

      <article className="surface-card p-4">
        <h3 className="mb-3 text-sm font-semibold text-slate-900">Distribusi Harga</h3>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={priceBins}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e7e7f1" />
              <XAxis dataKey="name" fontSize={12} />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#4fc89f" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </article>
    </section>
  );
}
