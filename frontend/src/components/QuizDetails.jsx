import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getQuizDetails, getCurrentUser, logout } from '../services/api';

export default function QuizDetails() {
    const { sessionId } = useParams();
    const [quiz, setQuiz] = useState(null);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        loadData();
    }, [sessionId]);

    const loadData = async () => {
        try {
            const [quizData, userData] = await Promise.all([
                getQuizDetails(sessionId),
                getCurrentUser()
            ]);
            setQuiz(quizData);
            setUser(userData);
        } catch (err) {
            console.error('Error loading data:', err);
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

    if (!quiz) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100">
                <div className="text-center">
                    <div className="text-6xl mb-4">❌</div>
                    <h2 className="text-2xl font-bold text-gray-800 mb-4">Quiz nie znaleziony</h2>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition font-semibold"
                    >
                        ← Powrót do panelu
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-100">
            {/* Header */}
            <header className="bg-white shadow-md">
                <div className="max-w-7xl mx-auto px-4 py-6 flex justify-between items-center">
                    <h1 className="text-3xl font-bold text-blue-600">📋 Szczegóły Quizu</h1>
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
                {/* Quiz Info Card */}
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">{quiz.topic}</h1>
                            <p className="text-gray-600 mt-2">
                                {new Date(quiz.ended_at || quiz.completed_at).toLocaleDateString('pl-PL', {
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                })}
                            </p>
                        </div>
                        <div className="text-right">
                            <p className="text-4xl font-bold text-blue-600">
                                {quiz.correct_answers}/{quiz.total_questions}
                            </p>
                            <p className="text-gray-600">{quiz.accuracy}% dokładności</p>
                        </div>
                    </div>

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
                        {quiz.use_adaptive_difficulty && (
                            <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
                                📊 Początkowy: {quiz.initial_difficulty_value?.toFixed(1) || 'N/A'} → Końcowy: {quiz.current_difficulty?.toFixed(1) || 'N/A'}
                            </span>
                        )}
                    </div>
                </div>

                {/* Questions */}
                {quiz.questions && quiz.questions.map((question, index) => (
                    <div key={question.id} className="bg-white rounded-xl shadow-lg p-6 mb-4">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-xl font-bold text-gray-800">
                                Pytanie {index + 1} z {quiz.total_questions}
                            </h3>
                            {question.is_correct ? (
                                <span className="px-4 py-2 bg-green-100 text-green-800 rounded-lg font-bold">
                                    ✅ Poprawnie
                                </span>
                            ) : (
                                <span className="px-4 py-2 bg-red-100 text-red-800 rounded-lg font-bold">
                                    ❌ Niepoprawnie
                                </span>
                            )}
                        </div>

                        <p className="text-lg text-gray-800 mb-4 font-semibold">{question.question_text}</p>

                        <div className="space-y-3 mb-4">
                            {['A', 'B', 'C', 'D'].map((option) => {
                                const optionText = question[`option_${option.toLowerCase()}`];
                                const isCorrect = question.correct_answer === option;
                                const isSelected = question.selected_answer === option;
                                const wasWrong = isSelected && !isCorrect;

                                return (
                                    <div
                                        key={`${question.id}-${option}`}
                                        className={`p-4 rounded-lg border-2 transition ${
                                            isCorrect
                                                ? 'bg-green-100 border-green-500'
                                                : wasWrong
                                                ? 'bg-red-100 border-red-500'
                                                : 'bg-gray-50 border-gray-300'
                                        }`}
                                    >
                                        <div className="flex items-start gap-3">
                                            <span className="font-bold text-lg">{option}.</span>
                                            <span className="flex-1">{optionText}</span>
                                            <div className="flex flex-col gap-1 items-end">
                                                {isCorrect && (
                                                    <span className="px-2 py-1 bg-green-600 text-white rounded text-sm font-semibold whitespace-nowrap">
                                                        ✅ Poprawna odpowiedź
                                                    </span>
                                                )}
                                                {isSelected && !isCorrect && (
                                                    <span className="px-2 py-1 bg-red-600 text-white rounded text-sm font-semibold whitespace-nowrap">
                                                        ❌ Twoja odpowiedź
                                                    </span>
                                                )}
                                                {isSelected && isCorrect && (
                                                    <span className="px-2 py-1 bg-green-600 text-white rounded text-sm font-semibold whitespace-nowrap">
                                                        ✅ Twoja odpowiedź
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Explanation */}
                        <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                            <p className="font-semibold text-blue-800 mb-1">💡 Wyjaśnienie:</p>
                            <p className="text-gray-800">{question.explanation}</p>
                        </div>
                    </div>
                ))}

                {/* Buttons */}
                <div className="flex gap-4">
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="flex-1 bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 transition font-semibold"
                    >
                        ← Powrót do panelu
                    </button>
                    <button
                        onClick={() => navigate('/quiz/setup')}
                        className="flex-1 bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition font-semibold"
                    >
                        🔄 Spróbuj ponownie
                    </button>
                </div>
            </div>
        </div>
    );
}