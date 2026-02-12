import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-950 px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-indigo-600">404</h1>
          <div className="text-6xl mb-4">🔍</div>
          <h2 className="text-3xl font-semibold text-gray-900 dark:text-slate-100 mb-4">
            Nie znaleziono strony
          </h2>
          <p className="text-gray-600 dark:text-slate-300 mb-8">
            Strona, której szukasz, nie istnieje lub została przeniesiona.
          </p>
        </div>

        <div className="space-y-4">
          <Link
            to="/dashboard"
            className="block w-full bg-indigo-600 dark:bg-indigo-700 text-white py-3 px-4 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors"
          >
            Wróć do strony głównej
          </Link>
        </div>
      </div>
    </div>
  );
}
