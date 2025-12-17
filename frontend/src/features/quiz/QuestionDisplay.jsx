import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getQuestion, submitAnswer, getCurrentUser } from '../../services/api';
import MainLayout from '../../layouts/MainLayout';
import LatexRenderer from '../../components/LatexRenderer';

/* =========================
   NOWE POPUPY (TOASTER)
   - kolejka (nie zjada się)
   - auto-zamykanie + animacja wyjścia
   - responsywne (mobile: center, desktop: prawa strona)
   - “obramowanie” w kolorze toasta (box-shadow ring) – nie białe
   - type: fire ma pomarańczowy gradient (nie amber)
========================= */

const TOAST_THEME = {
  success: { gradient: 'from-green-600 to-emerald-700', border: '#047857' },
  levelUp: { gradient: 'from-purple-600 to-pink-700', border: '#7e22ce' },
  milestone: { gradient: 'from-orange-600 to-red-700', border: '#c2410c' },
  fire: { gradient: 'from-orange-600 to-orange-800', border: '#9a3412' } // ✅ X poprawnych!
};

function ToastCard({ toast, onDone }) {
  const [phase, setPhase] = useState('in'); // in | out
  const theme = TOAST_THEME[toast.type] || TOAST_THEME.success;

  useEffect(() => {
    const duration = toast.duration ?? 5000;
    const exitMs = 320;

    const t1 = setTimeout(() => setPhase('out'), Math.max(0, duration - exitMs));
    const t2 = setTimeout(onDone, duration);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [toast, onDone]);

  return (
    <div
      className={`
        ${phase === 'out' ? 'toast-out' : 'toast-in'}
        w-[min(520px,calc(100vw-1.5rem))]
        bg-gradient-to-r ${theme.gradient}
        text-white px-6 sm:px-7 py-4 rounded-2xl
        flex items-center gap-4
        backdrop-blur-sm
      `}
      style={{
        // ✅ obramowanie w kolorze toasta (drugi cień) + cień główny
        boxShadow: `0 18px 45px rgba(0,0,0,0.35), 0 0 0 2px ${theme.border}`
      }}
      onClick={() => {
        setPhase('out');
        setTimeout(onDone, 180);
      }}
      role="status"
      aria-live="polite"
    >
      <span className="text-4xl animate-bounce">{toast.icon}</span>
      <div className="flex-1">
        <p className="font-bold text-lg leading-tight drop-shadow-md">{toast.message}</p>
      </div>
    </div>
  );
}

function Toaster({ toast, onDone }) {
  if (!toast) return null;

  return (
    <div
      className="fixed inset-x-0 z-50 px-3 sm:px-6 pointer-events-none"
      style={{
        // ✅ pewne odsunięcie od góry (nie margin/padding)
        top: 'calc(env(safe-area-inset-top, 0px) + 160px)'
      }}
    >
      <div className="flex justify-center sm:justify-end sm:pr-6 md:pr-10 pointer-events-none">
        <div className="pointer-events-auto">
          <ToastCard key={toast.id} toast={toast} onDone={onDone} />
        </div>
      </div>
    </div>
  );
}

/* ========================= */

export default function QuestionDisplay() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [question, setQuestion] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [answered, setAnswered] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [timeLeft, setTimeLeft] = useState(30);
  const [timerActive, setTimerActive] = useState(false);
  const [startTime, setStartTime] = useState(null);
  const [error, setError] = useState('');

  // ===== Toast kolejka =====
  const [toastQueue, setToastQueue] = useState([]);
  const [activeToast, setActiveToast] = useState(null);

  const showToast = (message, icon, type = 'success', duration = 5000) => {
    const t = { id: `${Date.now()}-${Math.random()}`, message, icon, type, duration };
    setToastQueue((q) => [...q, t]);
  };

  useEffect(() => {
    if (activeToast || toastQueue.length === 0) return;
    setActiveToast(toastQueue[0]);
    setToastQueue((q) => q.slice(1));
  }, [activeToast, toastQueue]);

  const handleToastDone = () => setActiveToast(null);

  // ===== Pozostałe stany =====
  const [previousDifficulty, setPreviousDifficulty] = useState(null);
  const [lastStreak, setLastStreak] = useState(0);
  const [milestoneShown, setMilestoneShown] = useState(new Set());
  const [currentStreak, setCurrentStreak] = useState(0);

  const getDeadlineKey = (sessId, qId) => `quiz_timer:${sessId}:${qId}`;

  useEffect(() => {
    loadUserAndQuestion();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timerActive, timeLeft]);

  const getMilestones = (totalQuestions) => {
    if (totalQuestions <= 5) return [3, 5];
    if (totalQuestions <= 10) return [4, 7, 10];
    if (totalQuestions <= 15) return [5, 10, 15];
    return [7, 14, 20];
  };

  // Zmiana trudności -> toast levelUp
  useEffect(() => {
    if (question && previousDifficulty && question.difficulty_label !== previousDifficulty) {
      const current = (question.difficulty_label || '').toLowerCase();
      const prev = previousDifficulty.toLowerCase();

      const difficultyOrder = {
        'łatwy': 1, latwy: 1, easy: 1,
        'średni': 2, sredni: 2, medium: 2,
        trudny: 3, hard: 3
      };

      const currentLevel = difficultyOrder[current] || 2;
      const prevLevel = difficultyOrder[prev] || 2;

      if (currentLevel > prevLevel) {
        showToast('Poziom trudności wzrósł! 💪', '⬆️', 'levelUp', 5000);
      } else if (currentLevel < prevLevel) {
        showToast('Poziom trudności zmalał 📉', '⬇️', 'levelUp', 5000);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [question?.difficulty_label]);

  // Seria -> toasty milestone/fire
  useEffect(() => {
    if (result && result.current_streak !== undefined && result.is_correct) {
      const newStreak = result.current_streak;
      setCurrentStreak(newStreak);

      const totalQuestions = question?.questions_count || 10;
      const milestones = getMilestones(totalQuestions);

      milestones.forEach((milestone, index) => {
        const milestoneKey = `${sessionId}-${milestone}`;
        if (newStreak === milestone && !milestoneShown.has(milestoneKey)) {
          setMilestoneShown((prev) => new Set([...prev, milestoneKey]));

          if (index === 0) showToast(`Dobry start! ${milestone} poprawnych! 🎯`, '🔥', 'fire', 5000);
          else if (index === 1) showToast(`Świetna passa! ${milestone} z rzędu! 🚀`, '🔥🔥', 'milestone', 5000);
          else if (index === 2) showToast(`Niesamowite! ${milestone} poprawnych! 👑`, '🔥🔥🔥', 'milestone', 5000);
        }
      });

      if (newStreak > 0 && newStreak % 3 === 0 && newStreak > lastStreak) {
        const milestoneKey = `${sessionId}-series-${newStreak}`;
        if (!milestoneShown.has(milestoneKey) && !milestones.includes(newStreak)) {
          setMilestoneShown((prev) => new Set([...prev, milestoneKey]));
          showToast(`${newStreak} poprawnych! Tak trzymaj! 💪`, '✨', 'fire', 5000); // ✅ fire = pomarańczowe
        }
      }

      setLastStreak(newStreak);
    } else if (result && !result.is_correct) {
      setCurrentStreak(0);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [result?.current_streak]);

  const loadUserAndQuestion = async () => {
    try {
      setError('');
      const [userData, questionData] = await Promise.all([getCurrentUser(), getQuestion(sessionId)]);

      setUser(userData);

      // zapisz poprzedni poziom trudności
      if (question) setPreviousDifficulty(question.difficulty_label);

      setQuestion(questionData);
      setAnswered(false);
      setSelectedAnswer(null);
      setResult(null);

      const durationMs = (questionData.time_per_question || 30) * 1000;
      const key = getDeadlineKey(sessionId, questionData.question_id);
      const stored = parseInt(localStorage.getItem(key), 10);
      const now = Date.now();
      const deadline = Number.isFinite(stored) ? stored : now + durationMs;
      localStorage.setItem(key, deadline);

      const remainingSeconds = Math.max(0, Math.ceil((deadline - now) / 1000));
      setTimeLeft(remainingSeconds);
      setStartTime(deadline - durationMs);
      setTimerActive(remainingSeconds > 0);

      if (remainingSeconds <= 0) setTimeout(() => handleAutoSubmit(), 0);
    } catch (err) {
      console.error('Error loading question:', err);
      if (err.response?.status === 404) navigate('/dashboard');
      else setError('Nie udało się załadować pytania. Spróbuj ponownie.');
    } finally {
      setLoading(false);
    }
  };

  const handleAutoSubmit = async () => {
    if (!answered && question && question.question_id) {
      await handleSubmit('', true);
    }
  };

  const handleSubmit = async (answer = selectedAnswer, isAutoSubmit = false) => {
    if (submitting) return;
    if (!answer && !isAutoSubmit) return;

    setSubmitting(true);
    setTimerActive(false);
    setAnswered(true);

    const actualResponseTime = Math.floor((Date.now() - startTime) / 1000);
    const responseTime = Math.min(actualResponseTime, question.time_per_question);

    try {
      const response = await submitAnswer(question.question_id, answer || '', responseTime);
      localStorage.removeItem(getDeadlineKey(sessionId, question.question_id));
      setResult(response);

      if (response.quiz_completed) {
        setTimeout(() => navigate(`/quiz/details/${sessionId}`), 3000);
      }
    } catch (err) {
      console.error('Error submitting answer:', err);
      setError('Nie udało się zapisać odpowiedzi. Spróbuj ponownie.');
      setAnswered(false);
    } finally {
      setSubmitting(false);
    }
  };

  const handleNextQuestion = () => {
    if (loading) return;
    setLoading(true);
    loadUserAndQuestion();
  };

  if (loading && !question) {
    return (
      <MainLayout user={user} hideChrome>
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500">
          <div className="bg-white p-12 rounded-2xl shadow-2xl text-center max-w-md">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-indigo-600 mx-auto mb-6"></div>
            <h2 className="text-2xl font-bold text-gray-800 mb-3">Generuję pytanie...</h2>
            <p className="text-gray-600">Przygotowujemy dla Ciebie kolejne pytanie</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  if (error && !question) {
    return (
      <MainLayout user={user} hideChrome>
        <div className="min-h-screen flex items-center justify-center bg-gray-100">
          <div className="bg-white p-8 rounded-2xl shadow-xl text-center max-w-md">
            <div className="text-6xl mb-4">😕</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Ups! Coś poszło nie tak</h2>
            <p className="text-gray-600 mb-6">{error}</p>
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

  if (!question) return null;

  const answers = ['option_a', 'option_b', 'option_c', 'option_d'].map((key) => question[key]);
  const normalizedDifficultyLabel = question.difficulty_label
    ? question.difficulty_label.charAt(0).toUpperCase() + question.difficulty_label.slice(1)
    : '';

  const difficultyPillClass = () => {
    const label = (question.difficulty_label || '').toLowerCase();
    if (['łatwy', 'latwy', 'easy'].includes(label)) return 'bg-green-100 text-green-800';
    if (['średni', 'sredni', 'medium'].includes(label)) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const optionClass = (answer) => {
    const isSelected = selectedAnswer === answer;
    if (!result) {
      return isSelected
        ? 'border-indigo-500 bg-indigo-50'
        : 'border-gray-200 hover:border-indigo-400 hover:bg-indigo-50';
    }
    if (answer === result.correct_answer) return 'border-green-500 bg-green-50';
    if (isSelected && !result.is_correct) return 'border-red-500 bg-red-50';
    return 'border-gray-200 bg-gray-50';
  };

  const timeExpired = timeLeft <= 0;

  return (
    <MainLayout user={user} hideChrome>
      <style>{`
        @keyframes toastIn {
          from { transform: translateY(-10px) translateX(18px) scale(.98); opacity: 0; }
          to   { transform: translateY(0)     translateX(0)    scale(1);   opacity: 1; }
        }
        @keyframes toastOut {
          from { transform: translateY(0)     translateX(0)    scale(1);   opacity: 1; }
          to   { transform: translateY(-8px)  translateX(18px) scale(.98); opacity: 0; }
        }
        .toast-in  { animation: toastIn  260ms cubic-bezier(.2,1,.2,1) both; }
        .toast-out { animation: toastOut 320ms ease-in both; }
      `}</style>

      {/* POPUPY */}
      <Toaster toast={activeToast} onDone={handleToastDone} />

      <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-4">
        <div className="max-w-4xl mx-auto py-8">
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden h-[86vh] flex flex-col pb-6">
            <div className="p-6 pb-5 flex-shrink-0">
              <div className="flex justify-between items-start gap-4">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-3">
                    <span className="inline-flex items-center justify-center h-14 w-14 text-4xl leading-none">🧠</span>
                    <div className="flex flex-col">
                      <div className="flex flex-wrap items-baseline gap-2">
                        <h2 className="text-2xl font-bold text-gray-800 leading-tight">{question.topic}</h2>
                        {question.subtopic && (
                          <span className="text-sm text-gray-600 font-medium">{question.subtopic}</span>
                        )}
                      </div>
                      <p className="text-gray-600">
                        Pytanie {question.question_number} z {question.questions_count || 10}
                      </p>
                    </div>
                  </div>
                </div>
                <div
                  className={`text-3xl font-bold ${
                    timeLeft <= 5 ? 'text-red-600 animate-pulse' : timeLeft <= 10 ? 'text-yellow-600' : 'text-green-600'
                  }`}
                >
                  ⏳ {timeLeft}s
                </div>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-3">
                <span className="text-sm text-gray-600">Poziom trudności:</span>
                <span className={`px-3 py-1 text-sm font-semibold rounded-full ${difficultyPillClass()}`}>
                  {normalizedDifficultyLabel || 'Średni'}
                </span>
                <span className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="text-lg">🔥</span>
                  <span className="font-semibold">Seria: {currentStreak}</span>
                </span>
              </div>
            </div>

            <div className="px-8 flex-1 overflow-y-auto">
              <div className="flex flex-col gap-6 pb-6">
                <h3 className="text-2xl font-bold text-gray-800">
                  <LatexRenderer text={question.question_text} />
                </h3>

                <div className="space-y-3">
                  {answers.map((answer, index) => {
                    const letter = String.fromCharCode(65 + index);
                    const isSelected = selectedAnswer === answer;
                    return (
                      <button
                        key={index}
                        onClick={() => !result && setSelectedAnswer(answer)}
                        disabled={!!result}
                        className={`
                          w-full text-left p-4 rounded-lg border-2 transition
                          ${optionClass(answer)}
                          ${result ? 'cursor-default' : 'cursor-pointer'}
                        `}
                      >
                        <span className="font-bold text-indigo-600 mr-3">{letter}.</span>
                        <LatexRenderer text={answer} inline />
                        {result && result.correct_answer === answer && <span className="ml-3 text-green-600">✔</span>}
                        {result && isSelected && !result.is_correct && <span className="ml-3 text-red-600">✖</span>}
                      </button>
                    );
                  })}
                </div>

                {(timeExpired || (result && result.was_timeout)) && (
                  <div className="p-4 bg-orange-50 border-l-4 border-orange-400 rounded-lg">
                    <p className="font-semibold text-orange-800 mb-1">⏰ Koniec czasu!</p>
                    <p className="text-gray-700">Nie udzielono odpowiedzi w wymaganym czasie.</p>
                  </div>
                )}

                {result && result.explanation && (
                  <div className="p-4 bg-blue-50 border-l-4 border-blue-400 rounded-lg">
                    <p className="font-semibold text-blue-800 mb-1">ℹ️ Wyjaśnienie:</p>
                    <LatexRenderer text={result.explanation} className="text-gray-700" />
                  </div>
                )}
              </div>
            </div>

            <div className="px-8 pt-6 pb-0 mb-6 flex-shrink-0 border-t border-gray-100">
              {!result ? (
                <button
                  onClick={() => handleSubmit()}
                  disabled={!selectedAnswer || submitting}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 rounded-xl font-bold text-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98]"
                >
                  {submitting ? 'Sprawdzanie...' : '✓ Sprawdź odpowiedź'}
                </button>
              ) : result.quiz_completed ? (
                <div className="text-center py-4">
                  <div className="text-6xl mb-3">🎉</div>
                  <h3 className="text-2xl font-bold text-gray-800 mb-2">Quiz ukończony!</h3>
                  <p className="text-gray-600 mb-4">Przekierowywanie do wyników...</p>
                </div>
              ) : (
                <button
                  onClick={handleNextQuestion}
                  className="w-full bg-gradient-to-r from-green-600 to-emerald-600 text-white py-4 rounded-xl font-bold text-lg hover:from-green-700 hover:to-emerald-700 transition-all shadow-lg transform hover:scale-[1.02] active:scale-[0.98]"
                >
                  Następne pytanie →
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
