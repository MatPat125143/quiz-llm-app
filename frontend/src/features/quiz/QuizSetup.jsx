import {useState, useEffect} from 'react';
import {useNavigate, useLocation} from 'react-router-dom';
import MainLayout from '../../layouts/MainLayout';
import useCurrentUser from '../../hooks/useCurrentUser';
import {
    PREDEFINED_TOPICS, TOPIC_SUBTOPICS, KNOWLEDGE_LEVELS, DIFFICULTY_LEVELS, QUIZ_DEFAULTS
} from '../../services/constants';

export default function QuizSetup() {
    const location = useLocation();
    const replayParams = location.state?.replayParams || null;
    const { user } = useCurrentUser();
    const [topic, setTopic] = useState(replayParams?.topic || '');
    const [subtopic, setSubtopic] = useState(replayParams?.subtopic || '');
    const [knowledgeLevel, setKnowledgeLevel] = useState(replayParams?.knowledgeLevel || QUIZ_DEFAULTS.KNOWLEDGE_LEVEL);
    const [difficulty, setDifficulty] = useState(replayParams?.difficulty || QUIZ_DEFAULTS.DIFFICULTY);
    const loading = false;
    const [error, setError] = useState('');
    const [showAdvanced, setShowAdvanced] = useState(false);

    const [questionsCount, setQuestionsCount] = useState(replayParams?.questionsCount ?? QUIZ_DEFAULTS.QUESTIONS_COUNT);
    const [timePerQuestion, setTimePerQuestion] = useState(replayParams?.timePerQuestion ?? QUIZ_DEFAULTS.TIME_PER_QUESTION);
    const [useAdaptiveDifficulty, setUseAdaptiveDifficulty] = useState(replayParams?.useAdaptiveDifficulty ?? QUIZ_DEFAULTS.USE_ADAPTIVE_DIFFICULTY);

    const navigate = useNavigate();

    const difficultyDesc = {
        easy: 'Na rozgrzewkę', medium: 'W sam raz', hard: 'Dla ambitnych',
    };

    const suggestedSubtopics = topic && TOPIC_SUBTOPICS[topic] ? TOPIC_SUBTOPICS[topic].slice(0, 6) : [];

    useEffect(() => {
        if (!user) return;
        if (!replayParams?.knowledgeLevel && user.profile?.default_knowledge_level) {
            setKnowledgeLevel(user.profile.default_knowledge_level);
        }
    }, [replayParams?.knowledgeLevel, user]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!topic.trim()) {
            setError('Proszę wprowadzić lub wybrać temat.');
            return;
        }

        setError('');

        navigate('/quiz/play', {
            state: {
                startParams: {
                    topic, difficulty, questionsCount, timePerQuestion, useAdaptiveDifficulty, subtopic, knowledgeLevel
                }
            }
        });
    };

    return (<MainLayout user={user}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 sm:py-8">
            <div
                className="mb-8 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 rounded-2xl p-8 text-white shadow-xl">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold flex items-center gap-2">🎯 Rozpocznij nowy quiz</h1>
                        <p className="text-indigo-200 mt-1 text-lg">Ustaw temat i parametry gry — resztą zajmie się
                            AI.</p>
                    </div>
                    <div className="hidden md:block text-8xl opacity-20">🎯</div>
                </div>
            </div>

            <div
                className="bg-white dark:bg-slate-900 rounded-xl shadow-lg border border-gray-100 dark:border-slate-800 p-4 sm:p-6">

                <div
                    className="bg-blue-50 dark:bg-slate-900 border-2 border-blue-300 dark:border-blue-600 px-4 sm:px-6 py-4 sm:py-5 rounded-2xl mb-5 shadow-sm">
                    <p className="text-sm sm:text-base text-blue-900 dark:text-blue-100 leading-relaxed">
                        <strong>ℹ️ Informacja:</strong> Pytania generowane są przez sztuczną inteligencję. AI nie
                        jest doskonałe i może sporadycznie tworzyć pytania zawierające błędy lub nieścisłości.
                        Prosimy o wyrozumiałość.
                    </p>
                </div>

                {error && (<div className="bg-red-50 border border-red-400 text-red-700 px-4 py-3 rounded-xl mb-4">
                    {error}
                </div>)}

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-6">
                        <div className="space-y-6">
                            <div className="space-y-5">
                                <div>
                                    <label className="block text-base font-bold text-gray-800 mb-2">
                                        Temat quizu
                                    </label>
                                    <div className="flex items-stretch gap-2">
                                        <input
                                            type="text"
                                            value={topic}
                                            onChange={(e) => setTopic(e.target.value)}
                                            placeholder="Wprowadź własny temat lub wybierz poniżej"
                                            className="ui-input flex-1 text-base dark:placeholder:text-slate-400"
                                            disabled={loading}
                                        />
                                        <button
                                            type="button"
                                            onClick={() => {
                                                setTopic('');
                                                setSubtopic('');
                                            }}
                                            className="shrink-0 px-4 py-3 bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-700 transition font-semibold text-sm whitespace-nowrap flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                            disabled={loading || !topic.trim()}
                                        >
                                            🗑️ Wyczyść
                                        </button>
                                    </div>
                                    <div className="mt-3">
                                        <p className="text-xs text-gray-600 mb-2 font-semibold">
                                            Lub wybierz popularny temat:
                                        </p>
                                        <div
                                            className="max-w-[760px] mx-auto grid grid-cols-2 sm:grid-cols-3 gap-2">
                                            {PREDEFINED_TOPICS.map((t, idx) => (<button
                                                key={t}
                                                type="button"
                                                onClick={() => {
                                                    if (topic === t) {
                                                        setTopic('');
                                                        setSubtopic('');
                                                        return;
                                                    }
                                                    setTopic(t);
                                                    setSubtopic('');
                                                }}
                                                className={`w-full min-h-[56px] sm:min-h-[76px] px-2.5 py-2 rounded-xl border-2 font-semibold text-[13px] sm:text-sm transition-all flex items-center justify-center ${PREDEFINED_TOPICS.length % 2 === 1 && idx === PREDEFINED_TOPICS.length - 1 ? 'col-span-2 sm:col-span-1 w-1/2 sm:w-full justify-self-center sm:justify-self-auto' : ''} ${PREDEFINED_TOPICS.length % 3 === 1 && idx === PREDEFINED_TOPICS.length - 1 ? 'sm:col-start-2' : ''} ${topic === t ? 'bg-indigo-600 text-white border-transparent' : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-400 dark:bg-slate-900 dark:text-slate-200 dark:border-slate-700 dark:hover:border-indigo-500'}`}
                                                disabled={loading}
                                            >
                                                <span className="block text-center leading-snug">{t}</span>
                                            </button>))}
                                        </div>
                                    </div>
                                </div>

                                {topic && TOPIC_SUBTOPICS[topic] && (<div>
                                    <label className="block text-base font-bold text-gray-800 mb-2">
                                        Podtemat (opcjonalnie)
                                    </label>
                                    <div className="flex items-stretch gap-2 mb-2">
                                        <input
                                            type="text"
                                            value={subtopic}
                                            onChange={(e) => setSubtopic(e.target.value)}
                                            placeholder="Wprowadź własny podtemat"
                                            className="ui-input flex-1 text-base dark:placeholder:text-slate-400"
                                            disabled={loading}
                                        />
                                        <button
                                            type="button"
                                            onClick={() => setSubtopic('')}
                                            className="shrink-0 px-4 py-3 bg-gray-100 text-gray-700 dark:bg-slate-800 dark:text-slate-200 rounded-xl hover:bg-gray-200 dark:hover:bg-slate-700 transition font-semibold text-sm whitespace-nowrap flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                            disabled={loading || !subtopic.trim()}
                                        >
                                            🗑️ Wyczyść
                                        </button>
                                    </div>
                                    <p className="text-xs text-gray-600 mb-2 font-semibold">
                                        Lub wybierz popularny podtemat:
                                    </p>
                                    <div className="space-y-2">
                                        {suggestedSubtopics.length === 5 ? (<>
                                            <div
                                                className="max-w-[760px] mx-auto grid grid-cols-2 sm:grid-cols-6 gap-2">
                                                {suggestedSubtopics.map((sub, idx) => (<button
                                                    key={sub}
                                                    type="button"
                                                    onClick={() => setSubtopic((prev) => (prev === sub ? '' : sub))}
                                                    className={`${suggestedSubtopics.length % 2 === 1 && idx === suggestedSubtopics.length - 1 ? 'col-span-2 sm:col-span-2 w-1/2 sm:w-full justify-self-center sm:justify-self-auto' : 'col-span-1 sm:col-span-2'} min-h-[56px] sm:min-h-[76px] px-2.5 py-2 rounded-xl border-2 text-[13px] sm:text-sm font-semibold transition-all flex items-center justify-center ${subtopic === sub ? 'bg-indigo-100 border-indigo-500 text-indigo-700' : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-300 dark:bg-slate-900 dark:text-slate-200 dark:border-slate-700 dark:hover:border-indigo-500'} ${idx < 3 ? '' : idx === 3 ? 'sm:col-start-2' : 'sm:col-start-4'}`}
                                                    disabled={loading}
                                                >
                                                                    <span
                                                                        className="block text-center leading-snug">{sub}</span>
                                                </button>))}
                                            </div>
                                        </>) : (<div
                                            className="max-w-[760px] mx-auto grid grid-cols-2 sm:grid-cols-3 gap-2">
                                            {suggestedSubtopics.map((sub, idx) => (<button
                                                key={sub}
                                                type="button"
                                                onClick={() => setSubtopic((prev) => (prev === sub ? '' : sub))}
                                                className={`w-full min-h-[56px] sm:min-h-[76px] px-2.5 py-2 rounded-xl border-2 text-[13px] sm:text-sm font-semibold transition-all flex items-center justify-center ${suggestedSubtopics.length % 2 === 1 && idx === suggestedSubtopics.length - 1 ? 'col-span-2 sm:col-span-1 w-1/2 sm:w-full justify-self-center sm:justify-self-auto' : ''} ${suggestedSubtopics.length % 3 === 1 && idx === suggestedSubtopics.length - 1 ? 'sm:col-start-2' : ''} ${subtopic === sub ? 'bg-indigo-100 border-indigo-500 text-indigo-700' : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-300 dark:bg-slate-900 dark:text-slate-200 dark:border-slate-700 dark:hover:border-indigo-500'}`}
                                                disabled={loading}
                                            >
                                                                <span
                                                                    className="block text-center leading-snug">{sub}</span>
                                            </button>))}
                                        </div>)}
                                    </div>
                                </div>)}
                            </div>

                            <div className="space-y-5">

                                <div>
                                    <label className="block text-base font-bold text-gray-800 mb-2">
                                        Poziom trudności
                                    </label>
                                    <div className="max-w-[760px] mx-auto grid grid-cols-2 sm:grid-cols-3 gap-2">
                                        {DIFFICULTY_LEVELS.map((lvl, idx) => (<button
                                            key={lvl.key}
                                            type="button"
                                            onClick={() => setDifficulty(lvl.key)}
                                            className={`w-full min-h-[56px] sm:min-h-[76px] px-2.5 py-2 rounded-xl border-2 font-semibold text-[13px] sm:text-sm transition-all flex items-center justify-center ${DIFFICULTY_LEVELS.length % 2 === 1 && idx === DIFFICULTY_LEVELS.length - 1 ? 'col-span-2 sm:col-span-1 w-1/2 sm:w-full justify-self-center sm:justify-self-auto' : ''} ${difficulty === lvl.key ? 'bg-indigo-600 text-white border-transparent' : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-400 dark:bg-slate-900 dark:text-slate-200 dark:border-slate-700 dark:hover:border-indigo-500'}`}
                                            disabled={loading}
                                        >
                                            <div className="text-center leading-snug">
                                                <div>{lvl.emoji} {lvl.label}</div>
                                                <div
                                                    className={`text-[11px] mt-0.5 ${difficulty === lvl.key ? 'text-indigo-100' : 'text-gray-500 dark:text-slate-400'}`}>
                                                    {difficultyDesc[lvl.key] || ''}
                                                </div>
                                            </div>
                                        </button>))}
                                    </div>

                                    <div className="mt-3 max-w-[760px] mx-auto">
                                        <button
                                            type="button"
                                            onClick={() => setUseAdaptiveDifficulty(!useAdaptiveDifficulty)}
                                            className={`w-full min-h-[56px] sm:min-h-[76px] px-3 py-2 rounded-xl border-2 font-semibold text-[13px] sm:text-sm transition-all flex items-center justify-center ${useAdaptiveDifficulty ? 'bg-indigo-600 text-white border-transparent shadow-lg shadow-indigo-500/30 ring-2 ring-indigo-300/60' : 'bg-white text-gray-700 border-gray-300 hover:border-indigo-400 dark:bg-slate-900 dark:text-slate-200 dark:border-slate-700 dark:hover:border-indigo-500'}`}
                                            disabled={loading}
                                        >
                                            {useAdaptiveDifficulty ? '✨ Tryb adaptacyjny: Włączony' : 'Tryb adaptacyjny: Wyłączony'}
                                        </button>
                                    </div>

                                    {useAdaptiveDifficulty && (<div
                                        className="mt-3 bg-indigo-50 dark:bg-slate-900 border-2 border-indigo-300 dark:border-indigo-600 px-4 py-3 rounded-2xl shadow-sm">
                                        <p className="text-sm sm:text-base text-indigo-800 dark:text-indigo-200">
                                            <strong>Tryb adaptacyjny:</strong> Trudność dostosuje się do
                                            odpowiedzi.
                                        </p>
                                    </div>)}
                                </div>
                            </div>
                        </div>

                        <div className="border-t pt-4">
                            <button
                                type="button"
                                onClick={() => setShowAdvanced(!showAdvanced)}
                                className="w-full flex items-center justify-between text-gray-800 dark:text-slate-100 font-bold text-sm mb-3 hover:text-indigo-600 dark:hover:text-indigo-300 transition-all"
                            >
                                <span>⚙️ Ustawienia zaawansowane</span>
                                <span
                                    className={`inline-flex transition-transform duration-300 ${showAdvanced ? 'rotate-180' : ''}`}>
                  <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m6 9 6 6 6-6"/>
                  </svg>
                </span>
                            </button>

                            {showAdvanced && (<div
                                className="grid grid-cols-1 lg:grid-cols-3 gap-4 bg-gray-50 dark:bg-slate-800 rounded-lg p-4 border border-gray-100 dark:border-slate-700">
                                <div>
                                    <label
                                        className="block text-gray-700 dark:text-slate-200 font-semibold mb-1 text-sm">
                                        Poziom wiedzy
                                    </label>
                                    <select
                                        value={knowledgeLevel}
                                        onChange={(e) => {
                                            setKnowledgeLevel(e.target.value);
                                        }}
                                        className="ui-select text-sm"
                                        disabled={loading}
                                    >
                                        {KNOWLEDGE_LEVELS.map((k) => (<option key={k.key} value={k.key}>
                                            {k.emoji} {k.label}
                                        </option>))}
                                    </select>
                                    <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">
                                        Domyślnie ustawione na podstawie Twojego profilu.
                                    </p>
                                </div>

                                <div>
                                    <label
                                        className="block text-gray-700 dark:text-slate-200 font-semibold mb-1 text-sm">
                                        Liczba pytań: <span className="text-indigo-600">{questionsCount}</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="5"
                                        max="20"
                                        step="1"
                                        value={questionsCount}
                                        onChange={(e) => {
                                            setQuestionsCount(Number(e.target.value));
                                        }}
                                        className="ui-range"
                                        disabled={loading}
                                    />
                                    <div
                                        className="flex justify-between text-xs text-gray-500 dark:text-slate-400 mt-0.5">
                                        <span>5</span>
                                        <span>20</span>
                                    </div>
                                </div>

                                <div>
                                    <label
                                        className="block text-gray-700 dark:text-slate-200 font-semibold mb-1 text-sm">
                                        Czas na pytanie: <span
                                        className="text-indigo-600">{timePerQuestion}s</span>
                                    </label>
                                    <input
                                        type="range"
                                        min="10"
                                        max="60"
                                        step="5"
                                        value={timePerQuestion}
                                        onChange={(e) => {
                                            setTimePerQuestion(Number(e.target.value));
                                        }}
                                        className="ui-range"
                                        disabled={loading}
                                    />
                                    <div
                                        className="flex justify-between text-xs text-gray-500 dark:text-slate-400 mt-0.5">
                                        <span>10s</span>
                                        <span>60s</span>
                                    </div>
                                </div>

                            </div>)}
                        </div>

                        <div className="pt-2">
                            <button
                                type="submit"
                                disabled={loading}
                                className="w-full py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold hover:from-indigo-700 hover:to-purple-700 shadow-lg transition-all disabled:opacity-50 text-base"
                            >
                                {loading ? 'Uruchamianie...' : 'Rozpocznij quiz 🚀'}
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </MainLayout>);
}

