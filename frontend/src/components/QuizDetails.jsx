import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getQuizDetails } from '../services/api';

export default function QuizDetails() {
    const { sessionId } = useParams();
    const [quiz, setQuiz] = useState(null);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        loadQuizDetails();
    }, [sessionId]);

    const loadQuizDetails = async () => {
        try {
            const data = await getQuizDetails(sessionId);
            setQuiz(data);
        } catch (err) {
            console.error('Error loading quiz details:', err);
        } finally {
            setLoading(false);
        }
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
        <div className="min-h-screen bg-gray-100 py-8">
            <div className="max-w-4xl mx-auto px-4">
                {/* Header */}
                <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-800">{quiz.topic}</h1>
                            <p className="text-gray-600 mt-2">
                                {new Date(quiz.completed_at).toLocaleDateString('pl-PL', {
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
                                {quiz.score}/{quiz.total_questions}
                            </p>
                            <p className="text-gray-600">{quiz.accuracy}% dokładności</p>
                        </div>
                    </div>

                    <div className="flex gap-2">
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
                                        key={option}
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