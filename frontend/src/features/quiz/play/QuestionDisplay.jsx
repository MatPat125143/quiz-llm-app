import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { getQuestion, submitAnswer, startQuiz } from '../../../services/api';
import { getDifficultyBadgeClass, getDifficultyBadgeLabel } from '../../../services/helpers';
import MainLayout from '../../../layouts/MainLayout';
import LatexRenderer from '../../../components/LatexRenderer';
import useCurrentUser from '../../../hooks/useCurrentUser';
import { QuestionToaster } from './QuestionToasts';
import QuestionTimer from './QuestionTimer';

const TOAST_PRIORITY = {
  timeout: 4,
  levelUp: 3,
  fire: 2,
  milestone: 2,
  success: 1
};

const QUESTION_TOAST_STYLES = `
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
`;

function QuestionLoader({ title = 'Przygotowuję quiz...', subtitle }) {
  return (
    <MainLayout hideChrome>
      <div className="h-[125dvh] flex items-center justify-center bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-4">
        <div className="bg-white p-10 sm:p-12 rounded-2xl shadow-2xl text-center max-w-md w-full">
          <div className="animate-spin rounded-full h-20 w-20 border-b-4 border-indigo-600 mx-auto mb-6" />
          <h2 className="text-2xl font-bold text-gray-800 mb-3">{title}</h2>
          {subtitle && <p className="text-gray-600 mb-4">{subtitle}</p>}
          <div className="mt-6 space-y-2">
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-indigo-500 rounded-full animate-pulse" />
              <span>Inicjalizacja sesji...</span>
            </div>
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse delay-100" />
              <span>Przygotowywanie pytań...</span>
            </div>
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-pink-500 rounded-full animate-pulse delay-200" />
              <span>Za chwilę zaczynamy!</span>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

export default function QuestionDisplay() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const { user } = useCurrentUser();
  const [question, setQuestion] = useState(null);
  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [answered, setAnswered] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [timeLeft, setTimeLeft] = useState(30);
  const [timerActive, setTimerActive] = useState(false);
  const [error, setError] = useState('');

  const [toastQueue, setToastQueue] = useState([]);
  const [activeToast, setActiveToast] = useState(null);
  const timeoutToastShownRef = useRef(new Set());
  const toastContextRef = useRef('');
  const loadUserAndQuestionRef = useRef(null);
  const autoSubmitRef = useRef(null);
  const deadlineRef = useRef(null);
  const startTimeRef = useRef(null);
  const timeoutTriggeredRef = useRef(new Set());

  const showToast = useCallback((message, icon, type = 'success', duration = 2200) => {
    const priority = TOAST_PRIORITY[type] || 1;
    const context = toastContextRef.current;
    const createdAt = Date.now();
    const t = { id: `${createdAt}-${Math.random()}`, message, icon, type, duration, priority, context, createdAt };

    setToastQueue((q) => {
      
      const filtered = q.filter((item) => item.context === context);
      const next = [...filtered, t].sort((a, b) => {
        if (b.priority !== a.priority) return b.priority - a.priority;
        return a.createdAt - b.createdAt;
      });
      return next;
    });

    
    if (activeToast && activeToast.context === context && priority > (activeToast.priority || 0)) {
      setActiveToast(null);
    }
  }, [activeToast]);

  const showTimeoutToastOnce = useCallback((questionId) => {
    if (!questionId) return;
    const shown = timeoutToastShownRef.current;
    if (shown.has(questionId)) return;
    shown.add(questionId);
    showToast('Koniec czasu! Nie udzielono odpowiedzi w wymaganym czasie.', '⏰', 'timeout', 2000);
  }, [showToast]);

  useEffect(() => {
    if (activeToast || toastQueue.length === 0) return;
    setActiveToast(toastQueue[0]);
    setToastQueue((q) => q.slice(1));
  }, [activeToast, toastQueue]);

  const handleToastDone = () => setActiveToast(null);

  const [, setLastStreak] = useState(0);
  const [milestoneShown, setMilestoneShown] = useState(new Set());
  const [currentStreak, setCurrentStreak] = useState(0);

  const questionPollAttemptsRef = useRef(0);
  const questionPollTimerRef = useRef(null);
  const startAttemptedRef = useRef(false);

  const getDeadlineKey = (sessId, qId) => `quiz_timer:${sessId}:${qId}`;

  useEffect(() => {
    return () => {
      if (questionPollTimerRef.current) clearTimeout(questionPollTimerRef.current);
    };
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    setLoading(true);
    loadUserAndQuestionRef.current?.();
  }, [sessionId]);

  useEffect(() => {
    if (sessionId) return;
    if (startAttemptedRef.current) return;

    const startParams = location.state?.startParams;
    if (!startParams) {
      setError('Brak danych startowych quizu. Wróć do ustawień i rozpocznij grę ponownie.');
      setLoading(false);
      return;
    }

    startAttemptedRef.current = true;
    setLoading(true);
    setError('');

    (async () => {
      try {
        const response = await startQuiz(
          startParams.topic,
          startParams.difficulty,
          startParams.questionsCount,
          startParams.timePerQuestion,
          startParams.useAdaptiveDifficulty,
          startParams.subtopic || '',
          startParams.knowledgeLevel
        );
        navigate(`/quiz/play/${response.session_id}`, { replace: true });
      } catch (err) {
        console.error('Error starting quiz:', err);
        setError('Nie udało się uruchomić quizu. Spróbuj ponownie.');
        setLoading(false);
      }
    })();
    
  }, [sessionId, location.state?.startParams, navigate]);

  useEffect(() => {
    if (!timerActive || !question?.question_id) return;

    const timer = setInterval(() => {
      const deadline = deadlineRef.current;
      if (!Number.isFinite(deadline)) return;

      const remaining = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
      setTimeLeft(remaining);

      if (remaining <= 0) {
        setTimerActive(false);
        const qid = question.question_id;
        if (!timeoutTriggeredRef.current.has(qid)) {
          timeoutTriggeredRef.current.add(qid);
          autoSubmitRef.current?.();
        }
      }
    }, 250);

    return () => clearInterval(timer);
  }, [timerActive, question?.question_id]);

  const getMilestones = (totalQuestions) => {
    if (totalQuestions <= 5) return [3, 5];
    if (totalQuestions <= 10) return [4, 7, 10];
    if (totalQuestions <= 15) return [5, 10, 15];
    return [7, 14, 20];
  };

  useEffect(() => {
    if (result && result.current_streak !== undefined && result.is_correct) {
      const newStreak = result.current_streak;
      setCurrentStreak(newStreak);
      setLastStreak(newStreak);

      const totalQuestions = question?.questions_count || 10;
      const milestones = getMilestones(totalQuestions);
      const shown = milestoneShown;

      if (milestones.some((m) => newStreak >= m && !shown.has(m))) {
        const hit = milestones.filter((m) => newStreak >= m && !shown.has(m));
        hit.forEach((m) => shown.add(m));
        setMilestoneShown(new Set(shown));
        showToast(`Seria ${newStreak}!`, '🔥', 'fire', 1800);
      }
    } else if (result && !result.is_correct) {
      setCurrentStreak(0);
    }
    
  }, [result, question?.questions_count, milestoneShown, showToast]);

  const loadUserAndQuestion = async () => {
    let keepLoading = false;
    try {
      setError('');
      const questionData = await getQuestion(sessionId);
      questionPollAttemptsRef.current = 0;

      toastContextRef.current = `q:${questionData.question_id || Date.now()}`;
      setToastQueue([]);
      setActiveToast(null);
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
      deadlineRef.current = deadline;
      startTimeRef.current = deadline - durationMs;

      const remainingSeconds = Math.max(0, Math.ceil((deadline - now) / 1000));
      setTimeLeft(remainingSeconds);
      setTimerActive(remainingSeconds > 0);

      if (remainingSeconds <= 0 && !timeoutTriggeredRef.current.has(questionData.question_id)) {
        timeoutTriggeredRef.current.add(questionData.question_id);
        setTimeout(() => autoSubmitRef.current?.(), 0);
      }
    } catch (err) {
      console.error('Error loading question:', err);
      if (err.response?.status === 404) {
        const apiError = err.response?.data?.error;

        if (apiError === 'Quiz already completed') {
          navigate(`/quiz/details/${sessionId}`);
          return;
        }

        if (apiError === 'No more questions available') {
          const maxAttempts = 25; 
          const delayMs = 400;
          const nextAttempt = questionPollAttemptsRef.current + 1;
          questionPollAttemptsRef.current = nextAttempt;

          if (nextAttempt <= maxAttempts) {
            keepLoading = true;
            questionPollTimerRef.current = setTimeout(() => {
              loadUserAndQuestionRef.current?.();
            }, delayMs);
            return;
          }

          setError('Nie udało się pobrać kolejnego pytania. Spróbuj ponownie za chwilę.');
          return;
        }

        navigate('/dashboard');
      }
      else setError('Nie udało się załadować pytania. Spróbuj ponownie.');
    } finally {
      if (!keepLoading) setLoading(false);
    }
  };

  const handleAutoSubmit = async () => {
    if (!answered && question && question.question_id) {
      showTimeoutToastOnce(question.question_id);
      await handleSubmit('', true);
    }
  };

  loadUserAndQuestionRef.current = loadUserAndQuestion;
  autoSubmitRef.current = handleAutoSubmit;

  useEffect(() => {
    if (result?.was_timeout) showTimeoutToastOnce(question?.question_id);
  }, [result?.was_timeout, question?.question_id, showTimeoutToastOnce]);

  const handleSubmit = async (answer = selectedAnswer, isAutoSubmit = false) => {
    if (submitting) return;
    if (!answer && !isAutoSubmit) return;

    setSubmitting(true);
    setTimerActive(false);
    setAnswered(true);

    const now = Date.now();
    const baseStart = Number.isFinite(startTimeRef.current) ? startTimeRef.current : now;
    const actualResponseTime = Math.max(0, Math.floor((now - baseStart) / 1000));
    const maxTime = Number(question.time_per_question) || 30;
    const responseTime = Math.min(actualResponseTime, maxTime);

    try {
      const response = await submitAnswer(question.question_id, answer || '', responseTime);
      localStorage.removeItem(getDeadlineKey(sessionId, question.question_id));
      setResult(response);

      if (response?.difficulty_changed) {
        const difficultyOrder = {
          'łatwy': 1, latwy: 1, easy: 1,
          'średni': 2, sredni: 2, medium: 2,
          trudny: 3, hard: 3
        };
        const prev = String(response.previous_difficulty || '').toLowerCase();
        const next = String(response.new_difficulty || '').toLowerCase();
        const prevLevel = difficultyOrder[prev] || 2;
        const nextLevel = difficultyOrder[next] || 2;

        if (nextLevel > prevLevel) {
          showToast('Poziom trudności wzrósł!', '⬆️', 'levelUp', 2000);
        } else if (nextLevel < prevLevel) {
          showToast('Poziom trudności zmalał', '⬇️', 'levelUp', 2000);
        } else {
          showToast('Zmieniono poziom trudności', '⚖️', 'levelUp', 2000);
        }
      }

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
    
    toastContextRef.current = `loading:${Date.now()}`;
    setToastQueue([]);
    setActiveToast(null);
    setQuestion(null);
    setLoading(true);
    loadUserAndQuestionRef.current?.();
  };

  if (loading) {
    return (
      <QuestionLoader
        title={question ? 'Przygotowuję kolejne pytanie...' : 'Przygotowuję quiz...'}
        subtitle={question?.topic ? `Temat: ${question.topic}${question.subtopic ? ` • ${question.subtopic}` : ''}` : undefined}
      />
    );
  }

  if (loading && !question) {
    return (
      <MainLayout user={user} hideChrome>
        <div className="h-[125dvh] flex items-center justify-center bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500">
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
        <div className="h-[125dvh] flex items-center justify-center bg-gray-100">
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
    return (
    <MainLayout user={user} hideChrome>
      <style>{QUESTION_TOAST_STYLES}</style>
      <QuestionToaster toast={activeToast} onDone={handleToastDone} />

      <div className="h-[125dvh] bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 p-2 sm:p-4 overflow-hidden">
        <div className="max-w-4xl mx-auto h-full py-2 sm:py-8">
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden w-full h-[calc(100%-1rem)] sm:h-[calc(100%-4rem)] flex flex-col">
            <div className="p-4 sm:p-6 pb-5 flex-shrink-0">
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
                <QuestionTimer timeLeft={timeLeft} />
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-3">
                <span className="text-sm text-gray-600">Poziom trudności:</span>
                <span className={`px-3 py-1 text-sm font-semibold rounded-full ${getDifficultyBadgeClass(question.difficulty_label)}`}>
                  {getDifficultyBadgeLabel(question.difficulty_label)}
                </span>
                <span className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="text-lg">🔥</span>
                  <span className="font-semibold">Seria: {currentStreak}</span>
                </span>
              </div>
            </div>

            <div className="px-4 sm:px-8 flex-1 min-h-0 overflow-y-auto">
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

                {result && result.explanation && (
                  <div className="p-4 bg-blue-50 border-l-4 border-blue-400 rounded-lg">
                    <p className="font-semibold text-blue-800 mb-1">ℹ️ Wyjaśnienie:</p>
                    <LatexRenderer text={result.explanation} className="text-gray-700" />
                  </div>
                )}
              </div>
            </div>

            <div className="px-4 sm:px-8 pt-4 pb-4 sm:pt-6 sm:pb-6 flex-shrink-0 border-t border-gray-100">
              {!result ? (
                <button
                  onClick={() => handleSubmit()}
                  disabled={!selectedAnswer || submitting}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-4 rounded-xl font-bold text-lg hover:from-blue-700 hover:to-purple-700 transition-all shadow-lg disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98]"
                >
                  {submitting ? 'Sprawdzanie...' : 'Sprawdź odpowiedź'}
                </button>
              ) : result.quiz_completed ? (
                <div className="w-full h-[64px] bg-white/80 border border-purple-200 rounded-xl px-5 flex items-center justify-center gap-3 shadow-sm overflow-hidden">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-purple-600" />
                  <p className="font-semibold text-gray-800">Quiz ukończony — przekierowywanie do wyników...</p>
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

