import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getAdminDashboard,
  getAllUsers,
  deleteUser,
  changeUserRole,
  toggleUserStatus,
  logout,
  adminSearchUsers,
  adminGetUserQuizzes,
  adminDeleteQuizSession
} from '../services/api';

export default function AdminPanel() {
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const [selectedUser, setSelectedUser] = useState(null);
  const [userQuizzes, setUserQuizzes] = useState([]);
  const [loadingQuizzes, setLoadingQuizzes] = useState(false);

  const navigate = useNavigate();

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      const [statsData, usersData] = await Promise.all([
        getAdminDashboard(),
        getAllUsers()
      ]);
      setStats(statsData);
      setUsers(usersData);
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

  const handleLogout = () => {
    logout();
    navigate('/login');
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
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-blue-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-indigo-600 to-purple-600 shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-2">👑 Panel administratora</h1>
            <p className="text-indigo-200 mt-1 text-sm">Zarządzanie systemem quizowym</p>
          </div>

          <div className="flex gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="bg-white text-indigo-600 px-5 py-2 rounded-lg font-semibold shadow-sm hover:bg-indigo-50 transition"
            >
              ← Powrót
            </button>
            <button
              onClick={handleLogout}
              className="bg-red-600 text-white px-5 py-2 rounded-lg font-semibold shadow-sm hover:bg-red-700 transition"
            >
              Wyloguj
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-10">
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
              onClick={applyFilters}
              className="bg-indigo-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-indigo-700 transition"
            >
              Filtruj
            </button>
          </div>
        </div>

        {/* 👥 Tabela użytkowników */}
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6 flex items-center gap-2">👥 Zarządzanie użytkownikami</h2>

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
                      <td className="py-3 px-4 text-center">
                        {user.total_quizzes || 0}
                      </td>
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
      </main>

      {/* 📜 Modal z historią quizów */}
      {selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-3xl w-full p-6 relative">
            <button
              onClick={() => setSelectedUser(null)}
              className="absolute top-3 right-3 text-gray-600 hover:text-red-600 text-xl font-bold"
            >
              ✖
            </button>
            <h3 className="text-xl font-bold text-gray-800 mb-4">
              📜 Historia quizów — {selectedUser.username}
            </h3>

            {loadingQuizzes ? (
              <p className="text-gray-600">Ładowanie...</p>
            ) : userQuizzes.length === 0 ? (
              <p className="text-gray-500">Brak zakończonych quizów.</p>
            ) : (
              <div className="space-y-3 max-h-[60vh] overflow-y-auto">
                {userQuizzes.map((quiz) => (
                  <div
                    key={quiz.id}
                    className="p-4 border rounded-lg flex justify-between items-center hover:bg-gray-50 transition"
                  >
                    <div>
                      <p className="font-semibold text-gray-800">{quiz.topic}</p>
                      <p className="text-sm text-gray-500">
                        Wynik: {Math.round(quiz.accuracy)}% ({quiz.correct_answers}/{quiz.total_questions})
                      </p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => navigate(`/quiz/details/${quiz.id}`)}
                        className="px-3 py-1 bg-indigo-500 text-white rounded-lg text-sm hover:bg-indigo-600"
                      >
                        Szczegóły
                      </button>
                      <button
                        onClick={() => handleDeleteSession(quiz.id)}
                        className="px-3 py-1 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600"
                      >
                        🗑️ Usuń
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
