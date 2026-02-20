import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getQuizHistory } from '../../services/api';
import {
  calculatePercentage,
  formatQuizDuration,
  getAdaptiveBadgeClass,
  getDifficultyBadgeClass,
  getDifficultyBadgeLabel,
  getKnowledgeBadgeClass,
  getKnowledgeBadgeLabel,
} from '../../services/helpers';
import { DIFFICULTY_LEVELS, KNOWLEDGE_LEVELS } from '../../services/constants';
import MainLayout from '../../layouts/MainLayout';
import FiltersPanel from '../../components/FiltersPanel';
import PaginationBar from '../../components/PaginationBar';
import useCurrentUser from '../../hooks/useCurrentUser';
import LoadingState from '../../components/LoadingState';
import EmptyState from '../../components/EmptyState';

export default function QuizHistory() {
  const { user, loading: userLoading } = useCurrentUser();
  const [quizzes, setQuizzes] = useState([]);
  const [filteredQuizzes, setFilteredQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [filters, setFilters] = useState({
    topic: '',
    difficulty: '',
    knowledgeLevel: '',
    sortBy: 'date_desc',
    isAdaptive: '',
  });

  const navigate = useNavigate();

  const normalizeDifficulty = (value) => {
    const raw = String(value || '')
      .trim()
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

    if (raw === 'latwy') return 'easy';
    if (raw === 'sredni') return 'medium';
    if (raw === 'trudny') return 'hard';
    return raw;
  };

  const loadData = useCallback(async () => {
    try {
      const quizData = await getQuizHistory();
      setQuizzes(Array.isArray(quizData?.results) ? quizData.results : []);
    } catch (err) {
      console.error('Error loading history:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const applyFilters = useCallback(() => {
    let filtered = [...quizzes];

    if (filters.topic.trim()) {
      const needle = filters.topic.toLowerCase();
      filtered = filtered.filter(
        (q) =>
          (q.topic || '').toLowerCase().includes(needle) ||
          (q.subtopic || '').toLowerCase().includes(needle)
      );
    }

    if (filters.difficulty) {
      filtered = filtered.filter(
        (q) => normalizeDifficulty(q.difficulty) === normalizeDifficulty(filters.difficulty)
      );
    }

    if (filters.knowledgeLevel) {
      filtered = filtered.filter((q) => q.knowledge_level === filters.knowledgeLevel);
    }

    if (filters.isAdaptive) {
      const adaptiveValue = filters.isAdaptive === 'true';
      filtered = filtered.filter((q) => Boolean(q.use_adaptive_difficulty) === adaptiveValue);
    }

    switch (filters.sortBy) {
      case 'date_asc':
        filtered.sort((a, b) => new Date(a.started_at) - new Date(b.started_at));
        break;
      case 'score_desc':
        filtered.sort((a, b) => calculatePercentage(b) - calculatePercentage(a));
        break;
      case 'score_asc':
        filtered.sort((a, b) => calculatePercentage(a) - calculatePercentage(b));
        break;
      default:
        filtered.sort((a, b) => new Date(b.started_at) - new Date(a.started_at));
        break;
    }

    setFilteredQuizzes(filtered);
  }, [filters, quizzes]);

  useEffect(() => {
    applyFilters();
  }, [applyFilters]);

  const handleFilterChange = (key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(1);
  };

  const clearFilters = () => {
    setFilters({
      topic: '',
      difficulty: '',
      knowledgeLevel: '',
      sortBy: 'date_desc',
      isAdaptive: '',
    });
    setPage(1);
  };

  const totalPages = Math.max(1, Math.ceil(filteredQuizzes.length / pageSize));
  const hasPrev = page > 1;
  const hasNext = page < totalPages;
  const pagedQuizzes = filteredQuizzes.slice((page - 1) * pageSize, page * pageSize);

  if (loading || userLoading) {
    return (
      <LoadingState message="Ładowanie historii..." fullScreen={true} />
    );
  }

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
                Szukaj w temacie lub podtemacie quizu
              </label>
              <input
                type="text"
                value={filters.topic}
                onChange={(e) => handleFilterChange('topic', e.target.value)}
                placeholder="np. Matematyka, Algebra, Historia..."
                className="ui-input"
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Rodzaj quizu</label>
              <select
                value={filters.isAdaptive}
                onChange={(e) => handleFilterChange('isAdaptive', e.target.value)}
                className="ui-select"
              >
                <option value="">Wszystkie</option>
                <option value="true">Adaptacyjne</option>
                <option value="false">Standardowe</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Sortuj według</label>
              <select
                value={filters.sortBy}
                onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                className="ui-select"
              >
                <option value="date_desc">Najnowsze</option>
                <option value="date_asc">Najstarsze</option>
                <option value="score_desc">Wynik malejąco</option>
                <option value="score_asc">Wynik rosnąco</option>
              </select>
            </div>

            <div className="md:col-span-4 mt-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">Poziom trudności</label>
              <div className="flex flex-wrap gap-2">
                {DIFFICULTY_LEVELS.map((opt) => {
                  const active = filters.difficulty === opt.key;
                  const base = getDifficultyBadgeClass(opt.key);
                  return (
                    <button
                      key={opt.key}
                      type="button"
                      onClick={() => handleFilterChange('difficulty', active ? '' : opt.key)}
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
              <label className="block text-sm font-semibold text-gray-700 mb-2">Poziom wiedzy</label>
              <div className="flex flex-wrap gap-2 items-center">
                {KNOWLEDGE_LEVELS.map((opt) => {
                  const active = filters.knowledgeLevel === opt.key;
                  return (
                    <button
                      key={opt.key}
                      type="button"
                      onClick={() => handleFilterChange('knowledgeLevel', active ? '' : opt.key)}
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

        <div className="bg-white dark:bg-slate-900 rounded-2xl p-8 shadow-lg border border-gray-100 dark:border-slate-800">
          <div className="mb-4 text-gray-700 dark:text-slate-200 font-medium">
            Znaleziono: <span className="text-indigo-600 font-bold">{filteredQuizzes.length}</span> quizów
          </div>

          {filteredQuizzes.length === 0 ? (
            <div className="py-8">
              <EmptyState
                icon="🎯"
                title={quizzes.length === 0 ? 'Nie masz jeszcze żadnych quizów' : 'Brak wyników dla wybranych filtrów'}
              />
              {quizzes.length === 0 && (
                <button
                  onClick={() => navigate('/quiz/setup')}
                  className="mt-6 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:from-indigo-700 hover:to-purple-700 transition-all shadow-md"
                >
                  Rozpocznij pierwszy quiz
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {pagedQuizzes.map((quiz) => (
                <div
                  key={quiz.id}
                  onClick={() => navigate(`/quiz/details/${quiz.id}`)}
                  className="group p-6 border-2 border-gray-100 dark:border-slate-800 rounded-xl hover:border-indigo-300 hover:shadow-lg transition-all cursor-pointer bg-gradient-to-r from-white to-gray-50 dark:from-slate-900 dark:to-slate-800"
                >
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <h3 className="text-xl font-bold text-gray-800 dark:text-slate-100 group-hover:text-indigo-600 transition-colors">
                          {quiz.topic}
                          {quiz.subtopic && (
                            <span className="text-base font-normal text-gray-600 dark:text-slate-300 ml-2">
                              {quiz.subtopic}
                            </span>
                          )}
                        </h3>
                      </div>

                      <div className="flex flex-wrap gap-2 mb-3">
                        <span
                          className={`px-3 py-1 rounded-full text-sm font-semibold ${getDifficultyBadgeClass(
                            quiz.difficulty
                          )}`}
                        >
                          {getDifficultyBadgeLabel(quiz.difficulty)}
                        </span>

                        {quiz.knowledge_level && (
                          <span
                            className={`px-3 py-1 rounded-full text-sm font-semibold ${getKnowledgeBadgeClass(
                              quiz.knowledge_level
                            )}`}
                          >
                            {getKnowledgeBadgeLabel(quiz.knowledge_level)}
                          </span>
                        )}

                        {quiz.use_adaptive_difficulty && (
                          <span
                            className={`px-3 py-1 rounded-full text-sm font-semibold ${getAdaptiveBadgeClass()}`}
                          >
                            🎯 Adaptacyjny
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-6 text-gray-600 dark:text-slate-300">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">📊</span>
                          <div>
                            <p className="text-xs text-gray-500 dark:text-slate-400">Wynik</p>
                            <p className="text-lg font-bold text-indigo-600 dark:text-indigo-300">
                              {calculatePercentage(quiz)}%
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-2xl">✅</span>
                          <div>
                            <p className="text-xs text-gray-500 dark:text-slate-400">Odpowiedzi</p>
                            <p className="text-lg font-bold text-gray-700 dark:text-slate-200">
                              {quiz.correct_answers}/{quiz.total_questions}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-2xl">📅</span>
                          <div>
                            <p className="text-xs text-gray-500 dark:text-slate-400">Data</p>
                            <p className="text-sm font-medium text-gray-700 dark:text-slate-200">
                              {new Date(quiz.started_at).toLocaleString('pl-PL', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                                second: '2-digit',
                              })}
                            </p>
                          </div>
                        </div>

                        {quiz.ended_at && quiz.started_at && (
                          <div className="flex items-center gap-2">
                            <span className="text-2xl">⏱️</span>
                            <div>
                              <p className="text-xs text-gray-500 dark:text-slate-400">Czas</p>
                              <p className="text-sm font-medium text-gray-700 dark:text-slate-200">
                                {formatQuizDuration(
                                  quiz.started_at,
                                  quiz.ended_at,
                                  quiz.total_questions,
                                  quiz.time_per_question,
                                  quiz.total_response_time
                                )}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="text-indigo-400 group-hover:text-indigo-600 group-hover:translate-x-2 transition-all">
                      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              ))}

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
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}
