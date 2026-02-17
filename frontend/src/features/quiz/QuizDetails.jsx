import {useCallback, useEffect, useState} from 'react';
import {useParams, useNavigate, useLocation} from 'react-router-dom';
import {getQuizDetails} from '../../services/api';
import {
    getAdaptiveBadgeClass,
    getDifficultyBadgeClass,
    getDifficultyBadgeLabel,
    getKnowledgeBadgeClass,
    getKnowledgeBadgeLabel,
    formatQuizDuration
} from '../../services/helpers';
import {
    Chart as ChartJS,
    LineElement,
    CategoryScale,
    LinearScale,
    PointElement,
    Tooltip,
    Legend,
    Filler
} from 'chart.js';
import annotationPlugin from 'chartjs-plugin-annotation';
import {Line} from 'react-chartjs-2';
import MainLayout from '../../layouts/MainLayout';
import LatexRenderer from '../../components/LatexRenderer';
import useCurrentUser from '../../hooks/useCurrentUser';
import LoadingState from '../../components/LoadingState';

ChartJS.register(
    LineElement,
    CategoryScale,
    LinearScale,
    PointElement,
    Tooltip,
    Legend,
    Filler,
    annotationPlugin
);

export default function QuizDetails() {
    const {sessionId} = useParams();
    const navigate = useNavigate();
    const location = useLocation();

    const [quiz, setQuiz] = useState(null);
    const { user, loading: userLoading } = useCurrentUser();
    const [loading, setLoading] = useState(true);
    const [isDark, setIsDark] = useState(document.documentElement.dataset.theme === 'dark');


    const fromAdmin = location.state?.fromAdmin === true;

    useEffect(() => {
        const handler = (e) => setIsDark(e.detail === 'dark');
        window.addEventListener('themechange', handler);
        return () => window.removeEventListener('themechange', handler);
    }, []);

    const loadData = useCallback(async () => {
        try {
            const quizData = await getQuizDetails(sessionId);
            setQuiz(quizData);
        } catch (err) {
            console.error('Error loading quiz details:', err);
        } finally {
            setLoading(false);
        }
    }, [sessionId]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    if (loading || userLoading) {
        return <LoadingState message="Ładowanie szczegółów quizu..." fullScreen={true} />;
    }

    if (!quiz || !quiz.session) {
        return (
            <MainLayout user={user}>
                <div className="min-h-[60vh] flex flex-col items-center justify-center">
                    <div className="text-6xl mb-4">❌</div>
                    <h2 className="text-2xl font-bold text-gray-800 mb-4">Quiz nie znaleziony</h2>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition"
                    >
                        ← Powrót do panelu
                    </button>
                </div>
            </MainLayout>
        );
    }

    const session = quiz.session;
    const replayParams = {
        topic: session.topic || '',
        subtopic: session.subtopic || '',
        difficulty: session.difficulty || 'medium',
        questionsCount: session.questions_count ?? 10,
        timePerQuestion: session.time_per_question ?? 30,
        useAdaptiveDifficulty: session.use_adaptive_difficulty ?? true,
        knowledgeLevel: session.knowledge_level || 'high_school'
    };

    const difficultyData = quiz.difficulty_progress || [];
    const yAxisMaxDifficulty = 10;

    const chartData = {
        labels: difficultyData.map((_, i) => `Pytanie ${i + 1}`),
        datasets: [
            {
                label: 'Poziom trudności',
                data: difficultyData.map((d) => d.difficulty),
                borderColor: isDark ? 'rgba(56, 189, 248, 1)' : 'rgba(37, 99, 235, 1)',
                backgroundColor: isDark ? 'rgba(56, 189, 248, 0.22)' : 'rgba(37, 99, 235, 0.18)',
                tension: 0.3,
                fill: false,
                clip: false,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointBorderWidth: 2,
                pointBorderColor: isDark ? '#0f172a' : '#ffffff',
                pointBackgroundColor: isDark ? '#22d3ee' : '#2563eb'
            }
        ]
    };

    const getDifficultyKeyFromValue = (value) => {
        const num = Number(value);
        if (!Number.isFinite(num)) return null;
        if (num <= 4) return 'easy';
        if (num <= 7) return 'medium';
        return 'hard';
    };

    const chartOptions = {
        responsive: true,
        layout: {padding: {top: 12}},
        scales: {
            y: {
                min: 0,
                max: yAxisMaxDifficulty,
                ticks: {
                    color: isDark ? '#c7d2fe' : '#334155',
                    stepSize: 1
                },
                grid: {color: isDark ? 'rgba(148,163,184,0.26)' : 'rgba(148,163,184,0.28)'}
            },
            x: {
                ticks: {color: isDark ? '#c7d2fe' : '#334155'},
                grid: {color: isDark ? 'rgba(148,163,184,0.2)' : 'rgba(148,163,184,0.2)'}
            }
        },
        plugins: {
            legend: {display: false},
            tooltip: {
                backgroundColor: isDark ? '#1f2937' : '#4f46e5',
                titleColor: '#fff',
                bodyColor: '#fff'
            },
            annotation: {
                annotations: {
                    easyZone: {
                        type: 'box',
                        yMin: 0,
                        yMax: 3.33,
                        backgroundColor: isDark ? 'rgba(34,197,94,0.2)' : 'rgba(34,197,94,0.12)',
                        borderWidth: 0,
                        label: {
                            content: '🟢 Łatwy (0–3.3)',
                            enabled: true,
                            position: 'end',
                            color: isDark ? '#bbf7d0' : '#16a34a',
                            font: {weight: 'bold'}
                        }
                    },
                    mediumZone: {
                        type: 'box',
                        yMin: 3.33,
                        yMax: 6.66,
                        backgroundColor: isDark ? 'rgba(250,204,21,0.22)' : 'rgba(250,204,21,0.12)',
                        borderWidth: 0,
                        label: {
                            content: '🟡 Średni (3.3–6.6)',
                            enabled: true,
                            position: 'end',
                            color: isDark ? '#fde68a' : '#ca8a04',
                            font: {weight: 'bold'}
                        }
                    },
                    hardZone: {
                        type: 'box',
                        yMin: 6.66,
                        yMax: 10,
                        backgroundColor: isDark ? 'rgba(239,68,68,0.2)' : 'rgba(239,68,68,0.12)',
                        borderWidth: 0,
                        label: {
                            content: '🔴 Trudny (6.6–10)',
                            enabled: true,
                            position: 'end',
                            color: isDark ? '#fecaca' : '#dc2626',
                            font: {weight: 'bold'}
                        }
                    }
                }
            }
        }
    };

    const quizDurationLabel = formatQuizDuration(
        session.started_at,
        session.ended_at || session.completed_at,
        session.total_questions,
        session.time_per_question,
        session.total_response_time
    );

    const averageResponseTime = quiz.answers && quiz.answers.length > 0
        ? Math.round(quiz.answers.reduce((sum, ans) => sum + (ans.response_time || 0), 0) / quiz.answers.length)
        : 0;

    const formatTime = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = Math.max(0, seconds % 60);
        return `${mins} min ${secs} sek`;
    };

    return (
        <MainLayout user={user}>
            <div className="max-w-6xl mx-auto px-3 sm:px-6 py-6 sm:py-10">
                <div
                    className="bg-white dark:bg-slate-900 rounded-2xl p-4 sm:p-8 shadow-lg border border-gray-100 dark:border-slate-800 mb-8 sm:mb-10">
                    <div className="flex flex-col sm:flex-row sm:justify-between gap-4 sm:gap-6">
                        <div>
                            <h1 className="text-2xl sm:text-3xl font-bold text-gray-800 flex flex-wrap items-center gap-2">
                                📋 {session.topic}
                                {session.subtopic && (
                                    <span className="block sm:inline text-lg sm:text-2xl font-semibold text-indigo-600">
                    → {session.subtopic}
                  </span>
                                )}
                            </h1>
                            {fromAdmin && session.user_info && (
                                <p className="text-gray-600 mt-2 flex flex-wrap items-center gap-2 text-sm sm:text-base">
                                    <span className="font-semibold">👤 Użytkownik:</span>
                                    <span className="text-indigo-600 font-semibold">{session.user_info.username}</span>
                                    <span className="text-gray-500">({session.user_info.email})</span>
                                </p>
                            )}
                            <p className="text-gray-600 mt-2 text-sm sm:text-base">
                                {new Date(session.ended_at || session.completed_at).toLocaleString('pl-PL', {
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                })}
                            </p>
                        </div>

                        <div className="text-left sm:text-right">
                            <p className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                                {session.correct_answers}/{session.total_questions}
                            </p>
                            <p className="text-gray-600 font-medium text-sm sm:text-base">Skuteczność: {session.accuracy}%</p>
                        </div>
                    </div>

                    <div className="flex flex-wrap gap-2 sm:gap-3 mt-4">
            <span
                className={`px-3 sm:px-4 py-1.5 rounded-full text-xs sm:text-sm font-semibold ${getDifficultyBadgeClass(session.difficulty)}`}>
              {getDifficultyBadgeLabel(session.difficulty)}
            </span>

                        {session.knowledge_level && (
                            <span
                                className={`px-3 sm:px-4 py-1.5 rounded-full text-xs sm:text-sm font-semibold ${getKnowledgeBadgeClass()}`}>
                {getKnowledgeBadgeLabel(session.knowledge_level)}
              </span>
                        )}

                        {session.use_adaptive_difficulty && (
                            <span
                                className={`px-3 sm:px-4 py-1.5 rounded-full text-xs sm:text-sm font-semibold ${getAdaptiveBadgeClass()}`}>
                🎯 Tryb adaptacyjny
              </span>
                        )}
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4 mt-5 sm:mt-6">
                        <div
                            className="bg-gradient-to-br from-indigo-50 to-purple-50 dark:bg-slate-900 dark:bg-none rounded-xl p-3 sm:p-4 border border-indigo-100 dark:border-slate-800">
                            <p className="text-sm text-gray-600 mb-1">⏱️ Całkowity czas quizu</p>
                            <p className="text-xl sm:text-2xl font-bold text-indigo-600 dark:text-indigo-300">{quizDurationLabel}</p>
                        </div>
                        <div
                            className="bg-gradient-to-br from-green-50 to-emerald-50 dark:bg-slate-900 dark:bg-none rounded-xl p-3 sm:p-4 border border-green-100 dark:border-slate-800">
                            <p className="text-sm text-gray-600 mb-1">⚡ Średni czas odpowiedzi</p>
                            <p className="text-xl sm:text-2xl font-bold text-green-600 dark:text-green-300">{formatTime(averageResponseTime)}</p>
                        </div>
                    </div>
                </div>

                {session.use_adaptive_difficulty && difficultyData.length > 0 && (
                    <div
                        className="bg-white dark:bg-slate-900 rounded-2xl p-4 sm:p-6 mb-8 sm:mb-10 shadow-lg border border-gray-100 dark:border-slate-800">
                        <h3 className="text-lg sm:text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
                            📈 Progres trudności w trakcie quizu
                        </h3>
                        <Line data={chartData} options={chartOptions} height={100}/>
                    </div>
                )}

                <div className="space-y-4 sm:space-y-6">
                    {(quiz.answers || []).map((question, index) => {
                        const answers = [
                            {key: 'A', text: question.correct_answer},
                            {key: 'B', text: question.wrong_answer_1},
                            {key: 'C', text: question.wrong_answer_2},
                            {key: 'D', text: question.wrong_answer_3}
                        ];

                        return (
                            <div
                                key={index}
                                className="bg-white dark:bg-slate-900 rounded-2xl shadow-md border border-gray-100 dark:border-slate-800 p-4 sm:p-6"
                            >
                                <div className="flex flex-wrap justify-between items-start gap-3 mb-4">
                                    <div>
                                        <h3 className="text-base sm:text-lg font-bold text-gray-800">
                                            Pytanie {index + 1} z {session.total_questions}
                                        </h3>
                                        <p className="text-xs sm:text-sm text-gray-500 mt-1">
                                            ⏱️ Czas odpowiedzi: <span
                                            className="font-semibold text-indigo-600">{formatTime(question.response_time || 0)}</span>
                                        </p>
                                    </div>
                                    <div className="flex flex-col items-start gap-2 self-start">
                                        {question.is_correct ? (
                                            <span
                                                className="px-3 sm:px-4 py-1 bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-200 rounded-full font-semibold text-sm">
                        ✅ Poprawnie
                      </span>
                                        ) : (
                                            <span
                                                className="px-3 sm:px-4 py-1 bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-200 rounded-full font-semibold text-sm">
                        ❌ Niepoprawnie
                      </span>
                                        )}
                                        {getDifficultyKeyFromValue(question.difficulty_at_answer) && (
                                            <span
                                                className={`px-3 sm:px-4 py-1 rounded-full text-xs sm:text-sm font-semibold ${getDifficultyBadgeClass(getDifficultyKeyFromValue(question.difficulty_at_answer))}`}>
                        {getDifficultyBadgeLabel(getDifficultyKeyFromValue(question.difficulty_at_answer))}
                      </span>
                                        )}
                                    </div>
                                </div>

                                <LatexRenderer text={question.question_text}
                                               className="text-gray-800 font-medium mb-4 text-sm sm:text-base"/>

                                <div className="space-y-2">
                                    {answers.map(({key, text}) => {
                                        const isCorrect = question.correct_answer === text;
                                        const isSelected = question.selected_answer === text;
                                        const wrongSelected = isSelected && !isCorrect;

                                        return (
                                            <div
                                                key={key}
                                                className={`p-3 rounded-xl border-2 transition-all ${
                                                    isCorrect
                                                        ? 'bg-green-50 border-green-400 dark:bg-green-900/30 dark:border-green-700'
                                                        : wrongSelected
                                                            ? 'bg-red-50 border-red-400 dark:bg-red-900/30 dark:border-red-700'
                                                            : 'bg-gray-50 border-gray-200 dark:bg-slate-900 dark:border-slate-700'
                                                }`}
                                            >
                                                <span
                                                    className="font-bold text-indigo-600 dark:text-indigo-300 mr-2 text-sm sm:text-base">{key}.</span>
                                                <LatexRenderer text={text}
                                                               className="inline text-gray-800 dark:text-slate-100 break-words text-sm sm:text-base"
                                                               inline={true}/>
                                                {isCorrect && isSelected && (
                                                    <span
                                                        className="ml-0 sm:ml-3 mt-1 sm:mt-0 px-2 py-0.5 rounded-lg text-xs bg-green-600 text-white font-semibold inline-block">
                            ✅ Twoja odpowiedź
                          </span>
                                                )}
                                                {isCorrect && !isSelected && (
                                                    <span
                                                        className="ml-0 sm:ml-3 mt-1 sm:mt-0 px-2 py-0.5 rounded-lg text-xs bg-green-600 text-white font-semibold inline-block">
                            ✅ Poprawna
                          </span>
                                                )}
                                                {wrongSelected && (
                                                    <span
                                                        className="ml-0 sm:ml-3 mt-1 sm:mt-0 px-2 py-0.5 rounded-lg text-xs bg-red-600 text-white font-semibold inline-block">
                            ❌ Twoja odpowiedź
                          </span>
                                                )}
                                            </div>
                                        );
                                    })}
                                </div>

                                {question.explanation && (
                                    <div
                                        className="mt-4 p-3 sm:p-4 bg-blue-50 dark:bg-slate-900 border-l-4 border-blue-400 dark:border-blue-500 rounded-lg">
                                        <p className="font-semibold text-blue-800 dark:text-blue-200">💡 Wyjaśnienie:</p>
                                        <LatexRenderer text={question.explanation}
                                                       className="text-gray-700 dark:text-slate-200 mt-1 text-sm sm:text-base"/>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>

                <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mt-8 sm:mt-10">

                    {fromAdmin && (
                        <button
                            onClick={() => navigate('/admin')}
                            className="flex-1 px-6 py-3 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition font-semibold"
                        >
                            👑 Panel Admina
                        </button>
                    )}
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="flex-1 px-6 py-3 rounded-xl font-semibold transition-colors bg-indigo-600 text-white hover:bg-indigo-700 dark:bg-indigo-700 dark:hover:bg-indigo-600 dark:text-white"
                    >
                        ← Powrót do panelu
                    </button>
                    <button
                        onClick={() => navigate('/quiz/setup', {state: {replayParams}})}
                        className="flex-1 px-6 py-3 rounded-xl font-semibold transition-colors bg-green-600 text-white hover:bg-green-700 dark:bg-emerald-700 dark:hover:bg-emerald-600 dark:text-white"
                    >
                        🔄 Spróbuj ponownie
                    </button>
                </div>
            </div>
        </MainLayout>
    );
}

