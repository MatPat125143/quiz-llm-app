export default function LoadingState({
  message = 'Ładowanie...',
  fullScreen = false,
  className = '',
}) {
  if (fullScreen) {
    return (
      <div className={`min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 ${className}`}>
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-lg text-gray-600 dark:text-slate-200 font-medium">{message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-slate-900 rounded-2xl shadow-md p-12 text-center text-gray-600 dark:text-slate-200 ${className}`}>
      <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
      <p className="font-medium">{message}</p>
    </div>
  );
}
