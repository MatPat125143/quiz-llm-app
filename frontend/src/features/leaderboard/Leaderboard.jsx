import { useCallback, useEffect, useRef, useState } from 'react';
import {
  getGlobalLeaderboard,
  getLeaderboardStats
} from '../../services/api';
import MainLayout from '../../layouts/MainLayout';
import useCurrentUser from '../../hooks/useCurrentUser';
import LoadingState from '../../components/LoadingState';
import EmptyState from '../../components/EmptyState';

export default function Leaderboard() {
  const { user, loading: userLoading } = useCurrentUser();
  const [leaderboard, setLeaderboard] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const hasLoadedRef = useRef(false);
  const [period, setPeriod] = useState('all');
  const [rankingMode, setRankingMode] = useState('correct');

  const loadData = useCallback(async () => {
    if (!hasLoadedRef.current) {
      setLoading(true);
    }
    try {
      const [leaderboardData, statsData] = await Promise.all([
        getGlobalLeaderboard(period, 50),
        getLeaderboardStats()
      ]);
      setLeaderboard(leaderboardData.leaderboard || []);
      setStats(statsData);
    } catch (err) {
      console.error('Error loading leaderboard:', err);
    } finally {
      hasLoadedRef.current = true;
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const getMedalLabel = (rank) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `#${rank}`;
  };

  const getRankBadgeClass = (rank) => {
    if (rank === 1) return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    if (rank === 2) return 'bg-gray-100 text-gray-700 border-gray-200';
    if (rank === 3) return 'bg-orange-100 text-orange-800 border-orange-200';
    return 'bg-indigo-50 text-indigo-700 border-indigo-200';
  };

  const formatAvgTime = (value) => {
    const seconds = Number(value) || 0;
    if (seconds >= 60) {
      const min = Math.floor(seconds / 60);
      const sec = Math.round(seconds % 60);
      return `${min} min ${sec} sek`;
    }
    return `${Math.round(seconds)} s`;
  };

  const sortedLeaderboard = [...leaderboard].sort((a, b) => {
    if (rankingMode === 'speed') {
      const aTime = a.avg_response_time || Number.POSITIVE_INFINITY;
      const bTime = b.avg_response_time || Number.POSITIVE_INFINITY;
      return aTime - bTime;
    }
    if (rankingMode === 'quizzes') {
      return (b.total_quizzes || 0) - (a.total_quizzes || 0);
    }
    return (b.total_correct || 0) - (a.total_correct || 0);
  });

  const formatDate = (date) =>
    date.toLocaleDateString('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric' });

  const getWeekRangeLabel = () => {
    const now = new Date();
    const day = now.getDay();
    const diffToMonday = (day + 6) % 7;
    const start = new Date(now);
    start.setDate(now.getDate() - diffToMonday);
    const end = new Date(start);
    end.setDate(start.getDate() + 6);
    return `${formatDate(start)} – ${formatDate(end)}`;
  };

  const getMonthLabel = () =>
    new Date().toLocaleDateString('pl-PL', { month: 'long', year: 'numeric' });

  const periodLabel =
    period === 'week'
      ? `Tydzień: ${getWeekRangeLabel()}`
      : period === 'month'
      ? `Miesiąc: ${getMonthLabel()}`
      : 'Cały czas: wszystkie dane';

  if (loading || userLoading) {
    return (
      <MainLayout user={user}>
        <LoadingState message="Ładowanie rankingu..." fullScreen={true} />
      </MainLayout>
    );
  }

  return (
    <MainLayout user={user}>
      <div className="max-w-7xl mx-auto px-6 py-10">
        <div className="mb-8 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl p-8 text-white shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">🏆 Ranking graczy</h1>
              <p className="text-indigo-100 text-lg">
                Zobacz najlepszych graczy i sprawdź swoją pozycję w rankingu.
              </p>
            </div>
            <div className="hidden md:block text-8xl opacity-20">🏆</div>
          </div>
        </div>

        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-6 mb-8">
            {[
              {
                title: 'Aktywni gracze',
                value: stats.total_users,
                icon: '\uD83D\uDC65',
                color: 'from-blue-400 to-blue-600',
                caption: 'Uczestnicz\u0105cy w quizach',
              },
              {
                title: 'Uko\u0144czone quizy',
                value: stats.total_quizzes,
                icon: '\u2705',
                color: 'from-purple-400 to-purple-600',
                caption: 'Wszystkie sesje graczy',
              },
              {
                title: 'Średni czas odpowiedzi (sekundy)',
                value: formatAvgTime(
                  stats.average_response_time ?? stats.avg_response_time ?? 0
                ),
                icon: '⏱️',
                color: 'from-green-400 to-green-600',
                caption: 'Wszyscy gracze',
              },
              {
                title: 'Poprawne odpowiedzi',
                value: stats.correct_answers ?? 0,
                icon: '\uD83C\uDFAF',
                color: 'from-orange-400 to-orange-600',
                caption: 'Łącznie wszyscy gracze',
              },
            ].map((item) => (
              <div
                key={item.title}
                className="bg-white dark:bg-slate-900 rounded-2xl p-3 sm:p-6 shadow-lg hover:shadow-xl transition-all border border-gray-100 dark:border-slate-800"
              >
                <div className="flex items-center justify-between mb-2 sm:mb-3">
                  <div
                    className={`w-9 h-9 sm:w-12 sm:h-12 bg-gradient-to-br ${item.color} rounded-xl flex items-center justify-center`}
                  >
                    <span className="text-lg sm:text-2xl">{item.icon}</span>
                  </div>
                  <span
                    className={`text-xl sm:text-3xl font-bold bg-gradient-to-r ${item.color.replace(
                      '400',
                      '600'
                    )} bg-clip-text text-transparent`}
                  >
                    {item.value}
                  </span>
                </div>
                <p className="text-gray-600 dark:text-slate-300 font-medium text-xs sm:text-base leading-snug">
                  {item.title}
                </p>
                <p className="text-gray-400 dark:text-slate-400 text-xs sm:text-sm mt-1">{item.caption}</p>
              </div>
            ))}
          </div>
        )}

        {stats && stats.popular_topics && stats.popular_topics.length > 0 && (
          <div className="mt-8 bg-white dark:bg-slate-900 rounded-2xl shadow-lg border border-gray-100 dark:border-slate-800 p-6 mb-8">
            <h3 className="text-xl font-bold text-gray-800 dark:text-slate-100 mb-4 flex items-center gap-2">
              🔥 Najpopularniejsze tematy
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              {stats.popular_topics.slice(0, 10).map((topic, index) => (
                <div
                  key={index}
                  className="bg-gradient-to-br from-gray-50 to-gray-100 dark:from-slate-900 dark:to-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-800"
                >
                  <div
                    className="font-bold text-gray-800 dark:text-slate-100 text-sm mb-1 truncate"
                    title={topic.topic}
                  >
                    {topic.topic}
                  </div>
                  <div className="text-indigo-600 dark:text-indigo-300 font-semibold">
                    {topic.count} quizów
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-lg border border-gray-100 dark:border-slate-800 p-6 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-800 dark:text-slate-100 flex items-center gap-2">
              <span className="text-xl">🏅</span> Top gracze
            </h3>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-900/60 p-4">
              <div className="text-sm font-semibold text-gray-700 dark:text-slate-200 flex items-center gap-2">
                <span>🗓️</span> Okres czasu
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {[
                  { key: 'all', label: 'Cały czas' },
                  { key: 'month', label: 'Ostatni miesiąc' },
                  { key: 'week', label: 'Ostatni tydzień' },
                ].map((opt) => (
                  <button
                    key={opt.key}
                    onClick={() => setPeriod(opt.key)}
                    className={`px-4 py-2 text-sm rounded-lg font-semibold transition-all ${
                      period === opt.key
                        ? 'bg-white dark:bg-slate-900 text-indigo-700 dark:text-indigo-200 shadow border border-indigo-200 dark:border-indigo-500/40'
                        : 'text-gray-700 dark:text-slate-200 hover:bg-gray-200 dark:hover:bg-slate-700'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
              <div className="mt-3 text-sm font-semibold text-gray-700 dark:text-slate-200">
                {periodLabel}
              </div>
            </div>
            <div className="rounded-xl border border-gray-200 dark:border-slate-800 bg-gray-50 dark:bg-slate-900/60 p-4">
              <div className="text-sm font-semibold text-gray-700 dark:text-slate-200 flex items-center gap-2">
                <span>🏁</span> Ranking
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {[
                  { key: 'correct', label: 'Najwięcej poprawnych' },
                  { key: 'speed', label: 'Najszybszy gracz' },
                  { key: 'quizzes', label: 'Najwięcej quizów' },
                ].map((opt) => (
                  <button
                    key={opt.key}
                    onClick={() => setRankingMode(opt.key)}
                    className={`px-4 py-2 text-sm rounded-lg font-semibold transition-all ${
                      rankingMode === opt.key
                        ? 'bg-white dark:bg-slate-900 text-indigo-700 dark:text-indigo-200 shadow border border-indigo-200 dark:border-indigo-500/40'
                        : 'text-gray-700 dark:text-slate-200 hover:bg-gray-200 dark:hover:bg-slate-700'
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="mt-6 pt-6 border-t border-gray-100 dark:border-slate-800">
            {leaderboard.length === 0 ? (
              <EmptyState
                icon="🏆"
                title="Brak danych do wyświetlenia"
                description="Rozegraj quiz, aby pojawić się w rankingu."
                className="shadow-none border-0 bg-transparent dark:bg-transparent p-0"
              />
            ) : (
              <div className="space-y-3">
                {sortedLeaderboard.map((entry, index) => {
                  const displayRank = index + 1;
                  const isCurrentUser = user && entry.user_id === user.id;
                  const isTopThree = displayRank <= 3;
                  const rankingMeta =
                    rankingMode === 'speed'
                      ? {
                          label: 'Śr. czas',
                          value: formatAvgTime(entry.avg_response_time),
                        }
                      : rankingMode === 'quizzes'
                      ? {
                          label: 'Quizy',
                          value: entry.total_quizzes ?? 0,
                        }
                      : {
                          label: 'Poprawne',
                          value: entry.total_correct ?? 0,
                        };

                  return (
                    <div
                      key={entry.user_id}
                      className={`p-5 sm:p-6 border-2 rounded-xl transition-all ${
                        isCurrentUser
                          ? 'border-indigo-300 bg-indigo-50 dark:border-indigo-400/50 dark:bg-indigo-900/20'
                          : 'border-gray-100 dark:border-slate-800 bg-gradient-to-r from-white to-gray-50 dark:from-slate-900 dark:to-slate-900/70 hover:border-indigo-200 dark:hover:border-indigo-500/40 hover:shadow-md'
                      }`}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                        <div className="flex items-center gap-6 min-w-[160px]">
                          <div
                            className={`w-14 h-14 rounded-2xl border flex items-center justify-center font-bold ${getRankBadgeClass(
                              displayRank
                            )}`}
                            title={`Pozycja #${displayRank}`}
                          >
                            <span className={`text-2xl ${isTopThree ? 'text-3xl' : ''}`}>
                              {getMedalLabel(displayRank)}
                            </span>
                          </div>

                          <div className="flex items-center gap-3">
                            {entry.avatar_url ? (
                              <img
                                src={entry.avatar_url}
                                alt={entry.username}
                                className={`w-14 h-14 rounded-full border-2 ${
                                  isTopThree ? 'border-indigo-300' : 'border-gray-200'
                                } object-cover`}
                              />
                            ) : (
                              <div
                                className={`w-14 h-14 rounded-full bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center text-white font-bold border-2 ${
                                  isTopThree ? 'border-indigo-300' : 'border-gray-200'
                                }`}
                              >
                                {entry.username ? entry.username.charAt(0).toUpperCase() : '?'}
                              </div>
                            )}

                            <div className="min-w-0">
                              <div className="font-bold text-gray-800 dark:text-slate-100 flex items-center gap-2 min-w-0">
                                <span className="truncate">{entry.username}</span>
                                {isCurrentUser && (
                                  <span className="px-2 py-0.5 bg-indigo-600 text-white text-xs rounded-full shrink-0">
                                    Ty
                                  </span>
                                )}
                              </div>
                              <div className="text-xs text-gray-500 dark:text-slate-400 truncate">
                                {entry.email}
                              </div>
                            </div>
                          </div>
                        </div>

                        <div className="flex-1" />

                        <div className="sm:text-right sm:min-w-[140px]">
                          <div className="text-sm text-gray-500 dark:text-slate-400 font-semibold uppercase tracking-wide">
                            {rankingMeta.label}
                          </div>
                          <div className="text-3xl sm:text-4xl font-bold text-purple-700 dark:text-purple-300">
                            {rankingMeta.value}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

      </div>
    </MainLayout>
  );
}
