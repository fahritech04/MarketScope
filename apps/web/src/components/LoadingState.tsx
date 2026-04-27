export function LoadingState({ message = "Memuat data..." }: { message?: string }) {
  return (
    <div className="glass-panel flex items-center gap-3 rounded-2xl p-4">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
      <p className="text-sm text-slate-600">{message}</p>
    </div>
  );
}

