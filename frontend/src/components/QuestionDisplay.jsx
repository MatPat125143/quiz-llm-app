import { useState, useEffect, useRef } from 'react';
import { getQuestion, submitAnswer, endQuiz } from '../services/api';
import { useParams, useNavigate } from 'react-router-dom';

export default function QuestionDisplay() {
    const { sessionId } = useParams();
    const navigate = useNavigate();

    const [question, setQuestion] = useState(null);
    const [selectedAnswer, setSelectedAnswer] = useState(null);
    const [answered, setAnswered] = useState(false);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(true);
    const [timeLeft, setTimeLeft] = useState(30);
    const [startTime, setStartTime] = useState(null);
    const [error, setError] = useState('');

    // Prevent duplicate loading in React StrictMode
    const loadedRef = useRef(false);

    // Timer
    useEffect(() => {
        if (!answered && timeLeft > 0) {
            const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
            return () => clearTimeout(timer);
        } else if (timeLeft === 0 && !answered) {
            handleAutoSubmit();
        }
    }, [timeLeft, answered]);

    // Load first question (only once, prevent React StrictMode duplicate)
    useEffect(() => {
        if (!loadedRef.current) {
            loadedRef.current = true;
            loadQuestion();
        }
    }, []);

    const loadQuestion = async () => {
        try {
            setLoading(true);
            setError('');

            const data = await getQuestion(sessionId);

            setQuestion(data);
            setTimeLeft(data.time_per_question || 30);
            setStartTime(Date.now());
            setAnswered(false);
            setSelectedAnswer(null);
            setResult(null);

            // Debug info - sprawdź czy pytanie było z cache czy wygenerowane
            if (data.generation_status === 'cached') {
                console.log('⚡ Pytanie pobrane z cache (instant!)');
            } else {
                console.log(`⏳ Pytanie wygenerowane: ${data.generation_status}`);
            }

        } catch (err) {
            console.error('Error loading question:', err);

            if (err.response?.status === 404) {
                // Quiz zakończony - przekieruj do szczegółów
                navigate(`/quiz/details/${sessionId}`);
            } else {
                setError('Nie udało się załadować pytania. Spróbuj ponownie.');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleAutoSubmit = async () => {
        if (!answered) {
            await handleSubmit(null); // Auto-submit bez odpowiedzi
        }
    };

    const handleSubmit = async (answer) => {
        if (answered) return;

        const responseTime = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;
        const answerToSubmit = answer || selectedAnswer;

        // Jeśli brak odpowiedzi (timeout), wyślij pustą odpowiedź
        if (!answerToSubmit) {
            console.log('⏰ Timeout - brak odpowiedzi');
        }

        try {
            setAnswered(true);

            const data = await submitAnswer(
                question.question_id,
                answerToSubmit || '', // Wyślij pusty string jeśli brak odpowiedzi
                responseTime
            );

            setResult(data);

            // Nie automatycznie - użytkownik musi kliknąć "Następne pytanie"
            // Jeśli quiz zakończony, automatycznie przekieruj po 3 sekundach
            if (data.quiz_completed) {
                setTimeout(() => {
                    navigate(`/quiz/details/${sessionId}`);
                }, 3000);
            }
        } catch (err) {
            console.error('Error submitting answer:', err);
            setError('Nie udało się zapisać odpowiedzi. Spróbuj ponownie.');
            setAnswered(false);
        }
    };

    const handleNextQuestion = () => {
        if (loading) return;

        // Resetuj stan i pokaż loader podczas generowania kolejnego pytania
        setAnswered(false);
        setSelectedAnswer(null);
        setResult(null);
        setQuestion(null);
        setLoading(true);
        loadQuestion();
    };


    // Loading state - pierwsze ładowanie
    if (loading && !question) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600">
                <div className="bg-white p-12 rounded-2xl shadow-2xl text-center max-w-md">
                    <div className="animate-spin rounded-full h-20 w-20 border-b-4 border-blue-600 mx-auto mb-6"></div>
                    <h2 className="text-2xl font-bold text-gray-800 mb-3">
                        🤖 Generuję pytanie...
                    </h2>
                    <p className="text-gray-600">
                        ChatGPT przygotowuje dla Ciebie spersonalizowane pytanie
                    </p>
                    <div className="mt-6 space-y-2">
                        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                            <span>Analizuję temat...</span>
                        </div>
                        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                            <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse delay-100"></div>
                            <span>Tworzę pytanie...</span>
                        </div>
                        <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
                            <div className="w-2 h-2 bg-pink-500 rounded-full animate-pulse delay-200"></div>
                            <span>Przygotowuję odpowiedzi...</span>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    if (error && !question) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-100">
                <div className="bg-white p-8 rounded-2xl shadow-xl text-center max-w-md">
                    <div className="text-6xl mb-4">⚠️</div>
                    <h2 className="text-2xl font-bold text-gray-800 mb-4">Ups! Coś poszło nie tak</h2>
                    <p className="text-gray-600 mb-6">{error}</p>
                    <button
                        onClick={() => navigate('/quiz')}
                        className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition"
                    >
                        Powrót do menu
                    </button>
                </div>
            </div>
        );
    }

    if (!question) return null;

    const normalizedDifficultyLabel = question.difficulty_label
        ? question.difficulty_label.charAt(0).toUpperCase() + question.difficulty_label.slice(1)
        : '';
    const remainingAfterCurrent = Math.max((question.questions_remaining ?? 0) - 1, 0);

    const getOptionColor = (option) => {
        // WAŻNE: Sprawdź czy result istnieje, żeby uniknąć błędu
        if (!answered || !result) {
            return selectedAnswer === option
                ? 'bg-blue-100 border-blue-500 border-2'
                : 'bg-white hover:bg-gray-50';
        }

        if (option === result.correct_answer) {
            return 'bg-green-100 border-green-500 border-2';
        }
        if (selectedAnswer === option && !result.is_correct) {
            return 'bg-red-100 border-red-500 border-2';
        }
        return 'bg-gray-50';
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-4">
            <div className="max-w-4xl mx-auto py-8">
                {/* Header */}
                <div className="bg-white rounded-t-2xl p-6 shadow-lg">
                    <div className="flex justify-between items-center mb-4">
                        <div>
                            <h2 className="text-2xl font-bold text-gray-800">
                                📚 {question.topic}
                            </h2>
                            <p className="text-gray-600">
                                Pytanie {question.question_number} z {question.questions_count || 10}
                            </p>
                            <p className="text-sm text-gray-500">
                                Pozostało {remainingAfterCurrent} pytań po tym pytaniu
                            </p>
                        </div>

                        {/* Timer */}
                        <div className={`text-4xl font-bold ${
                            timeLeft <= 5 ? 'text-red-600 animate-pulse' :
                            timeLeft <= 10 ? 'text-yellow-600' :
                            'text-green-600'
                        }`}>
                            ⏱️ {timeLeft}s
                        </div>
                    </div>

                    {/* Difficulty indicator */}
                    {question.use_adaptive_difficulty && question.current_difficulty ? (
                        <div className="flex items-center gap-2">
                            <span className="text-sm text-gray-600">Poziom trudności:</span>
                            <span className={`px-3 py-1 text-sm font-semibold rounded-full ${
                                question.current_difficulty <= 3.5 ? 'bg-green-100 text-green-800' :
                                question.current_difficulty <= 7 ? 'bg-yellow-100 text-yellow-800' :
                                'bg-red-100 text-red-800'
                            }`}>
                                {normalizedDifficultyLabel ? `🎯 ${normalizedDifficultyLabel}` : '🎯'}
                                {question.current_difficulty ? ` (${question.current_difficulty.toFixed(1)})` : ''}
                            </span>
                        </div>
                    ) : (
                        question.difficulty_label && (
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-gray-600">Poziom trudności:</span>
                                <span className="px-3 py-1 text-sm font-semibold rounded-full bg-blue-100 text-blue-800">
                                    🎯 {normalizedDifficultyLabel}
                                </span>
                            </div>
                        )
                    )}

                    {/* Stats */}
                    {result && (
                        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                            <div className="flex gap-4 text-sm">
                                <span className="flex items-center gap-2">
                                    <span className="text-2xl">🎯</span>
                                    <span className="font-semibold">{result.session_stats.correct_answers}/{result.session_stats.total_questions}</span>
                                </span>
                                <span className="flex items-center gap-2">
                                    <span className="text-2xl">📊</span>
                                    <span className="font-semibold">{result.session_stats.accuracy.toFixed(1)}%</span>
                                </span>
                                <span className="flex items-center gap-2">
                                    <span className="text-2xl">🔥</span>
                                    <span className="font-semibold">Seria: {result.current_streak}</span>
                                </span>
                            </div>
                        </div>
                    )}
                </div>

                {/* Question */}
                <div className="bg-white p-8 shadow-lg">
                    <h3 className="text-2xl font-bold text-gray-800 mb-6">
                        {question.question_text}
                    </h3>

                    {/* Answers */}
                    <div className="space-y-3">
                        {['A', 'B', 'C', 'D'].map((letter) => {
                            const option = question[`option_${letter.toLowerCase()}`];
                            return (
                                <button
                                    key={letter}
                                    onClick={() => !answered && setSelectedAnswer(option)}
                                    disabled={answered}
                                    className={`w-full text-left p-4 rounded-lg transition ${
                                        getOptionColor(option)
                                    } ${!answered ? 'cursor-pointer' : 'cursor-default'}`}
                                >
                                    <span className="font-bold text-lg">{letter}.</span> {option}
                                </button>
                            );
                        })}
                    </div>

                    {/* Submit button */}
                    {!answered && (
                        <button
                            onClick={() => handleSubmit(selectedAnswer)}
                            disabled={!selectedAnswer}
                            className="w-full mt-6 bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 rounded-lg font-bold text-lg hover:from-blue-700 hover:to-purple-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            Zatwierdź odpowiedź
                        </button>
                    )}
                </div>

                {/* Result panel */}
                {answered && result && (
                    <div className={`p-6 shadow-lg ${
                        result.is_correct ? 'bg-green-50' : 'bg-red-50'
                    }`}>
                        <div className="text-center mb-4">
                            <div className="text-6xl mb-2">
                                {result.is_correct ? '✅' : '❌'}
                            </div>
                            <h3 className="text-3xl font-bold mb-2">
                                {result.is_correct ? 'Brawo! Poprawna odpowiedź!' : 'Niestety, niepoprawna odpowiedź'}
                            </h3>
                            {!result.is_correct && (
                                <p className="text-lg text-gray-700">
                                    Poprawna odpowiedź: <strong>{result.correct_answer}</strong>
                                </p>
                            )}
                        </div>

                        {/* Explanation */}
                        <div className="bg-white p-4 rounded-lg mb-4">
                            <h4 className="font-bold text-lg mb-2">💡 Wyjaśnienie:</h4>
                            <p className="text-gray-700">{result.explanation}</p>
                        </div>

                        {/* Difficulty change notification */}
                        {result.difficulty_changed && (
                            <div className="bg-blue-50 border border-blue-300 p-4 rounded-lg mb-4">
                                <p className="text-blue-800 font-semibold">
                                    🎯 Poziom trudności {result.new_difficulty > result.previous_difficulty ? 'zwiększony' : 'zmniejszony'}!
                                </p>
                                <p className="text-sm text-blue-600">
                                    {result.previous_difficulty.toFixed(1)} → {result.new_difficulty.toFixed(1)}
                                </p>
                            </div>
                        )}

                        {/* Next question button */}
                        {!result.quiz_completed ? (
                            <div className="text-center mt-4">
                                <button
                                    onClick={handleNextQuestion}
                                    disabled={loading}
                                    className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-lg font-bold text-lg hover:from-blue-700 hover:to-purple-700 transition shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {loading ? '🤖 Generuję pytanie...' : 'Następne pytanie →'}
                                </button>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                <p className="text-center text-xl font-bold text-gray-800">
                                    🎉 Quiz zakończony!
                                </p>
                                <p className="text-center text-gray-600">
                                    Przekierowanie do wyników za chwilę...
                                </p>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
