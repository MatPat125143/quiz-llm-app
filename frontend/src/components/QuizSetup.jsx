import { useState } from 'react';
import { startQuiz } from '../services/api';
import { useNavigate } from 'react-router-dom';

export default function QuizSetup() {
    const [topic, setTopic] = useState('');
    const [difficulty, setDifficulty] = useState('medium');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const predefinedTopics = [
        'Programowanie w Python',
        'JavaScript',
        'React',
        'Uczenie maszynowe',
        'Analiza danych',
        'Tworzenie stron internetowych',
        'Algorytmy',
        'Systemy baz danych',
        'Cyberbezpieczeństwo',
        'Chmura obliczeniowa'
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
            const response = await startQuiz(topic, difficulty);
            navigate(`/quiz/play/${response.session_id}`);
        } catch (err) {
            setError('Nie udało się uruchomić quizu. Spróbuj ponownie.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-2xl">
                <div className="text-center mb-8">
                    <h1 className="text-4xl font-bold text-gray-800 mb-2">🎯 Rozpocznij nowy quiz</h1>
                    <p className="text-gray-600">Wybierz temat i poziom trudności</p>
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

                    <div className="mb-8">
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
    );
}