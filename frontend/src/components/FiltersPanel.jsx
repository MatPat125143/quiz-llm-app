export default function FiltersPanel({
  title = 'Filtry i sortowanie',
  icon = '🔎',
  isOpen = true,
  onToggle,
  className = '',
  children,
}) {
  const toggleLabel = isOpen ? 'Ukryj' : 'Pokaż';

  return (
    <div
      className={`bg-white dark:bg-slate-900 rounded-2xl p-6 shadow-lg border border-gray-100 dark:border-slate-800 ${className}`}
    >
      <div className="flex items-center justify-between gap-3 min-h-[48px]">
        <h2 className="text-xl font-bold text-gray-800 dark:text-slate-100 flex items-center gap-2 leading-none">
          {icon && <span className="text-2xl">{icon}</span>}
          {title}
        </h2>
        {onToggle && (
          <button
            type="button"
            onClick={onToggle}
            className="md:hidden px-4 py-2 bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-700 transition font-semibold text-sm"
          >
            {toggleLabel}
          </button>
        )}
      </div>

      <div className={`${onToggle ? (isOpen ? 'block' : 'hidden') : 'block'} md:block mt-4`}>
        {children}
      </div>
    </div>
  );
}

