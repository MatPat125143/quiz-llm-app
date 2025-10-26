import { useState, useEffect } from 'react';
import { getQuestionsLibrary } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function QuestionsLibrary() {
    const navigate = useNavigate();
    const [questions, setQuestions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({
        search: '',
        topic: '',
        difficulty_min: '',
        difficulty_max: '',
        page: 1
    });
    const [totalCount, setTotalCount] = useState(0);
    const [expandedQuestion, setExpandedQuestion] = useState(null);

    useEffect(() => {
        loadQuestions();
    }, [filters]);

    const loadQuestions = async () => {
        try {
            setLoading(true);
            const params = {
                ...filters,
                page_size: 20
            };

            // Usuń puste filtry
            Object.keys(params).forEach(key => {
                if (params[key] === '') delete params[key];
            });

            const data = await getQuestionsLibrary(params);
            setQuestions(data.results);
            setTotalCount(data.count);
        } catch (err) {
            console.error('Error loading questions:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleFilterChange = (key, value) => {
        setFilters(prev => ({
            ...prev,
            [key]: value,
            page: 1  // Reset to first page when filtering
        }));
    };

    const getDifficultyColor = (level) => {
        if (level <= 3) return 'text-green-600 bg-green-100';
        if (level <= 6) return 'text-yellow-600 bg-yellow-100';
        return 'text-red-600 bg-red-100';
    };

    const getDifficultyLabel = (level) => {
        if (level <= 3) return 'Łatwy';
        if (level <= 6) return 'Średni';
        return 'Trudny';
    };

    return (
        <div className="min-h-screen bg-gray-100 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <div className="flex justify-between items-center">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">📚 Biblioteka Pytań</h1>
                            <p className="text-gray-600 mt-2">
                                Przeglądaj wszystkie pytania quizowe z wyjaśnieniami i statystykami
                            </p>
                        </div>
                        <button
                            onClick={() => navigate('/dashboard')}
                            className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition"
                        >
                            ← Powrót
                        </button>
                    </div>

                    {/* Filters */}
                    <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
                        <input
                            type="text"
                            placeholder="🔍 Szukaj pytania..."
                            value={filters.search}
                            onChange={(e) => handleFilterChange('search', e.target.value)}
                            className="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />

                        <input
                            type="text"
                            placeholder="Temat (np. Matematyka)"
                            value={filters.topic}
                            onChange={(e) => handleFilterChange('topic', e.target.value)}
                            className="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />

                        <input
                            type="number"
                            placeholder="Trudność min (1-10)"
                            min="1"
                            max="10"
                            value={filters.difficulty_min}
                            onChange={(e) => handleFilterChange('difficulty_min', e.target.value)}
                            className="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />

                        <input
                            type="number"
                            placeholder="Trudność max (1-10)"
                            min="1"
                            max="10"
                            value={filters.difficulty_max}
                            onChange={(e) => handleFilterChange('difficulty_max', e.target.value)}
                            className="border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>

                    {/* Stats */}
                    <div className="mt-4 text-gray-600">
                        Znaleziono: <strong>{totalCount}</strong> pytań
                    </div>
                </div>

                {/* Questions List */}
                {loading ? (
                    <div className="bg-white rounded-lg shadow-md p-12 text-center">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                        <p className="mt-4 text-gray-600">Ładowanie pytań...</p>
                    </div>
                ) : questions.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-md p-12 text-center">
                        <div className="text-6xl mb-4">🔍</div>
                        <h3 className="text-xl font-semibold text-gray-800 mb-2">
                            Nie znaleziono pytań
                        </h3>
                        <p className="text-gray-600">
                            Spróbuj zmienić kryteria wyszukiwania
                        </p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {questions.map((question) => (
                            <div
                                key={question.id}
                                className="bg-white rounded-lg shadow-md hover:shadow-lg transition"
                            >
                                {/* Question Header */}
                                <div
                                    className="p-6 cursor-pointer"
                                    onClick={() => setExpandedQuestion(
                                        expandedQuestion === question.id ? null : question.id
                                    )}
                                >
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <div className="flex items-center gap-3 mb-2">
                                                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getDifficultyColor(question.difficulty_level)}`}>
                                                    {getDifficultyLabel(question.difficulty_level)} ({question.difficulty_level})
                                                </span>
                                                <span className="text-sm text-gray-500">
                                                    📚 {question.topic}
                                                </span>
                                            </div>
                                            <h3 className="text-lg font-bold text-gray-800">
                                                {question.question_text}
                                            </h3>
                                        </div>

                                        {/* Stats */}
                                        <div className="ml-4 text-right">
                                            {question.stats.total_answers > 0 ? (
                                                <div className="text-sm">
                                                    <div className="font-semibold text-gray-700">
                                                        Odpowiedzi: {question.stats.total_answers}
                                                    </div>
                                                    <div className="flex gap-2 mt-1">
                                                        <span className="text-green-600">
                                                            ✓ {question.stats.correct_answers}
                                                        </span>
                                                        <span className="text-red-600">
                                                            ✗ {question.stats.wrong_answers}
                                                        </span>
                                                    </div>
                                                    <div className="text-blue-600 font-semibold mt-1">
                                                        {question.stats.accuracy}% trafności
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="text-sm text-gray-400">
                                                    Brak odpowiedzi
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Expanded Details */}
                                {expandedQuestion === question.id && (
                                    <div className="border-t border-gray-200 p-6 bg-gray-50">
                                        {/* Answers */}
                                        <div className="mb-6">
                                            <h4 className="font-bold text-gray-700 mb-3">Odpowiedzi:</h4>
                                            <div className="space-y-2">
                                                {/* Correct Answer */}
                                                <div className="p-3 bg-green-100 border-2 border-green-500 rounded-lg">
                                                    <span className="font-bold text-green-700">✓ POPRAWNA:</span>{' '}
                                                    <span className="text-gray-800">{question.correct_answer}</span>
                                                </div>

                                                {/* Wrong Answers */}
                                                {[question.wrong_answer_1, question.wrong_answer_2, question.wrong_answer_3].map((answer, idx) => (
                                                    <div key={idx} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                                                        <span className="font-bold text-red-600">✗ Błędna:</span>{' '}
                                                        <span className="text-gray-700">{answer}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Explanation */}
                                        <div className="p-4 bg-yellow-50 border-l-4 border-yellow-500 rounded-lg">
                                            <h4 className="font-bold text-yellow-800 mb-2">💡 Wyjaśnienie:</h4>
                                            <p className="text-gray-700">{question.explanation}</p>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {/* Pagination */}
                {totalCount > 20 && (
                    <div className="mt-6 flex justify-center gap-4">
                        <button
                            onClick={() => handleFilterChange('page', filters.page - 1)}
                            disabled={filters.page === 1}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
                        >
                            ← Poprzednia
                        </button>

                        <div className="px-4 py-2 bg-gray-200 rounded-lg">
                            Strona {filters.page} z {Math.ceil(totalCount / 20)}
                        </div>

                        <button
                            onClick={() => handleFilterChange('page', filters.page + 1)}
                            disabled={filters.page >= Math.ceil(totalCount / 20)}
                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition"
                        >
                            Następna →
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
