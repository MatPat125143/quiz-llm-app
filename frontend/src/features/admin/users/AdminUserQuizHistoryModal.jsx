import {
  getAdaptiveBadgeClass,
  getDifficultyBadgeClass,
  getDifficultyBadgeLabel,
  getKnowledgeBadgeClass,
  getKnowledgeBadgeLabel,
  formatQuizDuration
} from '../../../services/helpers';
import PaginationBar from '../../../components/PaginationBar';

export default function AdminUserQuizHistoryModal({
  selectedUser,
  setSelectedUser,
  loadingQuizzes,
  userQuizzes,
  quizFiltersOpen,
  setQuizFiltersOpen,
  quizFilters,
  setQuizFilters,
  setQuizPage,
  clearQuizFilters,
  filteredUserQuizzes,
  pagedUserQuizzes,
  calculatePercentage,
  navigate,
  handleDeleteSession,
  quizPage,
  quizTotalPages,
  quizPageSize,
  setQuizPageSize
}) {
  if (!selectedUser) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-2 sm:p-4">
      <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[92vh] overflow-hidden relative flex flex-col">
        <div className="sticky top-0 z-10 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 p-6 flex justify-between items-center">
          <h3 className="text-2xl font-bold text-white">📜 Historia quizów - {selectedUser.username}</h3>
          <button
            onClick={() => setSelectedUser(null)}
            className="text-white/90 hover:text-red-200 text-2xl font-bold transition-colors"
          >
            ✖
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 sm:p-6">
          {loadingQuizzes ? (
            <div className="text-center py-8">
              <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-slate-300">Ładowanie...</p>
            </div>
          ) : userQuizzes.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🎯</div>
              <p className="text-gray-500 dark:text-slate-300 text-lg">Brak zakończonych quizów.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="rounded-2xl bg-gradient-to-r from-white to-indigo-50/40 dark:from-slate-950/70 dark:to-slate-900/70 p-4 sm:p-5 shadow-sm">
                <div className="flex items-center justify-between gap-3 mb-4">
                  <h4 className="text-sm font-bold text-gray-800 dark:text-slate-100">Filtry historii</h4>
                  <button
                    type="button"
                    onClick={() => setQuizFiltersOpen((prev) => !prev)}
                    className="md:hidden px-3 py-2 bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-700 transition font-semibold text-sm"
                  >
                    {quizFiltersOpen ? 'Ukryj filtry' : 'Pokaż filtry'}
                  </button>
                </div>

                <div className={`${quizFiltersOpen ? 'block' : 'hidden'} md:block space-y-4`}>
                  <div className="grid grid-cols-1 xl:grid-cols-3 gap-3 sm:gap-4">
                    <div className="xl:col-span-2">
                      <label className="block text-xs font-semibold text-gray-600 dark:text-slate-300 mb-1.5">
                        Temat lub podtemat
                      </label>
                      <input
                        type="text"
                        value={quizFilters.topic}
                        onChange={(e) => {
                          setQuizFilters((prev) => ({ ...prev, topic: e.target.value }));
                          setQuizPage(1);
                        }}
                        placeholder="np. Matematyka, Równania..."
                        className="ui-input"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-gray-600 dark:text-slate-300 mb-1.5">
                        Sortowanie
                      </label>
                      <select
                        value={quizFilters.sortBy}
                        onChange={(e) => {
                          setQuizFilters((prev) => ({ ...prev, sortBy: e.target.value }));
                          setQuizPage(1);
                        }}
                        className="ui-select"
                      >
                        <option value="date_desc">Data: najnowsze</option>
                        <option value="date_asc">Data: najstarsze</option>
                        <option value="score_desc">Wynik: malejąco</option>
                        <option value="score_asc">Wynik: rosnąco</option>
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-600 dark:text-slate-300 mb-1.5">
                      Poziom trudności
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {[
                        { value: 'easy', label: '🟢 Łatwy' },
                        { value: 'medium', label: '🟡 Średni' },
                        { value: 'hard', label: '🔴 Trudny' },
                      ].map((opt) => {
                        const active = quizFilters.difficulty === opt.value;
                        return (
                          <button
                            key={opt.value}
                            type="button"
                            onClick={() => {
                              setQuizFilters((prev) => ({
                                ...prev,
                                difficulty: active ? '' : opt.value
                              }));
                              setQuizPage(1);
                            }}
                            className={`px-3 py-2 rounded-full border-2 text-sm font-semibold transition-all ${
                              active
                                ? `${getDifficultyBadgeClass(opt.value)} border-transparent shadow`
                                : `${getDifficultyBadgeClass(opt.value)} border-transparent opacity-80 hover:opacity-100`
                            }`}
                          >
                            {opt.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-600 dark:text-slate-300 mb-1.5">
                      Poziom wiedzy
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {[
                        { value: 'elementary', label: '🏫 Podstawówka' },
                        { value: 'high_school', label: '🎓 Liceum' },
                        { value: 'university', label: '🏛️ Studia' },
                        { value: 'expert', label: '⭐ Ekspert' },
                      ].map((opt) => {
                        const active = quizFilters.knowledgeLevel === opt.value;
                        return (
                          <button
                            key={opt.value}
                            type="button"
                            onClick={() => {
                              setQuizFilters((prev) => ({
                                ...prev,
                                knowledgeLevel: active ? '' : opt.value
                              }));
                              setQuizPage(1);
                            }}
                            className={`px-3 py-2 rounded-full border-2 text-sm font-semibold transition-all ${
                              active
                                ? `${getKnowledgeBadgeClass(opt.value)} shadow`
                                : 'bg-gray-100 text-gray-800 border-gray-300 hover:bg-gray-200 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-700'
                            }`}
                          >
                            {opt.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-gray-600 dark:text-slate-300 mb-1.5">
                      Tryb quizu
                    </label>
                    <div className="flex flex-wrap gap-2 items-center">
                      {[
                        { value: 'true', label: '🎯 Adaptacyjny' },
                        { value: 'false', label: '📘 Klasyczny' },
                      ].map((opt) => {
                        const active = quizFilters.isAdaptive === opt.value;
                        return (
                          <button
                            key={opt.value}
                            type="button"
                            onClick={() => {
                              setQuizFilters((prev) => ({
                                ...prev,
                                isAdaptive: active ? '' : opt.value
                              }));
                              setQuizPage(1);
                            }}
                            className={`px-3 py-2 rounded-full border-2 text-sm font-semibold transition-all ${
                              active
                                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-indigo-600 shadow'
                                : 'bg-gray-100 text-gray-800 border-gray-300 hover:bg-gray-200 dark:bg-slate-800 dark:text-slate-200 dark:border-slate-700 dark:hover:bg-slate-700'
                            }`}
                          >
                            {opt.label}
                          </button>
                        );
                      })}

                      <button
                        type="button"
                        onClick={clearQuizFilters}
                        className="ml-auto px-4 py-2 bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-700 transition font-semibold text-sm"
                      >
                        🗑️ Wyczyść filtry
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white dark:bg-slate-900 rounded-2xl p-4 sm:p-6 shadow-lg">
                <div className="mb-4 text-gray-700 dark:text-slate-200 font-medium">
                  Znaleziono: <span className="text-indigo-600 font-bold">{filteredUserQuizzes.length}</span> quizów
                </div>

                {filteredUserQuizzes.length === 0 ? (
                  <div className="text-center py-10 text-gray-500 dark:text-slate-300">
                    Brak quizów dla wybranych filtrów.
                  </div>
                ) : (
                  pagedUserQuizzes.map((quiz) => (
                    <div
                      key={quiz.id}
                      className="group p-6 border-2 border-gray-100 dark:border-slate-800 rounded-xl hover:border-indigo-300 hover:shadow-lg bg-gradient-to-r from-white to-gray-50 dark:from-slate-950 dark:to-slate-900 transition"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <h4 className="text-xl font-bold text-gray-800 dark:text-slate-100 mb-3">
                            {quiz.topic}
                            {quiz.subtopic && (
                              <span className="block mt-1 text-sm font-semibold text-indigo-600 dark:text-indigo-300">
                                {quiz.subtopic}
                              </span>
                            )}
                          </h4>

                          <div className="flex items-center gap-3 mb-3 flex-wrap">
                            <span
                              className={`px-3 py-1 rounded-full text-sm font-semibold ${getDifficultyBadgeClass(quiz.difficulty)}`}
                            >
                              {getDifficultyBadgeLabel(quiz.difficulty)}
                            </span>

                            {quiz.knowledge_level && (
                              <span
                                className={`px-3 py-1 rounded-full text-sm font-semibold ${getKnowledgeBadgeClass(quiz.knowledge_level)}`}
                              >
                                {getKnowledgeBadgeLabel(quiz.knowledge_level)}
                              </span>
                            )}

                            {quiz.use_adaptive_difficulty && (
                              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getAdaptiveBadgeClass()}`}>
                                🎯 Tryb adaptacyjny
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
                                <p className="text-lg font-bold text-gray-800 dark:text-slate-100">
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
                                    second: '2-digit'
                                  })}
                                </p>
                              </div>
                            </div>

                            {quiz.ended_at && (
                              <div className="flex items-center gap-2">
                                <span className="text-2xl">📊</span>
                                <div>
                                  <p className="text-xs text-gray-500 dark:text-slate-400">Czas</p>
                                  <p className="text-sm font-medium text-gray-700 dark:text-slate-200">
                                    {formatQuizDuration(quiz.started_at, quiz.ended_at)}
                                  </p>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex gap-2 ml-4">
                          <button
                            onClick={() => navigate(`/quiz/details/${quiz.id}`, { state: { fromAdmin: true } })}
                            className="px-4 py-2 bg-indigo-500 text-white rounded-lg text-sm font-semibold hover:bg-indigo-600"
                          >
                            Szczegóły
                          </button>

                          <button
                            onClick={() => handleDeleteSession(quiz.id)}
                            className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-semibold hover:bg-red-600"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}

                {filteredUserQuizzes.length > 0 && (
                  <PaginationBar
                    page={quizPage}
                    totalPages={quizTotalPages}
                    hasPrev={quizPage > 1}
                    hasNext={quizPage < quizTotalPages}
                    loading={loadingQuizzes}
                    onPrev={() => setQuizPage((p) => Math.max(1, p - 1))}
                    onNext={() => setQuizPage((p) => Math.min(quizTotalPages, p + 1))}
                    pageSize={quizPageSize}
                    onPageSizeChange={(size) => {
                      setQuizPageSize(size);
                      setQuizPage(1);
                    }}
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
