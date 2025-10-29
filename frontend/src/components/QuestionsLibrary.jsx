import { useEffect, useState } from 'react';
import { getCurrentUser, getQuestionsLibrary } from '../services/api';
import Layout from './Layout';

const DIFFS = [
  { value: 'łatwy', label: '🟢 Łatwy' },
  { value: 'średni', label: '🟡 Średni' },
  { value: 'trudny', label: '🔴 Trudny' },
];

export default function QuestionsLibrary() {
  const [user, setUser] = useState(null);
  const [search, setSearch] = useState('');
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState([]);
  const [orderBy, setOrderBy] = useState('-created_at');
  const [items, setItems] = useState([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const pageSize = 20;
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

  useEffect(() => {
    fetchData({ page });
  }, [page, orderBy, search, topic, difficulty]);

  const fetchData = async (extra = {}) => {
    try {
      setLoading(true);
      setError('');
      const params = { page, page_size: pageSize, order_by: orderBy };
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
    <Layout user={user}>
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* 🔍 Filtry */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-6 border border-gray-100">
          <h2 className="text-xl font-bold text-gray-800 mb-4">🔍 Filtry i sortowanie</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Szukaj */}
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Szukaj w treści pytania
              </label>
              <input
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                placeholder="np. pochodna, trójkąt..."
                className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 transition"
              />
            </div>

            {/* Temat */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Temat</label>
              <input
                type="text"
                value={topic}
                onChange={(e) => {
                  setTopic(e.target.value);
                  setPage(1);
                }}
                placeholder="np. Matematyka"
                className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 transition"
              />
            </div>

            {/* Sortowanie */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Sortuj według</label>
              <select
                value={orderBy}
                onChange={(e) => {
                  setOrderBy(e.target.value);
                  setPage(1);
                }}
                className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 transition"
              >
                <option value="-created_at">Najnowsze</option>
                <option value="created_at">Najstarsze</option>
                <option value="-success_rate">Skuteczność ↓</option>
                <option value="success_rate">Skuteczność ↑</option>
              </select>
            </div>

            {/* Trudności */}
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
                      className={`px-3 py-1 rounded-full border-2 text-sm font-semibold transition-all ${
                        active
                          ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-indigo-600 shadow'
                          : 'bg-gray-100 text-gray-800 border-gray-300 hover:bg-gray-200'
                      }`}
                    >
                      {opt.label}
                    </button>
                  );
                })}

                {/* przycisk wyczyść */}
                <button
                  type="button"
                  onClick={clearFilters}
                  className="ml-auto px-4 py-2 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition font-semibold flex items-center gap-2"
                >
                  🗑️ Wyczyść filtry
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* 📊 Licznik */}
        <div className="mb-4 text-gray-700 font-medium">
          Znaleziono: <span className="text-indigo-600 font-bold">{count}</span> pytań
        </div>

        {/* 📋 Lista pytań */}
        <div className="space-y-4">
          {loading && (
            <div className="bg-white rounded-2xl shadow-md p-12 text-center text-gray-600">
              Ładowanie…
            </div>
          )}
          {error && !loading && (
            <div className="bg-white rounded-2xl shadow-md p-12 text-center text-red-600 font-semibold">
              {error}
            </div>
          )}
          {!loading && !error && items.length === 0 && (
            <div className="bg-white rounded-2xl shadow-md p-12 text-center text-gray-500">
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
              <div key={q.id} className="bg-white rounded-2xl shadow-lg p-6 border border-gray-100">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-gray-800 mb-2">{q.question_text}</h3>

                    <div className="text-sm text-gray-500 mb-2 flex gap-4 flex-wrap">
                      <span>📚 Temat: <b>{q.topic || '—'}</b></span>
                      <span>📅 Data: <b>{fmtDate(q.created_at)}</b></span>
                    </div>

                    <div className="mb-3">
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

                    {/* ✅ Odpowiedzi */}
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

                    {q.explanation && (
                      <div className="mt-3 bg-blue-50 border-l-4 border-blue-500 p-3 rounded">
                        <p className="text-sm text-blue-900">
                          <span className="font-semibold">💡 Wyjaśnienie:</span> {q.explanation}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* 📈 Statystyki */}
                  <div className="text-right ml-4 text-sm text-gray-600 min-w-[180px]">
                    {q.stats && (
                      <>
                        {'accuracy' in q.stats && (
                          <div className="mb-1">
                            🎯 Skuteczność: <b>{q.stats.accuracy ?? 0}%</b>
                          </div>
                        )}
                        {'total_answers' in q.stats && (
                          <div className="mb-1">
                            📊 Odpowiedzi: <b>{q.stats.total_answers ?? 0}</b>
                          </div>
                        )}
                        {'correct_answers' in q.stats && (
                          <div className="mb-1">
                            ✅ Poprawne: <b>{q.stats.correct_answers ?? 0}</b>
                          </div>
                        )}
                        {'wrong_answers' in q.stats && (
                          <div>
                            ❌ Błędne: <b>{q.stats.wrong_answers ?? 0}</b>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* 🔄 Paginacja */}
        {count > pageSize && (
          <div className="mt-6 flex justify-center items-center gap-4">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={!hasPrev || loading}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50"
            >
              ← Poprzednia
            </button>

            <span className="text-gray-700 font-semibold">
              Strona {page} z {totalPages}
            </span>

            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={!hasNext || loading}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-semibold hover:from-indigo-700 hover:to-purple-700 transition-all disabled:opacity-50"
            >
              Następna →
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}
