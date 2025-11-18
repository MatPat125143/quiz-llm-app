import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getQuestion, submitAnswer, getCurrentUser } from '../../services/api';
import MainLayout from '../../layouts/MainLayout';
import Spinner from '../../components/Spinner';

export default function QuestionDisplay() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [question, setQuestion] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const [timeLeft, setTimeLeft] = useState(30);
  const [timerActive, setTimerActive] = useState(false);
  const [startTime, setStartTime] = useState(null);

  useEffect(() => {
    loadUserAndQuestion();
  }, [sessionId]);

  // Timer effect
  useEffect(() => {
    if (!timerActive || timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          setTimerActive(false);
          handleAutoSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [timerActive, timeLeft]);

  const loadUserAndQuestion = async () => {
    try {
      const [userData, questionData] = await Promise.all([
        getCurrentUser(),
        getQuestion(sessionId)
      ]);

      setUser(userData);
      setQuestion(questionData);
      setTimeLeft(questionData.time_per_question || 30);
      setTimerActive(true);
      setStartTime(Date.now());

      console.log('⏳ Pytanie wygenerowane:', questionData.generation_status);
    } catch (err) {
      console.error('Error loading question:', err);
      if (err.response?.status === 404) {
        navigate('/dashboard');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleAutoSubmit = () => {
    if (!selectedAnswer && question) {
      const randomAnswer = question.answers[Math.floor(Math.random() * question.answers.length)];
      handleSubmit(randomAnswer, true);
    }
  };

  const handleSubmit = async (answer = selectedAnswer, isAutoSubmit = false) => {
    if (!answer || submitting) return;

    setSubmitting(true);
    setTimerActive(false);

    const responseTime = Math.floor((Date.now() - startTime) / 1000);

    try {
      const response = await submitAnswer(question.question_id, answer, responseTime);
      setResult(response);

      if (response.quiz_completed) {
        setTimeout(() => {
          navigate(`/quiz/details/${sessionId}`);
        }, 3000);
      }
    } catch (err) {
      console.error('Error submitting answer:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const handleNextQuestion = () => {
    setSelectedAnswer(null);
    setResult(null);
    setLoading(true);
    loadUserAndQuestion();
  };

  if (loading) {
    return (
      <MainLayout user={user}>
        <div className="min-h-screen flex items-center justify-center">
          <Spinner text="Ładowanie pytania..." />
        </div>
      </MainLayout>
    );
  }

  if (!question) {
    return (
      <MainLayout user={user}>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <div className="text-6xl mb-4">😔</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Brak pytań</h2>
            <p className="text-gray-600 mb-6">Nie znaleziono więcej pytań dla tego quizu</p>
            <button
              onClick={() => navigate('/dashboard')}
              className="px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition font-semibold"
            >
              Powrót do panelu
            </button>
          </div>
        </div>
      </MainLayout>
    );
  }

  const answers = ['option_a', 'option_b', 'option_c', 'option_d'].map(key => question[key]);

  return (
    <MainLayout user={user}>
      <div className="max-w-4xl mx-auto px-6 py-8">
        {/* Header z timerem */}
        <div className="mb-6 flex justify-between items-center bg-white p-4 rounded-xl shadow-lg">
          <div className="flex gap-4 text-sm">
            <span className="font-semibold text-gray-600">
              Pytanie {question.question_number} / {question.questions_count}
            </span>
            <span className="text-indigo-600 font-semibold">
              {question.difficulty_label}
            </span>
          </div>

          <div className={`text-2xl font-bold ${timeLeft <= 5 ? 'text-red-600 animate-pulse' : 'text-gray-700'}`}>
            ⏱️ {timeLeft}s
          </div>
        </div>

        {/* Pytanie */}
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">
            {question.question_text}
          </h2>

          {/* Odpowiedzi */}
          <div className="space-y-3">
            {answers.map((answer, index) => {
              const letter = String.fromCharCode(65 + index);
              const isSelected = selectedAnswer === answer;
              const isCorrect = result && answer === result.correct_answer;
              const isWrong = result && isSelected && !result.is_correct;

              return (
                <button
                  key={index}
                  onClick={() => !result && setSelectedAnswer(answer)}
                  disabled={!!result}
                  className={`
                    w-full p-4 rounded-xl border-2 text-left transition-all font-medium
                    ${!result && !isSelected ? 'border-gray-200 hover:border-indigo-400 hover:bg-indigo-50' : ''}
                    ${!result && isSelected ? 'border-indigo-500 bg-indigo-50' : ''}
                    ${isCorrect ? 'border-green-500 bg-green-50' : ''}
                    ${isWrong ? 'border-red-500 bg-red-50' : ''}
                    ${result ? 'cursor-default' : 'cursor-pointer'}
                  `}
                >
                  <span className="font-bold text-indigo-600 mr-3">{letter}.</span>
                  {answer}
                  {isCorrect && <span className="ml-3 text-green-600">✅</span>}
                  {isWrong && <span className="ml-3 text-red-600">❌</span>}
                </button>
              );
            })}
          </div>

          {/* Wyjaśnienie */}
          {result && result.explanation && (
            <div className="mt-6 p-4 bg-blue-50 border-l-4 border-blue-400 rounded-lg">
              <p className="font-semibold text-blue-800 mb-1">💡 Wyjaśnienie:</p>
              <p className="text-gray-700">{result.explanation}</p>
            </div>
          )}

          {/* Akcje */}
          {!result ? (
            <button
              onClick={() => handleSubmit()}
              disabled={!selectedAnswer || submitting}
              className="w-full mt-6 bg-gradient-to-r from-indigo-600 to-purple-600 text-white py-4 rounded-xl font-bold text-lg hover:from-indigo-700 hover:to-purple-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Sprawdzanie...' : 'Sprawdź odpowiedź'}
            </button>
          ) : (
            <div className="mt-6 space-y-4">
              {result.quiz_completed ? (
                <div className="text-center">
                  <div className="text-6xl mb-4">🎉</div>
                  <h3 className="text-2xl font-bold text-gray-800 mb-2">Quiz ukończony!</h3>
                  <p className="text-gray-600 mb-4">Przekierowywanie do wyników...</p>
                </div>
              ) : (
                <button
                  onClick={handleNextQuestion}
                  className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-4 rounded-xl font-bold text-lg hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg"
                >
                  Następne pytanie →
                </button>
              )}
            </div>
          )}
        </div>

        {/* Stats */}
        {result && (
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-3xl font-bold text-indigo-600">{result.session_stats.total_questions}</div>
                <div className="text-sm text-gray-600">Odpowiedzi</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-green-600">{result.session_stats.correct_answers}</div>
                <div className="text-sm text-gray-600">Poprawne</div>
              </div>
              <div>
                <div className="text-3xl font-bold text-purple-600">{result.session_stats.accuracy}%</div>
                <div className="text-sm text-gray-600">Celność</div>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  );
}