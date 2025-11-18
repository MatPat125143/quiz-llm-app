import { useState, useEffect } from 'react';
import { getQuizHistory, getCurrentUser } from '../../services/api';
import { calculatePercentage, getKnowledgeLevelLabel } from '../../services/helpers';
import { useNavigate } from 'react-router-dom';
import MainLayout from '../../layouts/MainLayout';

export default function QuizHistory() {
    const [user, setUser] = useState(null);
    const [quizzes, setQuizzes] = useState([]);
    const [filteredQuizzes, setFilteredQuizzes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        topic: '',
        difficulty: '',
        knowledgeLevel: '',
        sortBy: 'date_desc',
        is_custom: ''
    });
    const navigate = useNavigate();

    useEffect(() => {
        loadData();
    }, []);

    useEffect(() => {
        applyFilters();
    }, [filters, quizzes]);

    const loadData = async () => {
        try {
            const [userData, quizData] = await Promise.all([
                getCurrentUser(),
                getQuizHistory()
            ]);
            setUser(userData);
            setQuizzes(quizData.results || []);
        } catch (err) {
            console.error('Error loading history:', err);
        } finally {
            setLoading(false);
        }
    };

    const applyFilters = () => {
        let filtered = [...quizzes];

        if (filters.topic) {
            filtered = filtered.filter(q =>
                q.topic.toLowerCase().includes(filters.topic.toLowerCase()) ||
                (q.subtopic && q.subtopic.toLowerCase().includes(filters.topic.toLowerCase()))
            );
        }

        if (filters.difficulty) {
            filtered = filtered.filter(q => q.difficulty === filters.difficulty);
        }

        if (filters.knowledgeLevel) {
            filtered = filtered.filter(q => q.knowledge_level === filters.knowledgeLevel);
        }

        if (filters.is_custom) {
            const isCustomBool = filters.is_custom === 'true';
            filtered = filtered.filter(q => q.is_custom === isCustomBool);
        }

        switch (filters.sortBy) {
            case 'date_desc':
                filtered.sort((a, b) => new Date(b.started_at) - new Date(a.started_at));
                break;
            case 'date_asc':
                filtered.sort((a, b) => new Date(a.started_at) - new Date(b.started_at));
                break;
            case 'score_desc':
                filtered.sort((a, b) =>
                    (b.correct_answers / b.total_questions) - (a.correct_answers / a.total_questions)
                );
                break;
            case 'score_asc':
                filtered.sort((a, b) =>
                    (a.correct_answers / a.total_questions) - (b.correct_answers / b.total_questions)
                );
                break;
        }

        setFilteredQuizzes(filtered);
    };

    const handleFilterChange = (key, value) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };

    const clearFilters = () => {
        setFilters({
            topic: '',
            difficulty: '',
            knowledgeLevel: '',
            sortBy: 'date_desc',
            is_custom: ''
        });
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
                <div className="text-center">
                    <div className="w-16 h-16 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                    <p className="text-lg text-gray-600 font-medium">Ładowanie historii...</p>
                </div>
            </div>
        );
    }

    const averageScore = quizzes.length > 0
        ? Math.round(
            (quizzes.reduce((sum, q) => sum + (q.correct_answers / q.total_questions), 0) / quizzes.length) * 100
        )
        : 0;

    const bestScore = quizzes.length > 0
        ? Math.round(
            Math.max(...quizzes.map(q => (q.correct_answers / q.total_questions) * 100))
        )
        : 0;

    return (
        <MainLayout user={user}>
            <div className="max-w-7xl mx-auto px-6 py-8">
                <div className="bg-white rounded-xl p-6 shadow-lg border border-gray-100 mb-8">
                    <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                        <span className="text-2xl">🔍</span>
                        Filtry i sortowanie
                    </h2>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                        <div className="md:col-span-2">
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Szukaj w temacie lub podtemacie quizu
                            </label>
                            <input
                                type="text"
                                value={filters.topic}
                                onChange={(e) => handleFilterChange('topic', e.target.value)}
                                placeholder="np. Matematyka, Algebra, Historia..."
                                className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 transition"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Rodzaj quizu
                            </label>
                            <select
                                value={filters.is_custom}
                                onChange={(e) => handleFilterChange('is_custom', e.target.value)}
                                className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 transition"
                            >
                                <option value="">Wszystkie</option>
                                <option value="false">Adaptacyjne</option>
                                <option value="true">Standardowe</option>
                            </select>
                        </div>

                        <div>
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Sortuj według
                            </label>
                            <select
                                value={filters.sortBy}
                                onChange={(e) => handleFilterChange('sortBy', e.target.value)}
                                className="w-full px-4 py-2 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 transition"
                            >
                                <option value="date_desc">Najnowsze</option>
                                <option value="date_asc">Najstarsze</option>
                                <option value="score_desc">Najlepszy wynik</option>
                                <option value="score_asc">Najgorszy wynik</option>
                            </select>
                        </div>

                        <div className="md:col-span-4 mt-2">
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Poziom trudności
                            </label>
                            <div className="flex flex-wrap gap-2">
                                {[
                                    { value: 'easy', label: '🟢 Łatwy' },
                                    { value: 'medium', label: '🟡 Średni' },
                                    { value: 'hard', label: '🔴 Trudny' },
                                ].map((opt) => {
                                    const active = filters.difficulty === opt.value;
                                    return (
                                        <button
                                            key={opt.value}
                                            type="button"
                                            onClick={() =>
                                                handleFilterChange('difficulty', active ? '' : opt.value)
                                            }
                                            className={`px-3 py-1 rounded-full border-2 text-sm font-semibold transition-all ${
                                                active
                                                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-indigo-600 shadow'
                                                    : 'bg-gray-100 text-gray-800 border-gray-300 hover:bg-gray-200'
                                            }`}
                                        >
                                            {opt.label}
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        <div className="md:col-span-4 mt-2">
                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                Poziom wiedzy
                            </label>
                            <div className="flex flex-wrap gap-2">
                                {[
                                    { value: 'elementary', label: '📚 Podstawowa' },
                                    { value: 'high_school', label: '🎓 Liceum' },
                                    { value: 'university', label: '🎯 Studia' },
                                    { value: 'expert', label: '🏆 Ekspert' },
                                ].map((opt) => {
                                    const active = filters.knowledgeLevel === opt.value;
                                    return (
                                        <button
                                            key={opt.value}
                                            type="button"
                                            onClick={() =>
                                                handleFilterChange('knowledgeLevel', active ? '' : opt.value)
                                            }
                                            className={`px-3 py-1 rounded-full border-2 text-sm font-semibold transition-all ${
                                                active
                                                    ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-indigo-600 shadow'
                                                    : 'bg-gray-100 text-gray-800 border-gray-300 hover:bg-gray-200'
                                            }`}
                                        >
                                            {opt.label}
                                        </button>
                                    );
                                })}

                                <button
                                    type="button"
                                    onClick={clearFilters}
                                    className="ml-auto px-4 py-2 bg-gray-100 text-gray-700 rounded-xl hover:bg-gray-200 transition font-semibold flex items-center gap-2"
                                >
                                    🗑️ Wyczyść filtry
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 bg-gradient-to-br from-blue-400 to-blue-600 rounded-xl flex items-center justify-center">
                                <span className="text-2xl">📊</span>
                            </div>
                            <div>
                                <p className="text-gray-600 text-sm font-medium">Wszystkie quizy</p>
                                <p className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent">
                                    {quizzes.length}
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 bg-gradient-to-br from-green-400 to-green-600 rounded-xl flex items-center justify-center">
                                <span className="text-2xl">📈</span>
                            </div>
                            <div>
                                <p className="text-gray-600 text-sm font-medium">Średni wynik</p>
                                <p className="text-3xl font-bold bg-gradient-to-r from-green-600 to-green-800 bg-clip-text text-transparent">
                                    {averageScore}%
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white rounded-2xl p-6 shadow-lg border border-gray-100">
                        <div className="flex items-center gap-4">
                            <div className="w-14 h-14 bg-gradient-to-br from-purple-400 to-purple-600 rounded-xl flex items-center justify-center">
                                <span className="text-2xl">🏆</span>
                            </div>
                            <div>
                                <p className="text-gray-600 text-sm font-medium">Najlepszy wynik</p>
                                <p className="text-3xl font-bold bg-gradient-to-r from-purple-600 to-purple-800 bg-clip-text text-transparent">
                                    {bestScore}%
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
                            <span className="text-3xl">📚</span>
                            Twoje Quizy
                        </h2>
                        <span className="text-gray-600 font-medium">
                            Znaleziono: <span className="text-indigo-600 font-bold">{filteredQuizzes.length}</span>
                        </span>
                    </div>

                    {filteredQuizzes.length === 0 ? (
                        <div className="text-center py-16">
                            <div className="text-6xl mb-4">🔍</div>
                            <p className="text-gray-500 text-lg mb-6">
                                {quizzes.length === 0 ? 'Nie masz jeszcze żadnych quizów' : 'Brak wyników dla wybranych filtrów'}
                            </p>
                            {quizzes.length === 0 && (
                                <button
                                    onClick={() => navigate('/quiz/setup')}
                                    className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl font-medium hover:from-indigo-700 hover:to-purple-700 transition-all shadow-md"
                                >
                                    Rozpocznij pierwszy quiz 🚀
                                </button>
                            )}
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {filteredQuizzes.map((quiz) => (
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
                                                    {quiz.subtopic && (
                                                        <span className="text-base font-normal text-gray-600 ml-2">
                                                            → {quiz.subtopic}
                                                        </span>
                                                    )}
                                                </h3>
                                            </div>

                                            <div className="flex flex-wrap gap-2 mb-3">
                                                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                                                    quiz.difficulty === 'easy'
                                                        ? 'bg-green-100 text-green-700'
                                                        : quiz.difficulty === 'medium'
                                                        ? 'bg-yellow-100 text-yellow-700'
                                                        : 'bg-red-100 text-red-700'
                                                }`}>
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
        </MainLayout>
    );
}
