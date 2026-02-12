import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getAllUsers,
  deleteUser,
  changeUserRole,
  toggleUserStatus,
  adminSearchUsers,
  adminGetUserQuizzes,
  adminDeleteQuizSession
} from '../../services/api';
import {
  calculatePercentage
} from '../../services/helpers';
import MainLayout from '../../layouts/MainLayout';
import QuestionsManager from './QuestionsManager';
import useCurrentUser from '../../hooks/useCurrentUser';
import LoadingState from '../../components/LoadingState';
import AdminUsersSection from './users/AdminUsersSection';
import AdminUserQuizHistoryModal from './users/AdminUserQuizHistoryModal';

export default function AdminPanel() {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [currentUser, setCurrentUser] = useState(null);
  const [userFiltersOpen, setUserFiltersOpen] = useState(false);
  const [userPage, setUserPage] = useState(1);
  const [userPageSize, setUserPageSize] = useState(10);

  const [selectedUser, setSelectedUser] = useState(null);
  const [userQuizzes, setUserQuizzes] = useState([]);
  const [loadingQuizzes, setLoadingQuizzes] = useState(false);
  const [quizPage, setQuizPage] = useState(1);
  const [quizPageSize, setQuizPageSize] = useState(10);
  const [quizFiltersOpen, setQuizFiltersOpen] = useState(false);
  const [quizFilters, setQuizFilters] = useState({
    topic: '',
    difficulty: '',
    knowledgeLevel: '',
    isAdaptive: '',
    sortBy: 'date_desc',
  });

  const navigate = useNavigate();
  const redirectForbidden = useCallback(() => navigate('/403', { replace: true }), [navigate]);
  const { user: authUser, loading: userLoading } = useCurrentUser();

  const loadAdminData = useCallback(async () => {
    try {
      const usersData = await getAllUsers();
      setUsers(usersData);
    } catch (err) {
      console.error('Error loading admin data:', err);
      if (err.response?.status === 403) {
        redirectForbidden();
        return;
      }
    } finally {
      setLoading(false);
    }
  }, [redirectForbidden]);

  const applyFilters = useCallback(async () => {
    try {
      const data = await adminSearchUsers({
        query: searchQuery,
        role: roleFilter,
        is_active: statusFilter
      });
      setUsers(data);
      setUserPage(1);
    } catch (err) {
      console.error('Search error:', err);
    }
  }, [roleFilter, searchQuery, statusFilter]);

  useEffect(() => {
    loadAdminData();
  }, [loadAdminData]);

  useEffect(() => {
    if (authUser) {
      setCurrentUser(authUser);
    }
  }, [authUser]);

  useEffect(() => {
    setUserPage(1);
    applyFilters();
  }, [searchQuery, roleFilter, statusFilter, applyFilters]);

  const clearFilters = () => {
    setSearchQuery('');
    setRoleFilter('');
    setStatusFilter('');
    setUserPage(1);
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
    setQuizPage(1);
    setQuizPageSize(10);
	    setQuizFilters({
	      topic: '',
	      difficulty: '',
	      knowledgeLevel: '',
	      isAdaptive: '',
	      sortBy: 'date_desc',
	    });
      setQuizFiltersOpen(false);
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

  const clearQuizFilters = () => {
    setQuizFilters({
      topic: '',
      difficulty: '',
      knowledgeLevel: '',
      isAdaptive: '',
      sortBy: 'date_desc',
    });
    setQuizPage(1);
  };

  const filteredUserQuizzes = (() => {
    let filtered = [...userQuizzes];

    if (quizFilters.topic.trim()) {
      const topicNeedle = quizFilters.topic.toLowerCase();
      filtered = filtered.filter((q) =>
        (q.topic || '').toLowerCase().includes(topicNeedle)
        || (q.subtopic || '').toLowerCase().includes(topicNeedle)
      );
    }

    if (quizFilters.difficulty) {
      filtered = filtered.filter((q) => q.difficulty === quizFilters.difficulty);
    }

    if (quizFilters.knowledgeLevel) {
      filtered = filtered.filter((q) => q.knowledge_level === quizFilters.knowledgeLevel);
    }

    if (quizFilters.isAdaptive) {
      const adaptiveValue = quizFilters.isAdaptive === 'true';
      filtered = filtered.filter((q) => Boolean(q.use_adaptive_difficulty) === adaptiveValue);
    }

    switch (quizFilters.sortBy) {
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

    return filtered;
  })();

  const quizTotalPages = Math.max(1, Math.ceil(filteredUserQuizzes.length / quizPageSize));
  const pagedUserQuizzes = filteredUserQuizzes.slice(
    (quizPage - 1) * quizPageSize,
    quizPage * quizPageSize
  );

  if (loading || userLoading) {
    return (
      <LoadingState message="Ładowanie danych panelu..." fullScreen={true} />
    );
  }

    return (
    <MainLayout user={currentUser}>
      <div className="max-w-7xl mx-auto px-6 py-10">

        <div className="mb-8 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl p-8 text-white shadow-xl">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-2">🛠️ Panel administratora</h1>
              <p className="text-indigo-200 mt-1 text-lg">Zarządzanie systemem quizowym</p>
            </div>
            <div className="hidden md:block text-8xl opacity-20">🛠️</div>
          </div>
        </div>

        <div className="mb-8 bg-white dark:bg-slate-900 rounded-2xl shadow-lg border border-gray-100 dark:border-slate-800 p-2">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab('users')}
              className={`flex-1 py-3 px-6 rounded-xl font-semibold transition-all ${
                activeTab === 'users'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                  : 'bg-gray-50 text-gray-700 hover:bg-gray-100 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              👥 Gracze
            </button>

            <button
              onClick={() => setActiveTab('questions')}
              className={`flex-1 py-3 px-6 rounded-xl font-semibold transition-all ${
                activeTab === 'questions'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                  : 'bg-gray-50 text-gray-700 hover:bg-gray-100 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              ❓ Pytania
            </button>
          </div>
        </div>

        {activeTab === 'questions' ? (
          <QuestionsManager />
        ) : (
          <AdminUsersSection
            users={users}
            loading={loading}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            roleFilter={roleFilter}
            setRoleFilter={setRoleFilter}
            statusFilter={statusFilter}
            setStatusFilter={setStatusFilter}
            userFiltersOpen={userFiltersOpen}
            setUserFiltersOpen={setUserFiltersOpen}
            clearFilters={clearFilters}
            userPage={userPage}
            setUserPage={setUserPage}
            userPageSize={userPageSize}
            setUserPageSize={setUserPageSize}
            openUserQuizzes={openUserQuizzes}
            handleChangeRole={handleChangeRole}
            handleToggleStatus={handleToggleStatus}
            handleDeleteUser={handleDeleteUser}
          />
        )}
      </div>
      <AdminUserQuizHistoryModal
        selectedUser={selectedUser}
        setSelectedUser={setSelectedUser}
        loadingQuizzes={loadingQuizzes}
        userQuizzes={userQuizzes}
        quizFiltersOpen={quizFiltersOpen}
        setQuizFiltersOpen={setQuizFiltersOpen}
        quizFilters={quizFilters}
        setQuizFilters={setQuizFilters}
        setQuizPage={setQuizPage}
        clearQuizFilters={clearQuizFilters}
        filteredUserQuizzes={filteredUserQuizzes}
        pagedUserQuizzes={pagedUserQuizzes}
        calculatePercentage={calculatePercentage}
        navigate={navigate}
        handleDeleteSession={handleDeleteSession}
        quizPage={quizPage}
        quizTotalPages={quizTotalPages}
        quizPageSize={quizPageSize}
        setQuizPageSize={setQuizPageSize}
      />
    </MainLayout>
  );
}





