export default function EmptyState({
  title = 'Brak danych',
  description = '',
  icon = '📭',
  className = '',
}) {
  return (
    <div className={`bg-white dark:bg-slate-900 rounded-2xl shadow-md p-12 text-center text-gray-500 dark:text-slate-300 ${className}`}>
      <div className="text-4xl mb-3">{icon}</div>
      <p className="text-lg font-semibold text-gray-700 dark:text-slate-200">{title}</p>
      {description && <p className="mt-1">{description}</p>}
    </div>
  );
}
