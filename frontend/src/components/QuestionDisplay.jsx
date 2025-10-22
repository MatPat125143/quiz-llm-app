import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getQuestion, submitAnswer } from '../services/api';

export default function QuestionDisplay() {
    const { sessionId } = useParams();
    const [question, setQuestion] = useState(null);
    const [selectedAnswer, setSelectedAnswer] = useState('');
    const [timeLeft, setTimeLeft] = useState(30);
    const [loading, setLoading] = useState(true);
    const [submitted, setSubmitted] = useState(false);
    const [feedback, setFeedback] = useState(null);
    const [difficultyNotification, setDifficultyNotification] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        loadQuestion();
    }, [sessionId]);

    useEffect(() => {
        if (timeLeft > 0 && !submitted) {
            const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
            return () => clearTimeout(timer);
        } else if (timeLeft === 0 && !submitted) {
            handleSubmit();
        }
    }, [timeLeft, submitted]);

    const loadQuestion = async () => {
        try {
            const data = await getQuestion(sessionId);
            setQuestion(data);
            // Użyj czasu z ustawień sesji lub domyślnie 30 sekund
            setTimeLeft(data.time_per_question || 30);
        } catch (err) {
            console.error('Error loading question:', err);
            if (err.response?.status === 404) {
                navigate(`/quiz/details/${sessionId}`);
            }
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async () => {
        if (submitted) return;

        setSubmitted(true);

        try {
            const timePerQuestion = question.time_per_question || 30;
            const responseTime = timePerQuestion - timeLeft;
            // Convert option letter to actual answer text
            const answerText = selectedAnswer ? question[`option_${selectedAnswer.toLowerCase()}`] : '';
            const result = await submitAnswer(question.question_id, answerText, responseTime);
            setFeedback(result);

            // Pokaż powiadomienie o zmianie poziomu trudności
            if (result.difficulty_changed) {
                const difficultyDirection = result.new_difficulty > result.previous_difficulty ? 'wzrósł' : 'spadł';
                setDifficultyNotification({
                    message: `Poziom trudności ${difficultyDirection}!`,
                    direction: result.new_difficulty > result.previous_difficulty ? 'up' : 'down'
                });
                // Ukryj powiadomienie po 2 sekundach
                setTimeout(() => setDifficultyNotification(null), 2000);
            }

            setTimeout(() => {
                if (result.quiz_completed) {
                    navigate(`/quiz/details/${sessionId}`);
                } else {
                    setSubmitted(false);
                    setSelectedAnswer('');
                    setFeedback(null);
                    loadQuestion();
                }
            }, 3000);
        } catch (err) {
            console.error('Submit error:', err);
            setSubmitted(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100">
                <div className="text-2xl font-semibold text-gray-600">Ładowanie pytania...</div>
            </div>
        );
    }

    if (!question) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100">
                <div className="text-2xl font-semibold text-gray-600">Pytanie nie znalezione</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-500 to-pink-600 p-4">
            <div className="max-w-4xl mx-auto pt-8">
                {/* Header */}
                <div className="bg-white rounded-2xl shadow-2xl p-6 mb-4">
                    <div className="flex justify-between items-center">
                        <div className="flex-1">
                            <p className="text-sm text-gray-600">Pytanie {question.question_number}</p>
                            <div className="flex items-center gap-3 mt-1">
                                <h2 className="text-2xl font-bold text-gray-800">{question.topic}</h2>
                                {question.use_adaptive_difficulty && (
                                    <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full">
                                        Poziom {question.current_difficulty?.toFixed(1)}
                                    </span>
                                )}
                            </div>
                        </div>
                        <div className={`text-4xl font-bold ${
                            timeLeft <= 5 ? 'text-red-600 animate-pulse' : 'text-blue-600'
                        }`}>
                            ⏱️ {timeLeft}s
                        </div>
                    </div>
                </div>

                {/* Question */}
                <div className="bg-white rounded-2xl shadow-2xl p-8 mb-4">
                    <h3 className="text-2xl font-bold text-gray-800 mb-6">{question.question_text}</h3>

                    <div className="space-y-4">
                        {['A', 'B', 'C', 'D'].map((option) => {
                            const optionText = question[`option_${option.toLowerCase()}`];
                            const isSelected = selectedAnswer === option;
                            const isCorrect = feedback && optionText === feedback.correct_answer;
                            const isWrong = feedback && selectedAnswer === option && !feedback.is_correct;

                            return (
                                <button
                                    key={option}
                                    onClick={() => !submitted && setSelectedAnswer(option)}
                                    disabled={submitted}
                                    className={`w-full p-4 rounded-xl text-left font-semibold text-lg transition transform hover:scale-102 ${
                                        isCorrect
                                            ? 'bg-green-500 text-white shadow-lg'
                                            : isWrong
                                            ? 'bg-red-500 text-white shadow-lg'
                                            : isSelected
                                            ? 'bg-blue-500 text-white shadow-lg'
                                            : 'bg-gray-100 hover:bg-gray-200'
                                    }`}
                                >
                                    <span className="font-bold mr-3">{option}.</span>
                                    {optionText}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Difficulty Change Notification */}
                {difficultyNotification && (
                    <div className={`rounded-2xl shadow-2xl p-4 mb-4 ${
                        difficultyNotification.direction === 'up'
                            ? 'bg-orange-100 border-2 border-orange-400'
                            : 'bg-blue-100 border-2 border-blue-400'
                    } animate-pulse`}>
                        <p className={`text-lg font-bold text-center ${
                            difficultyNotification.direction === 'up'
                                ? 'text-orange-800'
                                : 'text-blue-800'
                        }`}>
                            {difficultyNotification.direction === 'up' ? '📈' : '📉'} {difficultyNotification.message}
                        </p>
                    </div>
                )}

                {/* Feedback */}
                {feedback && (
                    <div className={`rounded-2xl shadow-2xl p-6 mb-4 ${
                        feedback.is_correct ? 'bg-green-100' : 'bg-red-100'
                    }`}>
                        <h4 className={`text-2xl font-bold mb-2 ${
                            feedback.is_correct ? 'text-green-800' : 'text-red-800'
                        }`}>
                            {feedback.is_correct ? '✅ Poprawnie!' : '❌ Niepoprawnie'}
                        </h4>
                        <p className="text-gray-800 text-lg">{feedback.explanation}</p>
                        {feedback.current_streak >= 3 && question?.use_adaptive_difficulty && (
                            <div className="mt-3 pt-3 border-t border-gray-300">
                                <p className="text-sm text-gray-700">
                                    🔥 Świetna passa! {feedback.current_streak} poprawnych odpowiedzi z rzędu!
                                </p>
                            </div>
                        )}
                    </div>
                )}

                {/* Submit Button */}
                {!submitted && (
                    <button
                        onClick={handleSubmit}
                        disabled={!selectedAnswer}
                        className="w-full bg-gradient-to-r from-green-500 to-blue-500 text-white py-4 rounded-xl hover:from-green-600 hover:to-blue-600 transition shadow-lg font-bold text-xl disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Zatwierdź odpowiedź
                    </button>
                )}
            </div>
        </div>
    );
}