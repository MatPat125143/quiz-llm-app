import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getGlobalLeaderboard,
  getUserRanking,
  getLeaderboardStats,
  getCurrentUser
} from '../../services/api';
import MainLayout from '../../layouts/MainLayout';

export default function Leaderboard() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);
  const [myRanking, setMyRanking] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('all');

  useEffect(() => {
    loadData();
  }, [period]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [userData, leaderboardData, rankingData, statsData] = await Promise.all([
        getCurrentUser(),
        getGlobalLeaderboard(period, 50),
        getUserRanking(),
        getLeaderboardStats()
      ]);
      setUser(userData);
      setLeaderboard(leaderboardData.leaderboard || []);
      setMyRanking(rankingData);
      setStats(statsData);
    } catch (err) {
      console.error('Error loading leaderboard:', err);
    } finally {
      setLoading(false);
    }
  };

  const getMedalLabel = (rank) => {
    if (rank === 1) return '1st';
    if (rank === 2) return '2nd';
    if (rank === 3) return '3rd';
    return `#${rank}`;
  };

  const getAccuracyColor = (accuracy) => {
    if (accuracy >= 80) return 'text-green-600';
    if (accuracy >= 60) return 'text-yellow-600';
    if (accuracy >= 40) return 'text-orange-600';
    return 'text-red-600';
  };

  const getAccuracyBg = (accuracy) => {
    if (accuracy >= 80) return 'bg-green-50 border-green-200';
    if (accuracy >= 60) return 'bg-yellow-50 border-yellow-200';
    if (accuracy >= 40) return 'bg-orange-50 border-orange-200';
    return 'bg-red-50 border-red-200';
  };

  if (loading) {
    return (
      <MainLayout user={user}>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Ladowanie rankingu...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout user={user}>
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2 flex items-center gap-3">
            <span className="text-5xl">Ranking</span>
            Graczy
          </h1>
          <p className="text-gray-600">
            Zobacz najlepszych graczy i sprawdz swoja pozycje w rankingu.
          </p>
        </div>

        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl p-6 text-white shadow-lg">
              <div className="text-sm uppercase tracking-wide">Aktywni gracze</div>
              <div className="text-3xl font-bold">{stats.total_users}</div>
              <div className="text-blue-100 text-sm">Uczestniczacy w quizach</div>
            </div>
            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl p-6 text-white shadow-lg">
              <div className="text-sm uppercase tracking-wide">Ukonczone quizy</div>
              <div className="text-3xl font-bold">{stats.total_quizzes}</div>
              <div className="text-purple-100 text-sm">Wszystkie sesje</div>
            </div>
            <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl p-6 text-white shadow-lg">
              <div className="text-sm uppercase tracking-wide">Zadane pytania</div>
              <div className="text-3xl font-bold">{stats.total_questions}</div>
              <div className="text-green-100 text-sm">Lacznie odpowiedzi</div>
            </div>
            <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-2xl p-6 text-white shadow-lg">
              <div className="text-sm uppercase tracking-wide">Srednia dokladnosc</div>
              <div className="text-3xl font-bold">{stats.avg_accuracy}%</div>
              <div className="text-orange-100 text-sm">Poprawne odpowiedzi</div>
            </div>
          </div>
        )}

        {myRanking && myRanking.rank && (
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-2xl p-6 mb-8 text-white shadow-xl">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-bold mb-2">Twoja pozycja</h3>
                <p className="text-indigo-100">
                  Lepszy wynik niz {myRanking.percentile}% graczy.
                </p>
              </div>
              <div className="text-right">
                <div className="text-5xl font-bold">#{myRanking.rank}</div>
                <div className="text-indigo-100">z {myRanking.total_users} graczy</div>
              </div>
            </div>
            <div className="grid grid-cols-3 gap-4 mt-6 pt-6 border-t border-indigo-400">
              <div>
                <div className="text-3xl font-bold">{myRanking.stats.total_quizzes}</div>
                <div className="text-indigo-100 text-sm">Quizy</div>
              </div>
              <div>
                <div className="text-3xl font-bold">{myRanking.stats.accuracy}%</div>
                <div className="text-indigo-100 text-sm">Dokladnosc</div>
              </div>
              <div>
                <div className="text-3xl font-bold">{myRanking.stats.total_correct}</div>
                <div className="text-indigo-100 text-sm">Poprawnych</div>
              </div>
            </div>
          </div>
        )}

        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6 mb-8">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Okres czasu</h3>
          <div className="flex gap-3">
            <button
              onClick={() => setPeriod('all')}
              className={`px-6 py-3 rounded-xl font-semibold transition-all ${period === 'all' ? 'bg-indigo-600 text-white shadow-lg' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              Caly czas
            </button>
            <button
              onClick={() => setPeriod('month')}
              className={`px-6 py-3 rounded-xl font-semibold transition-all ${period === 'month' ? 'bg-indigo-600 text-white shadow-lg' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              Ostatni miesiac
            </button>
            <button
              onClick={() => setPeriod('week')}
              className={`px-6 py-3 rounded-xl font-semibold transition-all ${period === 'week' ? 'bg-indigo-600 text-white shadow-lg' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}
            >
              Ostatni tydzien
            </button>
          </div>
        </div>

        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
          <div className="p-6 bg-gradient-to-r from-indigo-50 to-purple-50 border-b border-gray-200">
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              Top gracze
            </h2>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700">Pozycja</th>
                  <th className="px-6 py-4 text-left text-sm font-bold text-gray-700">Gracz</th>
                  <th className="px-6 py-4 text-center text-sm font-bold text-gray-700">Quizy</th>
                  <th className="px-6 py-4 text-center text-sm font-bold text-gray-700">Pytania</th>
                  <th className="px-6 py-4 text-center text-sm font-bold text-gray-700">Poprawne</th>
                  <th className="px-6 py-4 text-center text-sm font-bold text-gray-700">Dokladnosc</th>
                  <th className="px-6 py-4 text-center text-sm font-bold text-gray-700">Punkty</th>
                </tr>
              </thead>
              <tbody>
                {leaderboard.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-gray-500">
                      <p className="text-lg font-semibold">Brak danych do wyswietlenia</p>
                      <p className="text-sm mt-2">Rozegraj quiz, aby pojawic sie w rankingu.</p>
                    </td>
                  </tr>
                ) : (
                  leaderboard.map((entry) => {
                    const isCurrentUser = user && entry.user_id === user.id;
                    const isTopThree = entry.rank <= 3;

                    return (
                      <tr
                        key={entry.user_id}
                        className={`border-b border-gray-100 transition-colors ${isCurrentUser ? 'bg-indigo-50 hover:bg-indigo-100' : 'hover:bg-gray-50'}`}
                      >
                        <td className="px-6 py-4">
                          <span className={`text-2xl font-bold ${isTopThree ? 'text-3xl' : ''}`}>
                            {getMedalLabel(entry.rank)}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            {entry.avatar_url ? (
                              <img
                                src={entry.avatar_url}
                                alt={entry.username}
                                className="w-10 h-10 rounded-full border-2 border-gray-200"
                              />
                            ) : (
                              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-bold">
                                {entry.username ? entry.username.charAt(0).toUpperCase() : '?'}
                              </div>
                            )}
                            <div>
                              <div className="font-bold text-gray-800 flex items-center gap-2">
                                <span>{entry.username}</span>
                                {isCurrentUser && (
                                  <span className="ml-2 px-2 py-0.5 bg-indigo-600 text-white text-xs rounded-full">
                                    Ty
                                  </span>
                                )}
                              </div>
                              <div className="text-sm text-gray-500">{entry.email}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 border border-blue-200 rounded-lg">
                            <span className="text-blue-600 font-bold">{entry.total_quizzes}</span>
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className="text-gray-700 font-semibold">{entry.total_questions}</span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className="text-green-600 font-bold">{entry.total_correct}</span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className={`inline-flex items-center gap-1 px-4 py-2 rounded-xl border-2 font-bold ${getAccuracyBg(entry.accuracy)}`}>
                            <span className={getAccuracyColor(entry.accuracy)}>
                              {entry.accuracy}%
                            </span>
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className="text-purple-600 font-bold text-lg">{entry.total_score}</span>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        </div>

        {stats && stats.popular_topics && stats.popular_topics.length > 0 && (
          <div className="mt-8 bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              Najpopularniejsze tematy
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {stats.popular_topics.slice(0, 10).map((topic, index) => (
                <div
                  key={index}
                  className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-4 border border-gray-200"
                >
                  <div className="font-bold text-gray-800 text-sm mb-1 truncate" title={topic.topic}>
                    {topic.topic}
                  </div>
                  <div className="text-indigo-600 font-semibold">{topic.count} quizow</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {stats && stats.best_user && (
          <div className="mt-8 bg-gradient-to-r from-yellow-400 via-yellow-500 to-orange-500 rounded-2xl p-6 text-white shadow-xl">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-2xl font-bold mb-2">Najlepszy gracz</h3>
                <p className="text-yellow-100">
                  Najwyzsza dokladnosc (minimum 5 ukonczonych quizow).
                </p>
              </div>
              <div className="text-right">
                <div className="text-4xl font-bold">{stats.best_user.username}</div>
                <div className="flex items-center gap-4 mt-2 justify-end">
                  <div>
                    <div className="text-2xl font-bold">{stats.best_user.accuracy}%</div>
                    <div className="text-yellow-100 text-sm">Dokladnosc</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold">{stats.best_user.total_quizzes}</div>
                    <div className="text-yellow-100 text-sm">Quizy</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="mt-8 flex gap-4">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex-1 px-6 py-3 bg-gray-600 text-white rounded-xl hover:bg-gray-700 transition font-semibold"
          >
            Powrot do panelu
          </button>
          <button
            onClick={() => navigate('/quiz/setup')}
            className="flex-1 px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 transition font-semibold shadow-lg"
          >
            Rozpocznij quiz
          </button>
        </div>
      </div>
    </MainLayout>
  );
}
