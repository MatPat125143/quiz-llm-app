import { useState, useEffect } from 'react';
import { startQuiz, getCurrentUser, logout } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function QuizSetup() {
    const [user, setUser] = useState(null);
    const [topic, setTopic] = useState('');
    const [difficulty, setDifficulty] = useState('medium');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [showAdvanced, setShowAdvanced] = useState(false);

    // Zaawansowane ustawienia
    const [questionsCount, setQuestionsCount] = useState(10);
    const [timePerQuestion, setTimePerQuestion] = useState(30);
    const [useAdaptiveDifficulty, setUseAdaptiveDifficulty] = useState(true);

    const navigate = useNavigate();

    useEffect(() => {
        loadUser();
    }, []);

    const loadUser = async () => {
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

    const predefinedTopics = [
        'Język polski',
        'Matematyka',
        'Historia',
        'Geografia',
        'Biologia',
        'Chemia',
        'Fizyka',
        'Wiedza o społeczeństwie',
        'Język angielski'
    ];

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!topic.trim()) {
            setError('Proszę wprowadzić lub wybrać temat');
            return;
        }

        setLoading(true);
        setError('');

        try {
            const response = await startQuiz(
                topic,
                difficulty,
                questionsCount,
                timePerQuestion,
                useAdaptiveDifficulty
            );
            navigate(`/quiz/play/${response.session_id}`);
        } catch (err) {
            setError('Nie udało się uruchomić quizu. Spróbuj ponownie.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100">
            {/* Header */}
            <header className="bg-white shadow-md">
                <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
                    <h1 className="text-3xl font-bold text-blue-600">🎯 Rozpocznij nowy quiz</h1>
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

            <div className="max-w-4xl mx-auto px-4 py-8">
                <div className="bg-white rounded-2xl shadow-lg p-8">
                    <div className="text-center mb-8">
                        <p className="text-gray-600 text-lg">Wybierz temat i poziom trudności</p>
                    </div>

                {error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="mb-6">
                        <label className="block text-gray-700 font-bold mb-3 text-lg">
                            Temat quizu
                        </label>
                        <input
                            type="text"
                            value={topic}
                            onChange={(e) => setTopic(e.target.value)}
                            placeholder="Wprowadź własny temat lub wybierz poniżej"
                            className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-blue-500 text-lg"
                            disabled={loading}
                        />

                        <div className="mt-4">
                            <p className="text-sm text-gray-600 mb-2 font-semibold">Lub wybierz popularny temat:</p>
                            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                                {predefinedTopics.map((t) => (
                                    <button
                                        key={t}
                                        type="button"
                                        onClick={() => setTopic(t)}
                                        className={`px-4 py-2 rounded-lg border-2 transition font-semibold text-sm ${
                                            topic === t
                                                ? 'bg-blue-500 text-white border-blue-500'
                                                : 'bg-white text-gray-700 border-gray-300 hover:border-blue-400'
                                        }`}
                                        disabled={loading}
                                    >
                                        {t}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>

                    <div className="mb-6">
                        <label className="block text-gray-700 font-bold mb-3 text-lg">
                            Poziom trudności
                        </label>
                        <div className="grid grid-cols-3 gap-4">
                            <button
                                type="button"
                                onClick={() => setDifficulty('easy')}
                                className={`py-4 rounded-lg border-2 transition font-bold ${
                                    difficulty === 'easy'
                                        ? 'bg-green-500 text-white border-green-500 shadow-lg transform scale-105'
                                        : 'bg-white text-gray-700 border-gray-300 hover:border-green-400'
                                }`}
                                disabled={loading}
                            >
                                <div className="text-3xl mb-1">😊</div>
                                <div>Łatwy</div>
                            </button>

                            <button
                                type="button"
                                onClick={() => setDifficulty('medium')}
                                className={`py-4 rounded-lg border-2 transition font-bold ${
                                    difficulty === 'medium'
                                        ? 'bg-yellow-500 text-white border-yellow-500 shadow-lg transform scale-105'
                                        : 'bg-white text-gray-700 border-gray-300 hover:border-yellow-400'
                                }`}
                                disabled={loading}
                            >
                                <div className="text-3xl mb-1">🤔</div>
                                <div>Średni</div>
                            </button>

                            <button
                                type="button"
                                onClick={() => setDifficulty('hard')}
                                className={`py-4 rounded-lg border-2 transition font-bold ${
                                    difficulty === 'hard'
                                        ? 'bg-red-500 text-white border-red-500 shadow-lg transform scale-105'
                                        : 'bg-white text-gray-700 border-gray-300 hover:border-red-400'
                                }`}
                                disabled={loading}
                            >
                                <div className="text-3xl mb-1">😰</div>
                                <div>Trudny</div>
                            </button>
                        </div>
                        {useAdaptiveDifficulty && (
                            <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-3">
                                <p className="text-sm text-blue-800">
                                    ℹ️ <strong>Adaptacyjny poziom trudności:</strong> Poziom trudności będzie automatycznie dostosowywany na podstawie Twoich odpowiedzi.
                                    Jeśli odpowiesz poprawnie na serię pytań, poziom trudności wzrośnie. W przypadku błędnych odpowiedzi, trudność zostanie zmniejszona.
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Zaawansowane ustawienia */}
                    <div className="mb-8 border-t pt-6">
                        <button
                            type="button"
                            onClick={() => setShowAdvanced(!showAdvanced)}
                            className="flex items-center justify-between w-full text-gray-700 font-bold text-lg mb-4 hover:text-blue-600 transition"
                        >
                            <span>⚙️ Ustawienia zaawansowane</span>
                            <span className="text-2xl">{showAdvanced ? '▼' : '▶'}</span>
                        </button>

                        {showAdvanced && (
                            <div className="space-y-6 bg-gray-50 rounded-lg p-6">
                                {/* Liczba pytań */}
                                <div>
                                    <label className="block text-gray-700 font-semibold mb-2">
                                        Liczba pytań: <span className="text-blue-600">{questionsCount}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="5"
                                        max="20"
                                        step="1"
                                        value={questionsCount}
                                        onChange={(e) => setQuestionsCount(Number(e.target.value))}
                                        className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                        disabled={loading}
                                    />
                                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                                        <span>5</span>
                                        <span>20</span>
                                    </div>
                                </div>

                                {/* Czas na pytanie */}
                                <div>
                                    <label className="block text-gray-700 font-semibold mb-2">
                                        Czas na pytanie: <span className="text-blue-600">{timePerQuestion}s</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="10"
                                        max="60"
                                        step="5"
                                        value={timePerQuestion}
                                        onChange={(e) => setTimePerQuestion(Number(e.target.value))}
                                        className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                                        disabled={loading}
                                    />
                                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                                        <span>10s</span>
                                        <span>60s</span>
                                    </div>
                                </div>

                                {/* Stały poziom trudności */}
                                <div className="flex items-center justify-between bg-white rounded-lg p-4 border-2 border-gray-200">
                                    <div>
                                        <label className="text-gray-700 font-semibold cursor-pointer">
                                            Adaptacyjny poziom trudności
                                        </label>
                                        <p className="text-xs text-gray-500 mt-1">
                                            {useAdaptiveDifficulty
                                                ? 'Poziom trudności dostosowuje się do Twoich odpowiedzi'
                                                : 'Stały poziom trudności przez cały quiz'}
                                        </p>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => setUseAdaptiveDifficulty(!useAdaptiveDifficulty)}
                                        className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
                                            useAdaptiveDifficulty ? 'bg-blue-600' : 'bg-gray-300'
                                        }`}
                                        disabled={loading}
                                    >
                                        <span
                                            className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                                                useAdaptiveDifficulty ? 'translate-x-7' : 'translate-x-1'
                                            }`}
                                        />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="flex gap-4">
                        <button
                            type="button"
                            onClick={() => navigate('/dashboard')}
                            className="flex-1 bg-gray-300 text-gray-700 py-4 rounded-lg hover:bg-gray-400 transition font-bold text-lg"
                            disabled={loading}
                        >
                            Anuluj
                        </button>
                        <button
                            type="submit"
                            disabled={loading}
                            className="flex-1 bg-blue-600 text-white py-4 rounded-lg hover:bg-blue-700 transition font-bold text-lg disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {loading ? 'Uruchamianie quizu...' : 'Rozpocznij quiz 🚀'}
                        </button>
                    </div>
                </form>
                </div>
            </div>
        </div>
    );
}