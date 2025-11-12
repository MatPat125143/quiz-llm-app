import { useState, useEffect } from 'react';
import { getCurrentUser, getQuizHistory } from '../services/api';
import { useNavigate } from 'react-router-dom';
import Layout from './Layout';

export default function UserDashboard() {
  const [user, setUser] = useState(null);
  const [quizzes, setQuizzes] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [userData, quizData] = await Promise.all([
        getCurrentUser(),
        getQuizHistory({ limit: 5 })
      ]);
      setUser(userData);
      setQuizzes(quizData.results || []);
    } catch (err) {
      console.error('Error loading dashboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const calculatePercentage = (quiz) => {
    if (!quiz.total_questions || quiz.total_questions === 0) return 0;
    return Math.round((quiz.correct_answers / quiz.total_questions) * 100);
  };

  const getKnowledgeLevelLabel = (level) => {
    const labels = {
      elementary: '🎓 Podstawowy',
      high_school: '📚 Licealny',
      university: '🎓 Uniwersytecki',
      expert: '👨‍🔬 Ekspercki'
    };
    return labels[level] || level;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-lg text-gray-600 font-medium">Ładowanie danych...</p>
        </div>
      </div>
    );
  }

  return (
    <Layout user={user}>
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Sekcja powitalna */}
        <div className="mb-8 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl p-8 text-white shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold mb-2">Witaj ponownie, {user?.username}! 👋</h2>
              <p className="text-indigo-100 text-lg">Gotowy na kolejne wyzwanie?</p>
            </div>
            <div className="hidden md:block text-8xl opacity-20">🎓</div>
          </div>
        </div>

        {/* Statystyki */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {[
            { title: 'Rozegrane quizy', value: user?.profile?.total_quizzes_played || 0, icon: '🎯', color: 'from-blue-400 to-blue-600' },
            { title: 'Wszystkie odpowiedzi', value: user?.profile?.total_questions_answered || 0, icon: '📝', color: 'from-purple-400 to-purple-600' },
            { title: 'Poprawne odpowiedzi', value: user?.profile?.total_correct_answers || 0, icon: '✅', color: 'from-green-400 to-green-600' },
            { title: 'Najwyższa passa', value: user?.profile?.highest_streak || 0, icon: '🔥', color: 'from-orange-400 to-orange-600' }
          ].map((item, i) => (
            <div
              key={i}
              className="bg-white rounded-2xl p-6 shadow-lg hover:shadow-xl transition-all border border-gray-100"
            >
              <div className="flex items-center justify-between mb-3">
                <div
                  className={`w-12 h-12 bg-gradient-to-br ${item.color} rounded-xl flex items-center justify-center`}
                >
                  <span className="text-2xl">{item.icon}</span>
                </div>
                <span
                  className={`text-3xl font-bold bg-gradient-to-r ${item.color.replace(
                    '400',
                    '600'
                  )} bg-clip-text text-transparent`}
                >
                  {item.value}
                </span>
              </div>
              <p className="text-gray-600 font-medium">{item.title}</p>
            </div>
          ))}
        </div>

        {/* Akcje */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <button
            onClick={() => navigate('/quiz/setup')}
            className="group relative overflow-hidden bg-gradient-to-br from-green-500 to-emerald-600 text-white p-8 rounded-2xl shadow-xl hover:shadow-2xl transition-all transform hover:scale-105"
          >
            <div className="relative z-10">
              <div className="text-4xl mb-3">🚀</div>
              <h3 className="text-xl font-bold mb-1">Rozpocznij Quiz</h3>
              <p className="text-green-100 text-sm">Nowe wyzwanie czeka!</p>
            </div>
            <div className="absolute inset-0 bg-gradient-to-br from-green-600 to-emerald-700 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </button>

          <button
            onClick={() => navigate('/quiz/questions')}
            className="group relative overflow-hidden bg-gradient-to-br from-amber-500 to-orange-600 text-white p-8 rounded-2xl shadow-xl hover:shadow-2xl transition-all transform hover:scale-105"
          >
            <div className="relative z-10">
              <div className="text-4xl mb-3">📚</div>
              <h3 className="text-xl font-bold mb-1">Biblioteka Pytań</h3>
              <p className="text-orange-100 text-sm">Przeglądaj wszystkie pytania</p>
            </div>
            <div className="absolute inset-0 bg-gradient-to-br from-amber-600 to-orange-700 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </button>

          <button
            onClick={() => navigate('/quiz/history')}
            className="group relative overflow-hidden bg-gradient-to-br from-purple-500 to-pink-600 text-white p-8 rounded-2xl shadow-xl hover:shadow-2xl transition-all transform hover:scale-105"
          >
            <div className="relative z-10">
              <div className="text-4xl mb-3">📖</div>
              <h3 className="text-xl font-bold mb-1">Historia Quizów</h3>
              <p className="text-purple-100 text-sm">Zobacz swoje wyniki</p>
            </div>
            <div className="absolute inset-0 bg-gradient-to-br from-purple-600 to-pink-700 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </button>
        </div>

        {/* Ostatnie quizy */}
        <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
              <span className="text-3xl">📚</span>
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
            <div className="text-center py-12">
              <div className="text-6xl mb-4">🎯</div>
              <p className="text-gray-500 text-lg mb-6">
                Nie masz jeszcze żadnych quizów
              </p>
              <button
                onClick={() => navigate('/quiz/setup')}
                className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:from-indigo-700 hover:to-purple-700 transition-all shadow-md"
              >
                Rozpocznij pierwszy quiz 🚀
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {quizzes.map((quiz) => (
                <div
                  key={quiz.id}
                  onClick={() => navigate(`/quiz/details/${quiz.id}`)}
                  className="group p-6 border-2 border-gray-100 rounded-xl hover:border-indigo-300 hover:shadow-lg transition-all cursor-pointer bg-gradient-to-r from-white to-gray-50"
                >
                  <div className="flex justify-between items-center">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <h3 className="text-xl font-bold text-gray-800 group-hover:text-indigo-600 transition-colors">
                          📚 {quiz.topic}
                        </h3>
                        <span
                          className={`px-3 py-1 rounded-full text-sm font-semibold ${
                            quiz.difficulty === 'easy'
                              ? 'bg-green-100 text-green-700'
                              : quiz.difficulty === 'medium'
                              ? 'bg-yellow-100 text-yellow-700'
                              : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {quiz.difficulty === 'easy' && '🟢 Łatwy'}
                          {quiz.difficulty === 'medium' && '🟡 Średni'}
                          {quiz.difficulty === 'hard' && '🔴 Trudny'}
                        </span>
                        {quiz.knowledge_level && (
                          <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-semibold">
                            {getKnowledgeLevelLabel(quiz.knowledge_level)}
                          </span>
                        )}
                        {quiz.use_adaptive_difficulty && (
                          <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-semibold">
                            🎯 Adaptacyjny
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-6 text-gray-600">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">📊</span>
                          <div>
                            <p className="text-xs text-gray-500">Wynik</p>
                            <p className="text-lg font-bold text-indigo-600">
                              {calculatePercentage(quiz)}%
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">✅</span>
                          <div>
                            <p className="text-xs text-gray-500">Odpowiedzi</p>
                            <p className="text-lg font-bold">
                              {quiz.correct_answers}/{quiz.total_questions}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">📅</span>
                          <div>
                            <p className="text-xs text-gray-500">Data</p>
                            <p className="text-sm font-medium">
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
                        {quiz.ended_at && quiz.started_at && (
                          <div className="flex items-center gap-2">
                            <span className="text-2xl">⏱️</span>
                            <div>
                              <p className="text-xs text-gray-500">Czas</p>
                              <p className="text-sm font-medium">
                                {Math.floor((new Date(quiz.ended_at) - new Date(quiz.started_at)) / 60000)} min
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
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}