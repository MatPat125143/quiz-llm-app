import { useState, useEffect } from 'react';
import { startQuiz, getCurrentUser } from '../services/api';
import { useNavigate } from 'react-router-dom';
import Layout from './Layout';

export default function QuizSetup() {
  const [user, setUser] = useState(null);
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const [questionsCount, setQuestionsCount] = useState(10);
  const [timePerQuestion, setTimePerQuestion] = useState(30);
  const [useAdaptiveDifficulty, setUseAdaptiveDifficulty] = useState(true);

  const navigate = useNavigate();

  useEffect(() => {
    (async () => {
      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (err) {
        console.error('Error loading user:', err);
      }
    })();
  }, []);

  const predefinedTopics = [
    'Język polski',
    'Matematyka',
    'Historia',
    'Geografia',
    'Biologia',
    'Chemia',
    'Fizyka',
    'Wiedza o społeczeństwie',
    'Język angielski',
  ];

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
        useAdaptiveDifficulty
      );
      navigate(`/quiz/play/${response.session_id}`);
    } catch (err) {
      console.error(err);
      setError('Nie udało się uruchomić quizu. Spróbuj ponownie.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout user={user}>
      <div className="max-w-5xl mx-auto px-6 py-10">
        <div className="bg-white rounded-2xl shadow-lg border border-gray-100 p-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2 flex items-center gap-2">
            🎯 Rozpocznij nowy quiz
          </h1>
          <p className="text-gray-600 mb-6">
            Wybierz temat, poziom trudności i rozpocznij quiz dopasowany do Twojego stylu nauki.
          </p>

          {error && (
            <div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded-xl mb-6">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Temat quizu */}
            <div>
              <label className="block text-lg font-bold text-gray-800 mb-3">
                Temat quizu
              </label>
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Wprowadź własny temat lub wybierz poniżej"
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:outline-none focus:border-indigo-500 transition-all"
                disabled={loading}
              />
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-3 font-semibold">
                  Lub wybierz popularny temat:
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  {predefinedTopics.map((t) => (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setTopic(t)}
                      className={`px-4 py-2 rounded-xl border-2 font-semibold text-sm transition-all ${
                        topic === t
                          ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-transparent shadow-md'
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

            {/* Poziom trudności */}
            <div>
              <label className="block text-lg font-bold text-gray-800 mb-3">
                Poziom trudności
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {[
                  { key: 'easy', emoji: '🟢', label: 'Łatwy' },
                  { key: 'medium', emoji: '🟡', label: 'Średni' },
                  { key: 'hard', emoji: '🔴', label: 'Trudny' },
                ].map((lvl) => (
                  <button
                    key={lvl.key}
                    type="button"
                    onClick={() => setDifficulty(lvl.key)}
                    className={`py-4 rounded-xl border-2 font-bold transition-all ${
                      difficulty === lvl.key
                        ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-transparent shadow-md scale-105'
                        : 'bg-gray-50 text-gray-800 border-gray-200 hover:border-indigo-400'
                    }`}
                    disabled={loading}
                  >
                    <div className="text-3xl mb-1">{lvl.emoji}</div>
                    {lvl.label}
                  </button>
                ))}
              </div>
              {useAdaptiveDifficulty && (
                <div className="mt-4 bg-indigo-50 border-l-4 border-indigo-500 p-4 rounded-r-xl">
                  <p className="text-sm text-indigo-800">
                    ℹ️ <strong>Tryb adaptacyjny:</strong> Quiz automatycznie dopasuje trudność do Twoich odpowiedzi.
                  </p>
                </div>
              )}
            </div>

            {/* Zaawansowane ustawienia */}
            <div className="border-t pt-6">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="w-full flex items-center justify-between text-gray-800 font-bold text-lg mb-4 hover:text-indigo-600 transition-all"
              >
                <span>⚙️ Ustawienia zaawansowane</span>
                <span className="text-2xl">{showAdvanced ? '▼' : '▶'}</span>
              </button>

              {showAdvanced && (
                <div className="space-y-6 bg-gray-50 rounded-xl p-6 border border-gray-100">
                  {/* Liczba pytań */}
                  <div>
                    <label className="block text-gray-700 font-semibold mb-2">
                      Liczba pytań: <span className="text-indigo-600">{questionsCount}</span>
                    </label>
                    <input
                      type="range"
                      min="5"
                      max="20"
                      step="1"
                      value={questionsCount}
                      onChange={(e) => setQuestionsCount(Number(e.target.value))}
                      className="w-full h-2 bg-indigo-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                      disabled={loading}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>5</span>
                      <span>20</span>
                    </div>
                  </div>

                  {/* Czas na pytanie */}
                  <div>
                    <label className="block text-gray-700 font-semibold mb-2">
                      Czas na pytanie: <span className="text-indigo-600">{timePerQuestion}s</span>
                    </label>
                    <input
                      type="range"
                      min="10"
                      max="60"
                      step="5"
                      value={timePerQuestion}
                      onChange={(e) => setTimePerQuestion(Number(e.target.value))}
                      className="w-full h-2 bg-indigo-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                      disabled={loading}
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>10s</span>
                      <span>60s</span>
                    </div>
                  </div>

                  {/* Tryb adaptacyjny */}
                  <div className="flex items-center justify-between bg-white rounded-xl p-4 border-2 border-gray-200">
                    <div>
                      <label className="text-gray-700 font-semibold cursor-pointer">
                        Tryb adaptacyjny
                      </label>
                      <p className="text-xs text-gray-500 mt-1">
                        {useAdaptiveDifficulty
                          ? 'Poziom trudności będzie się zmieniał dynamicznie.'
                          : 'Quiz zachowa wybrany poziom przez cały czas.'}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setUseAdaptiveDifficulty(!useAdaptiveDifficulty)}
                      className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
                        useAdaptiveDifficulty ? 'bg-indigo-600' : 'bg-gray-300'
                      }`}
                      disabled={loading}
                    >
                      <span
                        className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                          useAdaptiveDifficulty ? 'translate-x-7' : 'translate-x-1'
                        }`}
                      />
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Przyciski */}
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                type="button"
                onClick={() => navigate('/dashboard')}
                className="flex-1 py-4 rounded-xl border-2 border-gray-300 text-gray-700 font-semibold hover:bg-gray-100 transition"
                disabled={loading}
              >
                Anuluj
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold hover:from-indigo-700 hover:to-purple-700 shadow-md transition-all disabled:opacity-50"
              >
                {loading ? 'Uruchamianie quizu...' : 'Rozpocznij quiz 🚀'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
}
