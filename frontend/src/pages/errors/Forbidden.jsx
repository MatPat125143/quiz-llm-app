import { Link, useNavigate } from 'react-router-dom';

export default function Forbidden() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-slate-950 px-4">
      <div className="max-w-md w-full text-center">
        <div className="mb-8">
          <h1 className="text-9xl font-bold text-red-600">403</h1>
          <div className="text-6xl mb-4">🚫</div>
          <h2 className="text-3xl font-semibold text-gray-900 dark:text-slate-100 mb-4">
            Brak dostępu
          </h2>
          <p className="text-gray-600 dark:text-slate-300 mb-8">
            Nie masz uprawnień do tej strony.
          </p>
        </div>

        <div className="space-y-4">
          <button
            onClick={() => navigate(-1)}
            className="block w-full bg-indigo-600 dark:bg-indigo-700 text-white py-3 px-4 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 transition-colors"
          >
            Wróć
          </button>
          <Link
            to="/dashboard"
            className="block w-full bg-gray-200 dark:bg-slate-800 text-gray-700 dark:text-slate-100 py-3 px-4 rounded-lg hover:bg-gray-300 dark:hover:bg-slate-700 transition-colors"
          >
            Wróć do strony głównej
          </Link>
        </div>
      </div>
    </div>
  );
}
