export default function PaginationBar({
  page,
  totalPages,
  hasPrev,
  hasNext,
  loading,
  onPrev,
  onNext,
  pageSize,
  onPageSizeChange,
}) {
  return (
    <div className="mt-6 flex flex-col gap-3 sm:grid sm:grid-cols-[1fr_auto_1fr] sm:items-center">
      <div className="hidden sm:block" />
      <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-3">
        <button
          type="button"
          onClick={onPrev}
          disabled={!hasPrev || loading}
          className="px-3 sm:px-4 py-2 rounded-xl bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 hover:bg-gray-200 dark:hover:bg-slate-700 transition font-semibold text-xs sm:text-sm disabled:opacity-50"
        >
          ← Poprzednia
        </button>
        <span className="order-last basis-full text-center sm:order-none sm:basis-auto text-sm text-gray-700 dark:text-slate-200 font-medium">
          Strona {page} z {totalPages}
        </span>
        <button
          type="button"
          onClick={onNext}
          disabled={!hasNext || loading}
          className="px-3 sm:px-4 py-2 rounded-xl bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 hover:bg-gray-200 dark:hover:bg-slate-700 transition font-semibold text-xs sm:text-sm disabled:opacity-50"
        >
          Następna →
        </button>
      </div>

      <div className="flex items-center justify-end gap-2 text-sm text-gray-700 dark:text-slate-200">
        <span>Na stronę</span>
        <select
          className="ui-select w-20 min-w-[72px] max-w-[96px] shrink-0"
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
        >
          {[10, 20, 30, 50].map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

