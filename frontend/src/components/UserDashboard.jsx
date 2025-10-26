import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser, getQuizHistory, logout } from '../services/api';

export default function UserDashboard() {
    const [user, setUser] = useState(null);
    const [quizzes, setQuizzes] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        loadDashboard();
    }, []);

    const loadDashboard = async () => {
        try {
            const [userData, quizData] = await Promise.all([
                getCurrentUser(),
                getQuizHistory()
            ]);
            setUser(userData);
            setQuizzes(quizData.results || quizData);
        } catch (err) {
            console.error('Error loading dashboard:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    if (loading) {
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
                    <h1 className="text-3xl font-bold text-blue-600">📊 Panel główny</h1>
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
                {/* Welcome Section */}
                <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl shadow-lg p-8 mb-8 text-white">
                    <h2 className="text-4xl font-bold mb-2">
                        Witaj ponownie, {user?.username}! 👋
                    </h2>
                    <p className="text-xl opacity-90">Gotowy na kolejny quiz?</p>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <div className="text-3xl mb-2">🎯</div>
                        <p className="text-gray-600 text-sm">Rozegrane quizy</p>
                        <p className="text-3xl font-bold text-blue-600">
                            {user?.profile?.total_quizzes_played || 0}
                        </p>
                    </div>

                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <div className="text-3xl mb-2">📝</div>
                        <p className="text-gray-600 text-sm">Wszystkie odpowiedzi</p>
                        <p className="text-3xl font-bold text-purple-600">
                            {user?.profile?.total_questions_answered || 0}
                        </p>
                    </div>

                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <div className="text-3xl mb-2">✅</div>
                        <p className="text-gray-600 text-sm">Poprawne odpowiedzi</p>
                        <p className="text-3xl font-bold text-green-600">
                            {user?.profile?.total_correct_answers || 0}
                        </p>
                    </div>

                    <div className="bg-white rounded-xl shadow-lg p-6">
                        <div className="text-3xl mb-2">🔥</div>
                        <p className="text-gray-600 text-sm">Najwyższa passa</p>
                        <p className="text-3xl font-bold text-orange-600">
                            {user?.profile?.highest_streak || 0}
                        </p>
                    </div>
                </div>

                {/* Action Buttons */}
                <div className="mb-8 grid grid-cols-1 md:grid-cols-3 gap-4">
                    <button
                        onClick={() => navigate('/quiz/setup')}
                        className="bg-gradient-to-r from-green-500 to-blue-500 text-white py-6 rounded-2xl hover:from-green-600 hover:to-blue-600 transition shadow-lg font-bold text-2xl"
                    >
                        🚀 Rozpocznij nowy quiz
                    </button>
                    <button
                        onClick={() => navigate('/quiz/questions')}
                        className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white py-6 rounded-2xl hover:from-yellow-600 hover:to-orange-600 transition shadow-lg font-bold text-2xl"
                    >
                        📖 Biblioteka pytań
                    </button>
                    <button
                        onClick={() => navigate('/quiz/history')}
                        className="bg-gradient-to-r from-purple-500 to-pink-500 text-white py-6 rounded-2xl hover:from-purple-600 hover:to-pink-600 transition shadow-lg font-bold text-2xl"
                    >
                        📚 Historia quizów
                    </button>
                </div>

                {/* Recent Quizzes */}
                <div className="bg-white rounded-xl shadow-lg p-6">
                    <h2 className="text-2xl font-bold text-gray-800 mb-6">📚 Ostatnie quizy</h2>

                    {quizzes.length === 0 ? (
                        <div className="text-center py-12">
                            <div className="text-6xl mb-4">🎮</div>
                            <p className="text-xl text-gray-600 mb-2">Brak historii quizów</p>
                            <p className="text-gray-500">Rozpocznij pierwszy quiz, aby zobaczyć wyniki tutaj!</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {quizzes.slice(0, 5).map((quiz) => (
                                <div
                                    key={quiz.id}
                                    className="border-2 border-gray-200 rounded-lg p-4 hover:border-blue-500 transition cursor-pointer"
                                    onClick={() => navigate(`/quiz/details/${quiz.id}`)}
                                >
                                    <div className="flex justify-between items-center">
                                        <div>
                                            <h3 className="text-lg font-bold text-gray-800">{quiz.topic}</h3>
                                            <p className="text-sm text-gray-500">
                                                {new Date(quiz.completed_at).toLocaleDateString('pl-PL', {
                                                    year: 'numeric',
                                                    month: 'long',
                                                    day: 'numeric',
                                                    hour: '2-digit',
                                                    minute: '2-digit'
                                                })}
                                            </p>
                                            <div className="flex gap-2 mt-2">
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
                                        <div className="text-right">
                                            <p className="text-3xl font-bold text-blue-600">
                                                {quiz.correct_answers}/{quiz.total_questions}
                                            </p>
                                            <p className="text-sm text-gray-500">{quiz.accuracy}%</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {quizzes.length > 0 && (
                        <button
                            onClick={() => navigate('/quiz/history')}
                            className="w-full mt-6 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-semibold"
                        >
                            Zobacz pełną historię ({quizzes.length > 5 ? `${quizzes.length} quizów` : `${quizzes.length} quiz${quizzes.length === 1 ? '' : 'y'}`}) →
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}