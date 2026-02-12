import { useCallback, useEffect, useState } from 'react';
import { getQuestionsLibrary } from '../../services/api';
import {
  getDifficultyBadgeClass,
  getDifficultyBadgeLabel,
  getKnowledgeBadgeClass,
  getKnowledgeBadgeLabel
} from '../../services/helpers';
import { KNOWLEDGE_LEVELS, QUESTION_DIFFICULTY_LEVELS } from '../../services/constants';
import MainLayout from '../../layouts/MainLayout';
import FiltersPanel from '../../components/FiltersPanel';
import LatexRenderer from '../../components/LatexRenderer';
import PaginationBar from '../../components/PaginationBar';
import useCurrentUser from '../../hooks/useCurrentUser';
import LoadingState from '../../components/LoadingState';
import EmptyState from '../../components/EmptyState';

export default function QuestionsLibrary() {
  const { user } = useCurrentUser();

  const [search, setSearch] = useState('');
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState([]);
  const [filterKnowledge, setFilterKnowledge] = useState('');
  const [orderBy, setOrderBy] = useState('-created_at');

  const [items, setItems] = useState([]);
  const [count, setCount] = useState(0);

  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(false);

  const fetchData = useCallback(async (extra = {}) => {
    try {
      setLoading(true);
      setError('');

      const params = {
        page,
        page_size: pageSize,
        order_by: orderBy,
        ...extra,
      };

      if (search.trim()) params.search = search.trim();
      if (topic.trim()) params.topic = topic.trim();
      if (difficulty.length) params.difficulty = difficulty.join(',');
      if (filterKnowledge) params.knowledge_level = filterKnowledge;

      const data = await getQuestionsLibrary(params);

      setItems(Array.isArray(data?.results) ? data.results : []);
      setCount(Number(data?.count || 0));
    } catch (e) {
      console.error('Questions load error:', e);
      setError('Nie udało się pobrać pytań.');
    } finally {
      setLoading(false);
    }
  }, [difficulty, filterKnowledge, orderBy, page, pageSize, search, topic]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  const hasPrev = page > 1;
  const hasNext = page < totalPages;

  const toggleDiff = (val) => {
    setPage(1);
    setDifficulty((prev) => (prev.includes(val) ? prev.filter((d) => d !== val) : [...prev, val]));
  };

  const clearFilters = () => {
    setSearch('');
    setTopic('');
    setDifficulty([]);
    setFilterKnowledge('');
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
    <MainLayout user={user}>
      <div className="max-w-7xl mx-auto px-6 py-8">
        <FiltersPanel
          title="Filtry i sortowanie"
          icon=""
          isOpen={filtersOpen}
          onToggle={() => setFiltersOpen((prev) => !prev)}
          className="mb-8"
        >
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
                className="ui-input"
              />
            </div>

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
                className="ui-input"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Sortuj według
              </label>
              <select
                value={orderBy}
                onChange={(e) => {
                  setOrderBy(e.target.value);
                  setPage(1);
                }}
                className="ui-select"
              >
                <option value="-created_at">Najnowsze</option>
                <option value="created_at">Najstarsze</option>
                <option value="-success_rate">Skuteczność ↓</option>
                <option value="success_rate">Skuteczność ↑</option>
              </select>
            </div>

            <div className="md:col-span-4 mt-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Poziom trudności
              </label>
              <div className="flex flex-wrap gap-2">
                {QUESTION_DIFFICULTY_LEVELS.map((opt) => {
                  const active = difficulty.includes(opt.key);
                  const base = getDifficultyBadgeClass(opt.key);
                  return (
                    <button
                      key={opt.key}
                      type="button"
                      onClick={() => toggleDiff(opt.key)}
                      className={`px-3 py-2 rounded-full border-2 text-sm font-semibold transition-all ${
                        active
                          ? `${base} border-transparent shadow`
                          : `${base} border-transparent opacity-80 hover:opacity-100`
                      }`}
                    >
                      {opt.emoji} {opt.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="md:col-span-4 mt-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Poziom wiedzy
              </label>
              <div className="flex flex-wrap gap-2 items-center">
                {KNOWLEDGE_LEVELS.map((opt) => {
                  const active = filterKnowledge === opt.key;
                  return (
                    <button
                      key={opt.key}
                      type="button"
                      onClick={() => {
                        setFilterKnowledge(active ? '' : opt.key);
                        setPage(1);
                      }}
                      className={`px-3 py-2 rounded-full border-2 text-sm font-semibold transition-all ${
                        active
                          ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-indigo-600 shadow'
                          : 'bg-gray-100 text-gray-800 border-gray-300 hover:bg-gray-200 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-700'
                      }`}
                    >
                      {opt.emoji} {opt.label}
                    </button>
                  );
                })}

                <button
                  type="button"
                  onClick={clearFilters}
                  className="ml-auto px-4 py-2 bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-700 transition font-semibold flex items-center gap-2"
                >
                  🗑️ Wyczyść filtry
                </button>
              </div>
            </div>
          </div>
        </FiltersPanel>

        <div className="bg-white dark:bg-slate-900 rounded-2xl border border-gray-200 dark:border-slate-800 shadow-md p-4 sm:p-6">
          <div className="mb-4 text-gray-700 dark:text-slate-200 font-medium">
            Znaleziono: <span className="text-indigo-600 font-bold">{count}</span> pytań
          </div>

          <div className="space-y-4">
            {loading && (
              <LoadingState message="Ładowanie..." />
            )}

            {error && !loading && (
              <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-md p-12 text-center text-red-600 dark:text-red-300 font-semibold">
                {error}
              </div>
            )}

            {!loading && !error && items.length === 0 && (
              <EmptyState
                icon="📚"
                title="Brak wyników"
                description="Zmień filtry."
              />
            )}

            {!loading &&
              !error &&
              items.map((q) => {
                const answers = [
                  { key: 'A', text: q?.correct_answer ?? '—', correct: true },
                  { key: 'B', text: q?.wrong_answer_1 ?? '—', correct: false },
                  { key: 'C', text: q?.wrong_answer_2 ?? '—', correct: false },
                  { key: 'D', text: q?.wrong_answer_3 ?? '—', correct: false },
                ];

                const acc = q?.stats?.accuracy;
                const total = q?.stats?.total_answers;
                const correct = q?.stats?.correct_answers;
                const wrong = q?.stats?.wrong_answers;
                const used = q?.stats?.times_used;

                return (
                  <div
                    key={q.id}
                    className="group p-6 border-2 border-gray-100 dark:border-slate-800 rounded-xl hover:border-indigo-300 hover:shadow-lg transition-all bg-gradient-to-r from-white to-gray-50 dark:from-slate-900 dark:to-slate-800"
                  >
                    <div className="flex flex-col lg:flex-row lg:justify-between items-start gap-6">
                      <div className="flex-1">
                        <div className="mb-3">
                          <LatexRenderer
                            text={q.question_text}
                            className="text-lg font-bold text-gray-800 dark:text-slate-100 group-hover:text-indigo-600 transition-colors inline"
                            inline={true}
                          />
                        </div>

                        <div className="flex flex-wrap gap-3 mb-4">
                          <span
                            className={`px-3 py-1 rounded-full text-sm font-semibold ${getDifficultyBadgeClass(
                              q.difficulty_level
                            )}`}
                          >
                            {getDifficultyBadgeLabel(q.difficulty_level)}
                          </span>

                          {q.knowledge_level && (
                            <span
                              className={`px-3 py-1 rounded-full text-sm font-semibold ${getKnowledgeBadgeClass(
                                q.knowledge_level
                              )}`}
                            >
                              {getKnowledgeBadgeLabel(q.knowledge_level)}
                            </span>
                          )}

                          <span className="px-3 py-1 bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-200 rounded-full text-sm font-semibold">
                            {q.topic || '-'}
                          </span>

                          <span className="px-3 py-1 bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 rounded-full text-sm font-medium">
                            {fmtDate(q.created_at)}
                          </span>
                        </div>

                        <div className="space-y-2 mb-4">
                          {answers.map((a) => (
                            <div
                              key={`${q.id}-${a.key}`}
                              className={`p-3 rounded-xl border-2 transition-all ${
                                a.correct
                                  ? 'bg-green-50 border-green-400 dark:bg-green-900/30 dark:border-green-700'
                                  : 'bg-gray-50 border-gray-200 dark:bg-slate-900 dark:border-slate-700'
                              }`}
                            >
                              <span className="font-bold text-indigo-600 dark:text-indigo-300 mr-2">
                                {a.key}.
                              </span>
                              <LatexRenderer
                                text={a.text}
                                className="text-gray-800 dark:text-slate-100 break-words"
                                inline={true}
                              />
                              {a.correct && (
                                <span className="ml-3 px-2 py-0.5 rounded-lg text-xs bg-green-600 text-white font-semibold">
                                  ✅ Poprawna
                                </span>
                              )}
                            </div>
                          ))}
                        </div>

                        {q.explanation && (
                          <div className="bg-blue-50 dark:bg-slate-900 border-l-4 border-blue-500 dark:border-blue-500 p-4 rounded-r-xl">
                            <p className="text-sm text-blue-900 dark:text-blue-200">
                              <span className="font-semibold"> Wyjaśnienie:</span>{' '}
                              <LatexRenderer text={q.explanation} inline={true} />
                            </p>
                          </div>
                        )}
                      </div>

                      <div className="w-full lg:w-auto lg:min-w-[160px] text-left lg:text-right">
                        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 dark:bg-slate-900 dark:bg-none rounded-xl p-4 border border-indigo-100 dark:border-slate-800">
                          <p className="text-xs text-gray-600 mb-2">Statystyki</p>

                          <div className="mb-2">
                            <p className="text-sm text-gray-500">Skuteczność</p>
                            <p className="text-2xl font-bold text-indigo-600 dark:text-indigo-300">
                              {acc !== undefined && acc !== null ? Math.round(acc) : 0}%
                            </p>
                          </div>

                          <div className="text-sm text-gray-700 dark:text-slate-200 space-y-1">
                            <div>
                              Odpowiedzi: <b>{total ?? 0}</b>
                            </div>
                            <div>
                              Poprawne: <b>{correct ?? 0}</b>
                            </div>
                            <div>
                              Błędne: <b>{wrong ?? 0}</b>
                            </div>
                            <div>
                              Użycia: <b>{used ?? 0}</b>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
          </div>

          {count > 0 && (
            <PaginationBar
              page={page}
              totalPages={totalPages}
              hasPrev={hasPrev}
              hasNext={hasNext}
              loading={loading}
              onPrev={() => setPage((p) => Math.max(1, p - 1))}
              onNext={() => setPage((p) => Math.min(totalPages, p + 1))}
              pageSize={pageSize}
              onPageSizeChange={(size) => {
                setPageSize(size);
                setPage(1);
              }}
            />
          )}
        </div>
      </div>
    </MainLayout>
  );
}

