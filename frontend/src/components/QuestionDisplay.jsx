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

    // Funkcja mapująca poziom trudności na etykietę i kolor
    const getDifficultyInfo = (difficulty) => {
        if (difficulty <= 3) {
            return { label: 'Łatwy', color: 'bg-green-100 text-green-800', icon: '🟢' };
        } else if (difficulty <= 6) {
            return { label: 'Średni', color: 'bg-yellow-100 text-yellow-800', icon: '🟡' };
        } else if (difficulty <= 8) {
            return { label: 'Trudny', color: 'bg-red-100 text-red-800', icon: '🔴' };
        } else {
            return { label: 'Expert', color: 'bg-purple-100 text-purple-800', icon: '🟣' };
        }
    };

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
                const newDifficultyInfo = getDifficultyInfo(result.new_difficulty);
                setDifficultyNotification({
                    level: newDifficultyInfo.label,
                    color: newDifficultyInfo.color,
                    icon: newDifficultyInfo.icon,
                    direction: result.new_difficulty > result.previous_difficulty ? 'up' : 'down'
                });
                // Ukryj powiadomienie po 2.5 sekundach
                setTimeout(() => setDifficultyNotification(null), 2500);
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
                                {question.use_adaptive_difficulty && question.current_difficulty && (
                                    <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getDifficultyInfo(question.current_difficulty).color}`}>
                                        {getDifficultyInfo(question.current_difficulty).icon} {getDifficultyInfo(question.current_difficulty).label}
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

                {/* Difficulty Change Modal/Overlay */}
                {difficultyNotification && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-60 backdrop-blur-sm">
                        <div className={`${difficultyNotification.color} rounded-3xl shadow-2xl p-12 max-w-lg mx-4 transform animate-bounce border-4 ${
                            difficultyNotification.direction === 'up' ? 'border-orange-500' : 'border-blue-500'
                        }`}>
                            <div className="text-center">
                                <div className="text-8xl mb-6 animate-pulse">
                                    {difficultyNotification.direction === 'up' ? '📈' : '📉'}
                                </div>
                                <h2 className="text-4xl font-black mb-4">
                                    Poziom trudności
                                </h2>
                                <div className="text-6xl font-black mb-4">
                                    {difficultyNotification.icon} {difficultyNotification.level}
                                </div>
                                <p className="text-lg font-semibold opacity-80">
                                    {difficultyNotification.direction === 'up' ? 'Świetnie Ci idzie!' : 'Nie poddawaj się!'}
                                </p>
                            </div>
                        </div>
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