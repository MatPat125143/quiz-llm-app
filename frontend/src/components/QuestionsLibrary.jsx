import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser, logout, getQuestionsLibrary } from '../services/api';

const DIFFS = [
  { value: 'łatwy',  label: '🟢 Łatwy' },
  { value: 'średni', label: '🟡 Średni' },
  { value: 'trudny', label: '🔴 Trudny' },
];

export default function QuestionsLibrary() {
  const navigate = useNavigate();

  // user (header)
  const [user, setUser] = useState(null);

  // filtry
  const [search, setSearch] = useState('');
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState([]); // ['łatwy','średni',...]
  const [orderBy, setOrderBy] = useState('-created_at'); // tylko data i skuteczność (wg prośby)

  // dane
  const [items, setItems] = useState([]);
  const [count, setCount] = useState(0);

  // paginacja
  const [page, setPage] = useState(1);
  const pageSize = 20;

  // stan
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const me = await getCurrentUser();
        setUser(me);
      } catch (e) {
        console.error('Error loading user:', e);
      }
    })();
  }, []);

  // Natychmiastowe odświeżanie przy KAŻDEJ zmianie filtra/sortu/strony
  useEffect(() => {
    fetchData({ page });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, orderBy, search, topic, difficulty]);

  const fetchData = async (extra = {}) => {
    try {
      setLoading(true);
      setError('');

      const params = {
        page,
        page_size: pageSize,
        order_by: orderBy,
      };

      if (search.trim()) params.search = search.trim();
      if (topic.trim()) params.topic = topic.trim();
      if (difficulty.length) params.difficulty = difficulty.join(',');

      Object.assign(params, extra);

      const data = await getQuestionsLibrary(params);
      setItems(Array.isArray(data.results) ? data.results : []);
      setCount(Number(data.count || 0));
    } catch (e) {
      console.error('Questions load error:', e);
      setError('Nie udało się pobrać pytań.');
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  const hasPrev = page > 1;
  const hasNext = page < totalPages;

  const toggleDiff = (val) => {
    setPage(1);
    setDifficulty((prev) =>
      prev.includes(val) ? prev.filter((d) => d !== val) : [...prev, val]
    );
  };

  const clearFilters = () => {
    setSearch('');
    setTopic('');
    setDifficulty([]);
    setOrderBy('-created_at');
    setPage(1);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // pomocnicze – format daty
  const fmtDate = (iso) => {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      return d.toLocaleDateString('pl-PL', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return '—';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header (spójny z historią) */}
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-blue-600">📚 Biblioteka Pytań</h1>
          <div className="flex items-center gap-4">
            <div
              className="flex items-center gap-3 cursor-pointer hover:bg-gray-100 p-2 rounded-lg transition"
              onClick={() => navigate('/profile')}
            >
              {user?.profile?.avatar_url ? (
                <img
                  src={user.profile.avatar_url}
                  alt="Avatar"
                  className="w-10 h-10 rounded-full object-cover border-2 border-blue-500"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center border-2 border-blue-500">
                  <span className="text-white font-bold text-lg">
                    {user?.email?.[0]?.toUpperCase() || '?'}
                  </span>
                </div>
              )}
              <span className="font-semibold text-gray-800">{user?.username}</span>
            </div>

            <button
              onClick={() => navigate('/dashboard')}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition font-semibold"
            >
              ← Panel główny
            </button>

            {user?.profile?.role === 'admin' && (
              <button
                onClick={() => navigate('/admin')}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition font-semibold"
              >
                👑 Panel admina
              </button>
            )}

            <button
              onClick={handleLogout}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition font-semibold"
            >
              Wyloguj
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Filtry – bez przycisku „Szukaj”, wszystko działa onChange */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Filtry</h2>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Szukaj */}
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Szukaj w treści / odpowiedziach / wyjaśnieniach
              </label>
              <input
                type="text"
                value={search}
                onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                placeholder="np. pochodna, trójkąt…"
                className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Temat */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Temat
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => { setTopic(e.target.value); setPage(1); }}
                placeholder="np. Matematyka"
                className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              />
            </div>

            {/* Sort – zostawiamy tylko po dacie i skuteczności */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Sortuj według
              </label>
              <select
                value={orderBy}
                onChange={(e) => { setOrderBy(e.target.value); setPage(1); }}
                className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              >
                <option value="-created_at">Najnowsze</option>
                <option value="created_at">Najstarsze</option>
                <option value="-success_rate">Skuteczność: ↓</option>
                <option value="success_rate">Skuteczność: ↑</option>
              </select>
            </div>

            {/* Trudności (chipsy) */}
            <div className="md:col-span-4">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Poziom trudności
              </label>
              <div className="flex flex-wrap gap-2">
                {DIFFS.map((opt) => {
                  const active = difficulty.includes(opt.value);
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => toggleDiff(opt.value)}
                      className={`px-3 py-1 rounded-full border-2 text-sm font-semibold ${
                        active
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-gray-100 text-gray-800 border-gray-300'
                      }`}
                    >
                      {opt.label}
                    </button>
                  );
                })}

                <button
                  type="button"
                  onClick={clearFilters}
                  className="ml-auto px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition font-semibold"
                >
                  🗑️ Wyczyść
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Licznik wyników */}
        <div className="mb-4 text-gray-600">
          Znaleziono: <strong>{count}</strong> pytań
        </div>

        {/* Lista pytań – karta z odpowiedziami i oznaczeniem poprawnej */}
        <div className="space-y-4">
          {loading && (
            <div className="bg-white rounded-xl shadow-lg p-12 text-center">
              Ładowanie…
            </div>
          )}
          {error && !loading && (
            <div className="bg-white rounded-xl shadow-lg p-12 text-center text-red-600">
              {error}
            </div>
          )}
          {!loading && !error && items.length === 0 && (
            <div className="bg-white rounded-xl shadow-lg p-12 text-center text-gray-500">
              Brak wyników. Zmień filtry.
            </div>
          )}

          {!loading && !error && items.map((q) => {
            const answers = [
              { key: 'A', text: q.correct_answer, correct: true },
              { key: 'B', text: q.wrong_answer_1, correct: false },
              { key: 'C', text: q.wrong_answer_2, correct: false },
              { key: 'D', text: q.wrong_answer_3, correct: false },
            ];

            return (
              <div key={q.id} className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-gray-800 mb-1">
                      {q.question_text}
                    </h3>

                    <div className="text-sm text-gray-500 mb-2 flex gap-4 flex-wrap">
                      <span>
                        Temat: <span className="font-medium">{q.topic || '—'}</span>
                      </span>
                      <span>
                        Data: <span className="font-medium">{fmtDate(q.created_at)}</span>
                      </span>
                    </div>

                    {/* difficulty badge */}
                    <div className="flex flex-wrap gap-2 mb-3">
                      <span
                        className={`px-3 py-1 rounded-full text-sm font-semibold ${
                          q.difficulty_level === 'łatwy'
                            ? 'bg-green-100 text-green-800'
                            : q.difficulty_level === 'średni'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {q.difficulty_level === 'łatwy' && '🟢 Łatwy'}
                        {q.difficulty_level === 'średni' && '🟡 Średni'}
                        {q.difficulty_level === 'trudny' && '🔴 Trudny'}
                      </span>
                    </div>

                    {/* Odpowiedzi z zaznaczeniem poprawnej */}
                    <div className="space-y-2">
                      {answers.map((a) => (
                        <div
                          key={`${q.id}-${a.key}`}
                          className={`p-3 rounded border ${
                            a.correct
                              ? 'bg-green-50 border-green-400'
                              : 'bg-gray-50 border-gray-300'
                          }`}
                        >
                          <span className="font-bold mr-2">{a.key}.</span>
                          <span>{a.text}</span>
                          {a.correct && (
                            <span className="ml-3 px-2 py-0.5 rounded text-xs bg-green-600 text-white">
                              ✅ Poprawna
                            </span>
                          )}
                        </div>
                      ))}
                    </div>

                    {/* Wyjaśnienie */}
                    {q.explanation && (
                      <div className="mt-3 bg-blue-50 border-l-4 border-blue-500 p-3 rounded">
                        <p className="text-sm text-blue-900">
                          <span className="font-semibold">💡 Wyjaśnienie:</span> {q.explanation}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Statystyki */}
                  <div className="text-right ml-4 text-sm text-gray-600 min-w-[180px]">
                    {'stats' in q && q.stats ? (
                      <>
                        {'accuracy' in q.stats && (
                          <div className="mb-1">
                            Skuteczność: <b>{q.stats.accuracy ?? 0}%</b>
                          </div>
                        )}
                        {'total_answers' in q.stats && (
                          <div className="mb-1">
                            Odpowiedzi: <b>{q.stats.total_answers ?? 0}</b>
                          </div>
                        )}
                        {'correct_answers' in q.stats && (
                          <div className="mb-1">
                            Poprawne: <b>{q.stats.correct_answers ?? 0}</b>
                          </div>
                        )}
                        {'wrong_answers' in q.stats && (
                          <div>
                            Błędne: <b>{q.stats.wrong_answers ?? 0}</b>
                          </div>
                        )}
                      </>
                    ) : null}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Pagniacja */}
        {count > pageSize && (
          <div className="mt-6 flex justify-center items-center gap-4">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={!hasPrev || loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ← Poprzednia
            </button>

            <span className="text-gray-700 font-semibold">
              Strona {page} z {totalPages}
            </span>

            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={!hasNext || loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Następna →
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
