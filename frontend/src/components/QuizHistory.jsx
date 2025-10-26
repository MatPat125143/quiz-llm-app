import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { getCurrentUser, logout } from '../services/api';

export default function QuizHistory() {
    const [quizzes, setQuizzes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [user, setUser] = useState(null);
    const [filters, setFilters] = useState({
        topic: '',
        difficulty: '',
        is_custom: ''
    });
    const [sortBy, setSortBy] = useState('-started_at');
    const [pagination, setPagination] = useState({
        page: 1,
        pageSize: 10,
        totalCount: 0,
        hasNext: false,
        hasPrevious: false
    });
    const navigate = useNavigate();

    useEffect(() => {
        loadUserData();
        loadQuizHistory();
    }, [filters, sortBy, pagination.page]);

    const loadUserData = async () => {
        try {
            const userData = await getCurrentUser();
            setUser(userData);
        } catch (err) {
            console.error('Error loading user:', err);
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const loadQuizHistory = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('access_token');
            const params = new URLSearchParams({
                page: pagination.page,
                page_size: pagination.pageSize,
                order_by: sortBy
            });

            if (filters.topic) params.append('topic', filters.topic);
            if (filters.difficulty) params.append('difficulty', filters.difficulty);
            if (filters.is_custom) params.append('is_custom', filters.is_custom);

            const response = await axios.get(`http://localhost:8000/api/quiz/history/?${params}`, {
                headers: { Authorization: `Bearer ${token}` }
            });

            setQuizzes(response.data.results);
            setPagination(prev => ({
                ...prev,
                totalCount: response.data.count,
                hasNext: response.data.next,
                hasPrevious: response.data.previous
            }));
        } catch (err) {
            console.error('Error loading quiz history:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleFilterChange = (key, value) => {
        setFilters(prev => ({ ...prev, [key]: value }));
        setPagination(prev => ({ ...prev, page: 1 })); // Reset to page 1
    };

    const handleSortChange = (value) => {
        setSortBy(value);
        setPagination(prev => ({ ...prev, page: 1 })); // Reset to page 1
    };

    const clearFilters = () => {
        setFilters({ topic: '', difficulty: '', is_custom: '' });
        setSortBy('-started_at');
        setPagination(prev => ({ ...prev, page: 1 }));
    };

    const goToPage = (page) => {
        setPagination(prev => ({ ...prev, page }));
    };

    if (loading && quizzes.length === 0) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100">
                <div className="text-2xl font-semibold text-gray-600">Ładowanie...</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-100">
            {/* Header */}
            <header className="bg-white shadow-md">
                <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
                    <h1 className="text-3xl font-bold text-blue-600">📚 Historia Quizów</h1>
                    <div className="flex items-center gap-4">
                        {/* Avatar i nazwa użytkownika */}
                        <div
                            className="flex items-center gap-3 cursor-pointer hover:bg-gray-100 p-2 rounded-lg transition"
                            onClick={() => navigate('/profile')}
                        >
                            {user?.profile?.avatar_url ? (
                                <img
                                    src={user.profile.avatar_url}
                                    alt="Avatar"
                                    className="w-10 h-10 rounded-full object-cover border-2 border-blue-500"
                                />
                            ) : (
                                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center border-2 border-blue-500">
                                    <span className="text-white font-bold text-lg">
                                        {user?.email?.[0]?.toUpperCase() || '?'}
                                    </span>
                                </div>
                            )}
                            <span className="font-semibold text-gray-800">{user?.username}</span>
                        </div>

                        {/* Dashboard button */}
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition font-semibold"
                        >
                            ← Panel główny
                        </button>

                        {/* Admin button */}
                        {user?.profile?.role === 'admin' && (
                            <button
                                onClick={() => navigate('/admin')}
                                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition font-semibold"
                            >
                                👑 Panel admina
                            </button>
                        )}

                        {/* Logout button */}
                        <button
                            onClick={handleLogout}
                            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition font-semibold"
                        >
                            Wyloguj
                        </button>
                    </div>
                </div>
            </header>

            <div className="max-w-7xl mx-auto px-4 py-8">
                {/* Filters and Sort */}
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <h2 className="text-xl font-bold text-gray-800 mb-4">Filtry i sortowanie</h2>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                        {/* Szukaj po temacie */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Szukaj tematu
                            </label>
                            <input
                                type="text"
                                value={filters.topic}
                                onChange={(e) => handleFilterChange('topic', e.target.value)}
                                placeholder="np. Matematyka"
                                className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                            />
                        </div>

                        {/* Poziom trudności */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Poziom trudności
                            </label>
                            <select
                                value={filters.difficulty}
                                onChange={(e) => handleFilterChange('difficulty', e.target.value)}
                                className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                            >
                                <option value="">Wszystkie</option>
                                <option value="easy">🟢 Łatwy</option>
                                <option value="medium">🟡 Średni</option>
                                <option value="hard">🔴 Trudny</option>
                            </select>
                        </div>

                        {/* Custom */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Typ quizu
                            </label>
                            <select
                                value={filters.is_custom}
                                onChange={(e) => handleFilterChange('is_custom', e.target.value)}
                                className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                            >
                                <option value="">Wszystkie</option>
                                <option value="false">Standardowe</option>
                                <option value="true">Custom</option>
                            </select>
                        </div>

                        {/* Sortowanie */}
                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Sortuj według
                            </label>
                            <select
                                value={sortBy}
                                onChange={(e) => handleSortChange(e.target.value)}
                                className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                            >
                                <option value="-started_at">Najnowsze</option>
                                <option value="started_at">Najstarsze</option>
                                <option value="-accuracy">Najwyższa dokładność</option>
                                <option value="accuracy">Najniższa dokładność</option>
                                <option value="topic">Temat A-Z</option>
                                <option value="-topic">Temat Z-A</option>
                                <option value="-total_questions">Najwięcej pytań</option>
                                <option value="total_questions">Najmniej pytań</option>
                            </select>
                        </div>
                    </div>

                    <button
                        onClick={clearFilters}
                        className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition font-semibold"
                    >
                        🗑️ Wyczyść filtry
                    </button>
                </div>

                {/* Results count */}
                <div className="mb-4 text-gray-600">
                    Znaleziono: <strong>{pagination.totalCount}</strong> quizów
                </div>

                {/* Quiz list */}
                {quizzes.length === 0 ? (
                    <div className="bg-white rounded-xl shadow-lg p-12 text-center">
                        <div className="text-6xl mb-4">🔍</div>
                        <p className="text-xl text-gray-600 mb-2">Brak quizów spełniających kryteria</p>
                        <p className="text-gray-500">Spróbuj zmienić filtry</p>
                    </div>
                ) : (
                    <>
                        <div className="space-y-4">
                            {quizzes.map((quiz) => (
                                <div
                                    key={quiz.id}
                                    className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition cursor-pointer"
                                    onClick={() => navigate(`/quiz/details/${quiz.id}`)}
                                >
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <h3 className="text-xl font-bold text-gray-800 mb-2">{quiz.topic}</h3>
                                            <p className="text-sm text-gray-500 mb-3">
                                                {new Date(quiz.completed_at).toLocaleDateString('pl-PL', {
                                                    year: 'numeric',
                                                    month: 'long',
                                                    day: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                            </p>
                                            <div className="flex flex-wrap gap-2">
                                                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                                                    quiz.difficulty === 'easy'
                                                        ? 'bg-green-100 text-green-800'
                                                        : quiz.difficulty === 'medium'
                                                        ? 'bg-yellow-100 text-yellow-800'
                                                        : 'bg-red-100 text-red-800'
                                                }`}>
                                                    {quiz.difficulty === 'easy' && '🟢 Łatwy'}
                                                    {quiz.difficulty === 'medium' && '🟡 Średni'}
                                                    {quiz.difficulty === 'hard' && '🔴 Trudny'}
                                                </span>
                                                {quiz.is_custom && (
                                                    <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm font-semibold">
                                                        ⚙️ Custom
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="text-right ml-4">
                                            <p className="text-4xl font-bold text-blue-600">
                                                {quiz.correct_answers}/{quiz.total_questions}
                                            </p>
                                            <p className="text-sm text-gray-500 font-semibold">{quiz.accuracy}% trafności</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Pagination */}
                        {pagination.totalCount > pagination.pageSize && (
                            <div className="mt-6 flex justify-center items-center gap-4">
                                <button
                                    onClick={() => goToPage(pagination.page - 1)}
                                    disabled={!pagination.hasPrevious}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    ← Poprzednia
                                </button>

                                <span className="text-gray-700 font-semibold">
                                    Strona {pagination.page} z {Math.ceil(pagination.totalCount / pagination.pageSize)}
                                </span>

                                <button
                                    onClick={() => goToPage(pagination.page + 1)}
                                    disabled={!pagination.hasNext}
                                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Następna →
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
}
