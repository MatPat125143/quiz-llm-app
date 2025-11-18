import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getAdminDashboard,
  getAllUsers,
  deleteUser,
  changeUserRole,
  toggleUserStatus,
  adminSearchUsers,
  adminGetUserQuizzes,
  adminDeleteQuizSession,
  getCurrentUser
} from '../../services/api';
import { calculatePercentage, getKnowledgeLevelLabel } from '../../services/helpers';
import MainLayout from '../../layouts/MainLayout';

export default function AdminPanel() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentUser, setCurrentUser] = useState(null);

  const [selectedUser, setSelectedUser] = useState(null);
  const [userQuizzes, setUserQuizzes] = useState([]);
  const [loadingQuizzes, setLoadingQuizzes] = useState(false);

  const navigate = useNavigate();

  useEffect(() => {
    loadAdminData();
  }, []);

  // Automatyczne wyszukiwanie przy zmianie filtrów
  useEffect(() => {
    applyFilters();
  }, [searchQuery, roleFilter, statusFilter]);

  const loadAdminData = async () => {
    try {
      const [statsData, usersData, userData] = await Promise.all([
        getAdminDashboard(),
        getAllUsers(),
        getCurrentUser()
      ]);
      setStats(statsData);
      setUsers(usersData);
      setCurrentUser(userData);
    } catch (err) {
      console.error('Error loading admin data:', err);
      if (err.response?.status === 403) {
        alert('Brak uprawnień administratora');
        navigate('/dashboard');
      }
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = async () => {
    try {
      const data = await adminSearchUsers({
        query: searchQuery,
        role: roleFilter,
        is_active: statusFilter
      });
      setUsers(data);
    } catch (err) {
      console.error('Search error:', err);
    }
  };

  const clearFilters = () => {
    setSearchQuery('');
    setRoleFilter('');
    setStatusFilter('');
  };

  const handleDeleteUser = async (userId, email) => {
    if (!confirm(`Czy na pewno chcesz usunąć użytkownika ${email}?`)) return;
    try {
      await deleteUser(userId);
      await loadAdminData();
    } catch (err) {
      console.error('Delete error:', err);
      alert('Nie udało się usunąć użytkownika');
    }
  };

  const handleChangeRole = async (userId, currentRole) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    if (!confirm(`Zmienić rolę użytkownika na ${newRole === 'admin' ? 'ADMIN' : 'USER'}?`)) return;
    try {
      await changeUserRole(userId, newRole);
      await loadAdminData();
    } catch (err) {
      console.error('Role change error:', err);
      alert('Nie udało się zmienić roli');
    }
  };

  const handleToggleStatus = async (userId, isActive) => {
    const action = isActive ? 'dezaktywować' : 'aktywować';
    if (!confirm(`Czy na pewno chcesz ${action} tego użytkownika?`)) return;
    try {
      await toggleUserStatus(userId);
      await loadAdminData();
    } catch (err) {
      console.error('Toggle status error:', err);
      alert('Nie udało się zmienić statusu');
    }
  };

  const openUserQuizzes = async (user) => {
    setSelectedUser(user);
    setLoadingQuizzes(true);
    try {
      const data = await adminGetUserQuizzes(user.id);
      setUserQuizzes(data);
    } catch (err) {
      console.error('Error loading user quizzes:', err);
    } finally {
      setLoadingQuizzes(false);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!confirm('Czy na pewno chcesz usunąć tę sesję quizu?')) return;
    try {
      await adminDeleteQuizSession(sessionId);
      setUserQuizzes((prev) => prev.filter((q) => q.id !== sessionId));
      alert('Sesja quizu została usunięta.');
    } catch (err) {
      console.error('Delete session error:', err);
      alert('Nie udało się usunąć sesji quizu');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-purple-50 to-blue-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-700 font-semibold text-lg">Ładowanie danych panelu...</p>
        </div>
      </div>
    );
  }

  return (
    <MainLayout user={currentUser}>
      <div className="max-w-7xl mx-auto px-6 py-10">
        {/* Header sekcji admina */}
        <div className="mb-8 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl p-8 text-white shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">
                👑 Panel administratora
              </h1>
              <p className="text-indigo-200 mt-1 text-lg">Zarządzanie systemem quizowym</p>
            </div>
            <div className="hidden md:block text-8xl opacity-20">👑</div>
          </div>
        </div>

        {/* 🔍 Filtry */}
        <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100 mb-10">
          <h2 className="text-xl font-bold text-gray-800 mb-4">🔍 Wyszukiwarka użytkowników</h2>
          <div className="flex flex-col sm:flex-row gap-4 items-end">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-600 mb-1">Szukaj</label>
              <input
                type="text"
                placeholder="Wpisz nazwę lub e-mail..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Rola</label>
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="border border-gray-300 rounded-lg px-4 py-2"
              >
                <option value="">Wszystkie</option>
                <option value="admin">Admin</option>
                <option value="user">User</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Status</label>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="border border-gray-300 rounded-lg px-4 py-2"
              >
                <option value="">Wszystkie</option>
                <option value="true">Aktywni</option>
                <option value="false">Nieaktywni</option>
              </select>
            </div>

            <button
              onClick={clearFilters}
              className="bg-gray-100 text-gray-700 px-6 py-2 rounded-lg font-semibold hover:bg-gray-200 transition"
            >
              🗑️ Wyczyść
            </button>
          </div>
        </div>

        {/* 👥 Tabela użytkowników */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">
            👥 Zarządzanie użytkownikami
          </h2>

          <div className="overflow-x-auto rounded-lg border border-gray-200">
            <table className="w-full text-sm">
              <thead className="bg-indigo-600 text-white">
                <tr>
                  <th className="text-left py-3 px-4">ID</th>
                  <th className="text-left py-3 px-4">Email</th>
                  <th className="text-left py-3 px-4">Nazwa użytkownika</th>
                  <th className="text-left py-3 px-4">Rola</th>
                  <th className="text-left py-3 px-4">Status</th>
                  <th className="text-center py-3 px-4">Quizy</th>
                  <th className="text-center py-3 px-4">Akcje</th>
                </tr>
              </thead>
              <tbody>
                {users.length > 0 ? (
                  users.map((user) => (
                    <tr key={user.id} className="border-b border-gray-100 hover:bg-indigo-50 transition">
                      <td className="py-3 px-4">{user.id}</td>
                      <td className="py-3 px-4">{user.email}</td>
                      <td className="py-3 px-4 font-semibold">{user.username}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            user.role === 'admin'
                              ? 'bg-purple-100 text-purple-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {user.role === 'admin' ? '👑 ADMIN' : '👤 USER'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            user.is_active
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {user.is_active ? '✅ Aktywny' : '❌ Nieaktywny'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">{user.total_quizzes || 0}</td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex justify-center gap-2">
                          <button
                            onClick={() => openUserQuizzes(user)}
                            className="bg-indigo-500 hover:bg-indigo-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition"
                          >
                            📜
                          </button>
                          <button
                            onClick={() => handleChangeRole(user.id, user.role)}
                            className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition"
                            title="Zmień rolę"
                          >
                            🔄
                          </button>
                          <button
                            onClick={() => handleToggleStatus(user.id, user.is_active)}
                            className="bg-yellow-500 hover:bg-yellow-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition"
                            title={user.is_active ? 'Dezaktywuj' : 'Aktywuj'}
                          >
                            {user.is_active ? '🔒' : '🔓'}
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id, user.email)}
                            className="bg-red-500 hover:bg-red-600 text-white px-3 py-1.5 rounded-lg text-xs font-semibold transition"
                            title="Usuń użytkownika"
                          >
                            🗑️
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="7" className="text-center py-10 text-gray-500">
                      Brak użytkowników do wyświetlenia
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* 📜 Modal z historią quizów */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto relative">
            <div className="sticky top-0 bg-white border-b border-gray-200 p-6 flex justify-between items-center z-10">
              <h3 className="text-2xl font-bold text-gray-800">
                📜 Historia quizów — {selectedUser.username}
              </h3>
              <button
                onClick={() => setSelectedUser(null)}
                className="text-gray-600 hover:text-red-600 text-2xl font-bold transition"
              >
                ✖
              </button>
            </div>

            <div className="p-6">
              {loadingQuizzes ? (
                <div className="text-center py-8">
                  <div className="w-12 h-12 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                  <p className="text-gray-600">Ładowanie...</p>
                </div>
              ) : userQuizzes.length === 0 ? (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🎯</div>
                  <p className="text-gray-500 text-lg">Brak zakończonych quizów.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {userQuizzes.map((quiz) => (
                    <div
                      key={quiz.id}
                      className="group p-6 border-2 border-gray-100 rounded-xl hover:border-indigo-300 hover:shadow-lg transition-all bg-gradient-to-r from-white to-gray-50"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div className="flex-1">
                          <div className="mb-3">
                            <h4 className="text-xl font-bold text-gray-800 inline-flex items-center gap-2">
                              📚 {quiz.topic}
                              {quiz.subtopic && (
                                <span className="text-base font-normal text-indigo-600">
                                  → {quiz.subtopic}
                                </span>
                              )}
                            </h4>
                          </div>

                          <div className="flex items-center gap-3 mb-3 flex-wrap">
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
                                    {Math.floor(
                                      (new Date(quiz.ended_at) - new Date(quiz.started_at)) / 60000
                                    )}{' '}
                                    min
                                  </p>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex gap-2 ml-4">
                          <button
                              onClick={() => navigate(`/quiz/details/${quiz.id}`, { state: { fromAdmin: true } })}
                              className="px-4 py-2 bg-indigo-500 text-white rounded-lg text-sm font-semibold hover:bg-indigo-600 transition"
                            >
                              Szczegóły
                            </button>
                          <button
                            onClick={() => handleDeleteSession(quiz.id)}
                            className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm font-semibold hover:bg-red-600 transition"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
}