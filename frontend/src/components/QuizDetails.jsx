import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getQuizDetails, getCurrentUser, logout } from '../services/api';
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
import { Line } from 'react-chartjs-2';
import Layout from './Layout';

// ✅ Rejestracja wszystkich wymaganych elementów Chart.js
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
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [quiz, setQuiz] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

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
      console.error('Error loading quiz details:', err);
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
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 via-purple-50 to-blue-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-700 font-semibold text-lg">Ładowanie szczegółów quizu...</p>
        </div>
      </div>
    );
  }

  if (!quiz || !quiz.session) {
    return (
      <Layout user={user}>
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
      </Layout>
    );
  }

  const session = quiz.session;

  // 🔹 Dane do wykresu adaptacyjnego
  const difficultyData = quiz.difficulty_progress || [];
  const chartData = {
    labels: difficultyData.map((_, i) => `Pytanie ${i + 1}`),
    datasets: [
      {
        label: 'Poziom trudności',
        data: difficultyData.map((d) => d.difficulty),
        borderColor: 'rgba(79, 70, 229, 0.9)',
        backgroundColor: 'rgba(79, 70, 229, 0.15)',
        tension: 0.3,
        fill: false, // ⛔ brak wypełnienia pod linią
        pointRadius: 5,
        pointBackgroundColor: '#4f46e5'
      }
    ]
  };

  // 🔸 Trzy poziomy trudności: łatwy / średni / trudny
  const chartOptions = {
    responsive: true,
    scales: {
      y: {
        min: 0,
        max: 10,
        ticks: {
          color: '#4b5563',
          stepSize: 1
        },
        grid: { color: 'rgba(0,0,0,0.05)' }
      },
      x: {
        ticks: { color: '#4b5563' },
        grid: { color: 'rgba(0,0,0,0.05)' }
      }
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: '#4f46e5',
        titleColor: '#fff',
        bodyColor: '#fff'
      },
      annotation: {
        annotations: {
          easyZone: {
            type: 'box',
            yMin: 0,
            yMax: 3.33,
            backgroundColor: 'rgba(34,197,94,0.07)',
            borderWidth: 0,
            label: {
              content: '🟢 Łatwy (0–3.3)',
              enabled: true,
              position: 'end',
              color: '#16a34a',
              font: { weight: 'bold' }
            }
          },
          mediumZone: {
            type: 'box',
            yMin: 3.33,
            yMax: 6.66,
            backgroundColor: 'rgba(250,204,21,0.07)',
            borderWidth: 0,
            label: {
              content: '🟡 Średni (3.3–6.6)',
              enabled: true,
              position: 'end',
              color: '#ca8a04',
              font: { weight: 'bold' }
            }
          },
          hardZone: {
            type: 'box',
            yMin: 6.66,
            yMax: 10,
            backgroundColor: 'rgba(239,68,68,0.07)',
            borderWidth: 0,
            label: {
              content: '🔴 Trudny (6.6–10)',
              enabled: true,
              position: 'end',
              color: '#dc2626',
              font: { weight: 'bold' }
            }
          }
        }
      }
    }
  };

  return (
    <Layout user={user}>
      <div className="max-w-6xl mx-auto px-6 py-10">
        {/* Nagłówek */}
        <div className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 mb-10">
          <div className="flex justify-between flex-wrap gap-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-2">
                📋 {session.topic}
              </h1>
              <p className="text-gray-600 mt-2">
                {new Date(session.ended_at || session.completed_at).toLocaleString('pl-PL', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </p>
            </div>

            <div className="text-right">
              <p className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                {session.correct_answers}/{session.total_questions}
              </p>
              <p className="text-gray-600 font-medium">Skuteczność: {session.accuracy}%</p>
            </div>
          </div>

          {/* Tagi */}
          <div className="flex flex-wrap gap-3 mt-4">
            <span
              className={`px-4 py-1.5 rounded-full text-sm font-semibold ${
                session.difficulty === 'easy'
                  ? 'bg-green-100 text-green-800'
                  : session.difficulty === 'medium'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-red-100 text-red-800'
              }`}
            >
              {session.difficulty === 'easy' && '🟢 Łatwy'}
              {session.difficulty === 'medium' && '🟡 Średni'}
              {session.difficulty === 'hard' && '🔴 Trudny'}
            </span>

            {session.use_adaptive_difficulty && (
              <span className="px-4 py-1.5 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
                🎯 Adaptacyjny quiz
              </span>
            )}
          </div>
        </div>

        {/* 🔹 Wykres trudności (tylko dla adaptacyjnych) */}
        {session.use_adaptive_difficulty && difficultyData.length > 0 && (
          <div className="bg-white rounded-2xl p-6 mb-10 shadow-lg border border-gray-100">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
              📈 Progres trudności w trakcie quizu
            </h3>
            <Line data={chartData} options={chartOptions} height={100} />
          </div>
        )}

        {/* 🔹 Lista pytań i przyciski zostają bez zmian */}
        <div className="space-y-6">
          {quiz.answers.map((question, index) => {
            const answers = [
              { key: 'A', text: question.correct_answer },
              { key: 'B', text: question.wrong_answer_1 },
              { key: 'C', text: question.wrong_answer_2 },
              { key: 'D', text: question.wrong_answer_3 }
            ];

            return (
              <div
                key={index}
                className="bg-white rounded-2xl shadow-md border border-gray-100 p-6"
              >
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-bold text-gray-800">
                    Pytanie {index + 1} z {session.total_questions}
                  </h3>
                  {question.is_correct ? (
                    <span className="px-4 py-1 bg-green-100 text-green-700 rounded-full font-semibold">
                      ✅ Poprawnie
                    </span>
                  ) : (
                    <span className="px-4 py-1 bg-red-100 text-red-700 rounded-full font-semibold">
                      ❌ Niepoprawnie
                    </span>
                  )}
                </div>

                <p className="text-gray-800 font-medium mb-4">{question.question_text}</p>

                <div className="space-y-2">
                  {answers.map(({ key, text }) => {
                    const isCorrect = question.correct_answer === text;
                    const isSelected = question.selected_answer === text;
                    const wrongSelected = isSelected && !isCorrect;

                    return (
                      <div
                        key={key}
                        className={`p-3 rounded-lg border transition ${
                          isCorrect
                            ? 'bg-green-50 border-green-400'
                            : wrongSelected
                            ? 'bg-red-50 border-red-400'
                            : 'bg-gray-50 border-gray-200'
                        }`}
                      >
                        <strong>{key}.</strong> {text}
                        {isSelected && (
                          <span
                            className={`ml-2 text-sm font-semibold ${
                              isCorrect ? 'text-green-700' : 'text-red-700'
                            }`}
                          >
                            {isCorrect ? '(Twoja poprawna odpowiedź)' : '(Twoja błędna odpowiedź)'}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>

                {question.explanation && (
                  <div className="mt-4 p-4 bg-blue-50 border-l-4 border-blue-400 rounded-lg">
                    <p className="font-semibold text-blue-800">💡 Wyjaśnienie:</p>
                    <p className="text-gray-700 mt-1">{question.explanation}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Przyciski akcji */}
        <div className="flex flex-col sm:flex-row gap-4 mt-10">
          <button
            onClick={() => navigate('/dashboard')}
            className="flex-1 px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition font-semibold"
          >
            ← Powrót do panelu
          </button>
          <button
            onClick={() => navigate('/quiz/setup')}
            className="flex-1 px-6 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 transition font-semibold"
          >
            🔄 Spróbuj ponownie
          </button>
        </div>
      </div>
    </Layout>
  );
}
