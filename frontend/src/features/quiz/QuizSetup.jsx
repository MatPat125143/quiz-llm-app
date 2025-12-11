import { useState, useEffect } from 'react';
import { startQuiz, getCurrentUser } from '../../services/api';
import { useNavigate } from 'react-router-dom';
import MainLayout from '../../layouts/MainLayout';
import {
  PREDEFINED_TOPICS,
  TOPIC_SUBTOPICS,
  KNOWLEDGE_LEVELS,
  QUIZ_DEFAULTS
} from '../../services/constants';

export default function QuizSetup() {
  const [user, setUser] = useState(null);
  const [topic, setTopic] = useState('');
  const [subtopic, setSubtopic] = useState('');
  const [knowledgeLevel, setKnowledgeLevel] = useState(QUIZ_DEFAULTS.KNOWLEDGE_LEVEL);
  const [difficulty, setDifficulty] = useState(QUIZ_DEFAULTS.DIFFICULTY);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [questionsCount, setQuestionsCount] = useState(QUIZ_DEFAULTS.QUESTIONS_COUNT);
  const [timePerQuestion, setTimePerQuestion] = useState(QUIZ_DEFAULTS.TIME_PER_QUESTION);
  const [useAdaptiveDifficulty, setUseAdaptiveDifficulty] = useState(QUIZ_DEFAULTS.USE_ADAPTIVE_DIFFICULTY);

  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        const userData = await getCurrentUser();
        setUser(userData);

        // Ustaw domyślny poziom wiedzy z profilu użytkownika
        if (userData.profile?.default_knowledge_level) {
          setKnowledgeLevel(userData.profile.default_knowledge_level);
        }
      } catch (err) {
        console.error('Error loading user:', err);
      }
    })();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic.trim()) {
      setError('Proszę wprowadzić lub wybrać temat.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await startQuiz(
        topic,
        difficulty,
        questionsCount,
        timePerQuestion,
        useAdaptiveDifficulty,
        subtopic,
        knowledgeLevel
      );
      navigate(`/quiz/play/${response.session_id}`);
    } catch (err) {
      console.error(err);
      setError('Nie udało się uruchomić quizu. Spróbuj ponownie.');
      setLoading(false);
    }
  };

   if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-500 to-purple-600">
        <div className="bg-white p-12 rounded-2xl shadow-2xl text-center max-w-md">
          <div className="animate-spin rounded-full h-20 w-20 border-b-4 border-blue-600 mx-auto mb-6"></div>
          <h2 className="text-2xl font-bold text-gray-800 mb-3">
            🚀 Przygotowuję quiz...
          </h2>
          <p className="text-gray-600 mb-4">
            Tworzę spersonalizowany quiz na temat: <strong>{topic}</strong>
          </p>
          <div className="mt-6 space-y-2">
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span>Inicjalizacja sesji...</span>
            </div>
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse delay-100"></div>
              <span>Przygotowywanie pytań...</span>
            </div>
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500">
              <div className="w-2 h-2 bg-pink-500 rounded-full animate-pulse delay-200"></div>
              <span>Za chwilę rozpoczniemy!</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <MainLayout user={user}>
      <div className="max-w-6xl mx-auto px-4 py-6">
        <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
          <h1 className="text-2xl font-bold text-gray-800 mb-2 flex items-center gap-2">
            🎯 Rozpocznij nowy quiz
          </h1>
          <p className="text-gray-600 text-sm mb-4">
            Wybierz temat, poziom trudności i rozpocznij quiz dopasowany do Twojego stylu nauki.
          </p>

          <div className="bg-blue-50 border-l-4 border-blue-500 px-4 py-3 rounded-r-lg mb-4">
            <p className="text-sm text-blue-800">
              <strong>ℹ️ Informacja:</strong> Pytania generowane są przez sztuczną inteligencję. AI nie jest doskonałe i może sporadycznie tworzyć pytania zawierające błędy lub nieścisłości. Prosimy o wyrozumiałość i zgłaszanie ewentualnych problemów.
            </p>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded-xl mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
              <div className="space-y-5">
                <div>
                  <label className="block text-base font-bold text-gray-800 mb-2">
                    Temat quizu
                  </label>
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    placeholder="Wprowadź własny temat lub wybierz poniżej"
                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 text-sm"
                    disabled={loading}
                  />
                  <div className="mt-3">
                    <p className="text-xs text-gray-600 mb-2 font-semibold">
                      Lub wybierz popularny temat:
                    </p>
                    <div className="grid grid-cols-3 gap-2">
                      {PREDEFINED_TOPICS.map((t) => (
                        <button
                          key={t}
                          type="button"
                          onClick={() => setTopic(t)}
                          className={`px-3 py-1.5 rounded-lg border-2 font-semibold text-xs transition-all ${
                            topic === t
                              ? 'bg-indigo-600 text-white border-transparent'
                              : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-400'
                          }`}
                          disabled={loading}
                        >
                          {t}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {topic && TOPIC_SUBTOPICS[topic] && (
                  <div>
                    <label className="block text-base font-bold text-gray-800 mb-2">
                      Podtemat (opcjonalnie)
                    </label>
                    <input
                      type="text"
                      value={subtopic}
                      onChange={(e) => setSubtopic(e.target.value)}
                      placeholder="Wprowadź własny podtemat"
                      className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:outline-none focus:border-indigo-500 text-sm mb-2"
                      disabled={loading}
                    />
                    <div className="grid grid-cols-3 gap-2">
                      {TOPIC_SUBTOPICS[topic].slice(0, 6).map((sub) => (
                        <button
                          key={sub}
                          type="button"
                          onClick={() => setSubtopic(sub)}
                          className={`px-2 py-1.5 rounded-lg border-2 text-xs font-semibold transition-all ${
                            subtopic === sub
                              ? 'bg-indigo-100 border-indigo-500 text-indigo-700'
                              : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-300'
                          }`}
                          disabled={loading}
                        >
                          {sub}
                        </button>
                      ))}
                    </div>
                    {subtopic && (
                      <button
                        type="button"
                        onClick={() => setSubtopic('')}
                        className="mt-1 text-xs text-gray-500 hover:text-gray-700 underline"
                        disabled={loading}
                      >
                        Wyczyść
                      </button>
                    )}
                  </div>
                )}
              </div>

              <div className="space-y-5">

                <div>
                  <label className="block text-base font-bold text-gray-800 mb-2">
                    Poziom wiedzy
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {KNOWLEDGE_LEVELS.map((level) => (
                      <button
                        key={level.key}
                        type="button"
                        onClick={() => setKnowledgeLevel(level.key)}
                        className={`py-2 rounded-lg border-2 font-semibold transition-all text-xs ${
                          knowledgeLevel === level.key
                            ? 'bg-indigo-600 text-white border-transparent'
                            : 'bg-gray-50 text-gray-800 border-gray-200 hover:border-indigo-400'
                        }`}
                        disabled={loading}
                      >
                        <div className="text-lg mb-0.5">{level.emoji}</div>
                        <div>{level.label}</div>
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-base font-bold text-gray-800 mb-2">
                    Poziom trudności
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { key: 'easy', emoji: '🟢', label: 'Łatwy' },
                      { key: 'medium', emoji: '🟡', label: 'Średni' },
                      { key: 'hard', emoji: '🔴', label: 'Trudny' },
                    ].map((lvl) => (
                      <button
                        key={lvl.key}
                        type="button"
                        onClick={() => setDifficulty(lvl.key)}
                        className={`py-2 rounded-lg border-2 font-bold transition-all text-xs ${
                          difficulty === lvl.key
                            ? 'bg-indigo-600 text-white border-transparent'
                            : 'bg-gray-50 text-gray-800 border-gray-200 hover:border-indigo-400'
                        }`}
                        disabled={loading}
                      >
                        <div className="text-xl mb-0.5">{lvl.emoji}</div>
                        {lvl.label}
                      </button>
                    ))}
                  </div>
                  {useAdaptiveDifficulty && (
                    <div className="mt-2 bg-indigo-50 border-l-4 border-indigo-500 p-2 rounded-r-lg">
                      <p className="text-xs text-indigo-800">
                        <strong>Tryb adaptacyjny:</strong> Trudność dostosuje się do odpowiedzi.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="border-t pt-4">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="w-full flex items-center justify-between text-gray-800 font-bold text-sm mb-3 hover:text-indigo-600 transition-all"
              >
                <span>⚙️ Ustawienia zaawansowane</span>
                <span className="text-lg">{showAdvanced ? '▼' : '▶'}</span>
              </button>

              {showAdvanced && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 bg-gray-50 rounded-lg p-4 border border-gray-100">
                  <div>
                    <label className="block text-gray-700 font-semibold mb-1 text-sm">
                      Liczba pytań: <span className="text-indigo-600">{questionsCount}</span>
                    </label>
                    <input
                      type="range"
                      min="5"
                      max="20"
                      step="1"
                      value={questionsCount}
                      onChange={(e) => setQuestionsCount(Number(e.target.value))}
                      className="w-full h-1.5 bg-indigo-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                      disabled={loading}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-0.5">
                      <span>5</span>
                      <span>20</span>
                    </div>
                  </div>

                  <div>
                    <label className="block text-gray-700 font-semibold mb-1 text-sm">
                      Czas na pytanie: <span className="text-indigo-600">{timePerQuestion}s</span>
                    </label>
                    <input
                      type="range"
                      min="10"
                      max="60"
                      step="5"
                      value={timePerQuestion}
                      onChange={(e) => setTimePerQuestion(Number(e.target.value))}
                      className="w-full h-1.5 bg-indigo-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                      disabled={loading}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-0.5">
                      <span>10s</span>
                      <span>60s</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between bg-white rounded-lg p-3 border-2 border-gray-200">
                    <div>
                      <label className="text-gray-700 font-semibold cursor-pointer text-sm">
                        Tryb adaptacyjny
                      </label>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {useAdaptiveDifficulty ? 'Włączony' : 'Wyłączony'}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setUseAdaptiveDifficulty(!useAdaptiveDifficulty)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        useAdaptiveDifficulty ? 'bg-indigo-600' : 'bg-gray-300'
                      }`}
                      disabled={loading}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          useAdaptiveDifficulty ? 'translate-x-6' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="flex-1 py-3 rounded-lg border-2 border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition text-sm"
                disabled={loading}
              >
                Anuluj
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-3 rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold hover:from-indigo-700 hover:to-purple-700 shadow-md transition-all disabled:opacity-50 text-sm"
              >
                {loading ? 'Uruchamianie...' : 'Rozpocznij quiz 🚀'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </MainLayout>
  );
}