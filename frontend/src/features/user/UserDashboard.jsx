import { useState, useEffect } from 'react';
import { getQuizHistory } from '../../services/api';
import {
  calculatePercentage,
  getAdaptiveBadgeClass,
  getDifficultyBadgeClass,
  getDifficultyBadgeLabel,
  getKnowledgeBadgeClass,
  getKnowledgeBadgeLabel,
  formatQuizDuration
} from '../../services/helpers';
import { useNavigate } from 'react-router-dom';
import MainLayout from '../../layouts/MainLayout';
import useCurrentUser from '../../hooks/useCurrentUser';
import LoadingState from '../../components/LoadingState';

export default function UserDashboard() {
  const { user, loading: userLoading } = useCurrentUser();
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const quizData = await getQuizHistory({ limit: 5 });
      setQuizzes(quizData.results || []);
    } catch (err) {
      console.error('Error loading dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading || userLoading) {
    return (
      <LoadingState message="Ładowanie danych..." fullScreen={true} />
    );
  }

  const favoriteTopic =
    user?.profile?.favorite_topic ||
    (quizzes.length
      ? quizzes
          .map((q) => q.topic)
          .filter(Boolean)
          .reduce((acc, topic) => {
            acc[topic] = (acc[topic] || 0) + 1;
            return acc;
          }, {})
      : null);
  const favoriteTopicName =
    favoriteTopic && typeof favoriteTopic === 'object'
      ? Object.entries(favoriteTopic).sort((a, b) => b[1] - a[1])[0][0]
      : favoriteTopic || 'Brak danych';

  return (
    <MainLayout user={user}>
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl p-8 text-white shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold mb-2">Witaj ponownie, {user?.username}! 👋</h2>
              <p className="text-indigo-100 text-lg">Gotowy na kolejne wyzwanie?</p>
            </div>
            <div className="hidden md:block text-8xl opacity-20">🎓</div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-8">
          {[
            { title: 'Rozegrane gry', value: user?.profile?.total_quizzes_played || 0, icon: '🎯', color: 'from-blue-400 to-blue-600' },
            { title: 'Ulubiona kategoria', value: favoriteTopicName, icon: '🎓', color: 'from-purple-400 to-purple-600', isCategory: true },
            { title: 'Łączna liczba poprawnych odpowiedzi', value: user?.profile?.total_correct_answers || 0, icon: '✅', color: 'from-green-400 to-green-600' },
            { title: 'Najwyższa passa', value: user?.profile?.highest_streak || 0, icon: '🔥', color: 'from-orange-400 to-orange-600' }
          ].map((item, i) => (
            <div
              key={i}
              className="bg-white rounded-2xl p-3 sm:p-6 shadow-lg hover:shadow-xl transition-all border border-gray-100"
            >
          <div className="flex items-center justify-between mb-2 sm:mb-3">
            <div
              className={`w-9 h-9 sm:w-12 sm:h-12 bg-gradient-to-br ${item.color} rounded-xl flex items-center justify-center`}
            >
              <span className="text-lg sm:text-2xl">{item.icon}</span>
            </div>
            <span
              className={`${item.isCategory ? 'text-xs sm:text-lg leading-snug break-words text-right max-w-[7rem] sm:max-w-[9rem]' : 'text-xl sm:text-3xl'} font-bold bg-gradient-to-r ${item.color.replace(
                '400',
                '600'
              )} bg-clip-text text-transparent`}
            >
              {item.value}
            </span>
          </div>
              <p className="text-gray-600 font-medium text-xs sm:text-base leading-snug">{item.title}</p>
            </div>
          ))}
        </div>

        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 sm:gap-6 mb-8">
          <button
            onClick={() => navigate('/quiz/setup')}
            className="group col-span-2 md:col-span-1 relative overflow-hidden bg-gradient-to-br from-green-500 to-emerald-600 text-white p-4 sm:p-8 rounded-2xl shadow-xl hover:shadow-2xl transition-all transform hover:scale-105"
          >
            <div className="relative z-10">
              <div className="text-2xl sm:text-4xl mb-2 sm:mb-3">🚀</div>
              <h3 className="text-base sm:text-xl font-bold mb-1">Rozpocznij Quiz</h3>
              <p className="text-green-100 text-xs sm:text-sm">Nowe wyzwanie czeka!</p>
            </div>
            <div className="absolute inset-0 bg-gradient-to-br from-green-600 to-emerald-700 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </button>

          <button
            onClick={() => navigate('/quiz/questions')}
            className="group relative overflow-hidden bg-gradient-to-br from-amber-500 to-orange-600 text-white p-4 sm:p-8 rounded-2xl shadow-xl hover:shadow-2xl transition-all transform hover:scale-105"
          >
            <div className="relative z-10">
              <div className="text-2xl sm:text-4xl mb-2 sm:mb-3">📚</div>
              <h3 className="text-base sm:text-xl font-bold mb-1">Biblioteka Pytań</h3>
              <p className="text-orange-100 text-xs sm:text-sm">Przeglądaj wszystkie pytania</p>
            </div>
            <div className="absolute inset-0 bg-gradient-to-br from-amber-600 to-orange-700 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </button>

          <button
            onClick={() => navigate('/quiz/history')}
            className="group relative overflow-hidden bg-gradient-to-br from-purple-500 to-pink-600 text-white p-4 sm:p-8 rounded-2xl shadow-xl hover:shadow-2xl transition-all transform hover:scale-105"
          >
            <div className="relative z-10">
              <div className="text-2xl sm:text-4xl mb-2 sm:mb-3">📖</div>
              <h3 className="text-base sm:text-xl font-bold mb-1">Historia Quizów</h3>
              <p className="text-purple-100 text-xs sm:text-sm">Zobacz swoje wyniki</p>
            </div>
            <div className="absolute inset-0 bg-gradient-to-br from-purple-600 to-pink-700 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </button>
        </div>

        
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 sm:p-8 shadow-lg border border-gray-100 dark:border-slate-800">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 sm:mb-6">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-800 flex items-center gap-3">
              <span className="text-2xl sm:text-3xl">📚</span>
              Ostatnie Quizy
            </h2>
            {quizzes.length > 0 && (
              <button
                onClick={() => navigate('/quiz/history')}
                className="text-indigo-600 hover:text-indigo-700 font-medium text-sm"
              >
                Zobacz wszystkie →
              </button>
            )}
          </div>

          {quizzes.length === 0 ? (
            <div className="text-center py-10 sm:py-12">
              <div className="text-5xl sm:text-6xl mb-4">🎯</div>
              <p className="text-gray-500 text-base sm:text-lg mb-6">
                Nie masz jeszcze żadnych quizów
              </p>
              <button
                onClick={() => navigate('/quiz/setup')}
                className="px-5 py-2.5 sm:px-6 sm:py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:from-indigo-700 hover:to-purple-700 transition-all shadow-md"
              >
                Rozpocznij pierwszy quiz 🚀
              </button>
            </div>
          ) : (
            <div className="space-y-3 sm:space-y-4">
              {quizzes.map((quiz) => (
                <div
                  key={quiz.id}
                  onClick={() => {
                    const sessionId = quiz?.id ?? quiz?.session_id ?? quiz?.quiz_session_id;
                    if (sessionId) navigate(`/quiz/details/${sessionId}`);
                  }}
                  className="group relative p-4 sm:p-6 pr-12 sm:pr-6 border-2 border-gray-100 dark:border-slate-800 rounded-xl hover:border-indigo-300 hover:shadow-lg transition-all cursor-pointer bg-gradient-to-r from-white to-gray-50 dark:from-slate-900 dark:to-slate-800"
                >
                  <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center items-start gap-3 sm:gap-4">
                    <div className="w-full flex-1">
                      <div className="mb-3">
                        <h3 className="text-lg sm:text-xl font-bold text-gray-800 dark:text-slate-100 group-hover:text-indigo-600 dark:group-hover:text-indigo-300 transition-colors break-words">
                          {quiz.topic}
                        </h3>
                        <div className="mt-2 flex flex-col items-start gap-2 sm:flex-row sm:flex-wrap sm:items-center">
                          <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getDifficultyBadgeClass(quiz.difficulty)}`}>
                            {getDifficultyBadgeLabel(quiz.difficulty)}
                          </span>
                          {quiz.knowledge_level && (
                            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getKnowledgeBadgeClass()}`}>
                              {getKnowledgeBadgeLabel(quiz.knowledge_level)}
                            </span>
                          )}
                          {quiz.use_adaptive_difficulty && (
                            <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getAdaptiveBadgeClass()}`}>
                              🎯 Tryb adaptacyjny
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex flex-wrap gap-2 sm:gap-4 lg:gap-6 text-gray-600 dark:text-slate-300">
                        <div className="flex items-center gap-2 min-w-[105px] sm:min-w-[120px]">
                          <span className="text-xl sm:text-2xl">📊</span>
                          <div>
                            <p className="text-xs text-gray-500 dark:text-slate-400">Wynik</p>
                            <p className="text-base sm:text-lg font-bold text-indigo-600 dark:text-indigo-300">
                              {calculatePercentage(quiz)}%
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 min-w-[105px] sm:min-w-[120px]">
                          <span className="text-xl sm:text-2xl">✅</span>
                          <div>
                            <p className="text-xs text-gray-500 dark:text-slate-400">Odpowiedzi</p>
                            <p className="text-base sm:text-lg font-bold text-gray-800 dark:text-slate-100">
                              {quiz.correct_answers}/{quiz.total_questions}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 min-w-[105px] sm:min-w-[120px]">
                          <span className="text-xl sm:text-2xl">📅</span>
                          <div>
                            <p className="text-xs text-gray-500 dark:text-slate-400">Data</p>
                            <p className="text-xs sm:text-sm font-medium text-gray-700 dark:text-slate-200 break-words">
                              {new Date(quiz.started_at).toLocaleDateString('pl-PL', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </p>
                          </div>
                        </div>
                        {(quiz.ended_at || quiz.completed_at || (quiz.total_questions && quiz.time_per_question)) && (
                          <div className="flex items-center gap-2 min-w-[105px] sm:min-w-[120px]">
                            <span className="text-xl sm:text-2xl">⏱️</span>
                            <div>
                              <p className="text-xs text-gray-500 dark:text-slate-400">Czas</p>
                              <p className="text-xs sm:text-sm font-medium text-gray-700 dark:text-slate-200">
                                {formatQuizDuration(
                                  quiz?.started_at,
                                  quiz?.ended_at || quiz?.completed_at,
                                  quiz?.total_questions,
                                  quiz?.time_per_question
                                )}
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 dark:text-slate-400 group-hover:text-slate-600 dark:group-hover:text-white transition-all group-hover:translate-x-1 sm:group-hover:translate-x-2">
                      <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}

