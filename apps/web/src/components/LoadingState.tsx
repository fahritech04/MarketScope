export function LoadingState({ message = "Memuat data..." }: { message?: string }) {
  return (
    <div className="surface-card flex items-center gap-3 p-4">
      <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-violet-500 border-t-transparent" />
      <p className="text-sm text-muted">{message}</p>
    </div>
  );
}
