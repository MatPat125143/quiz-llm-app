import {DIFFICULTY_LEVELS, KNOWLEDGE_LEVELS, QUESTION_DIFFICULTY_LEVELS} from './constants';

const knowledgeMetaByKey = Object.fromEntries(KNOWLEDGE_LEVELS.map((k) => [k.key, k]));
const difficultyMetaByKey = Object.fromEntries(
    DIFFICULTY_LEVELS.flatMap((d) => {
        const entries = [[d.key, d]];
        if (d.apiValue) entries.push([d.apiValue, d]);
        return entries;
    })
);


export const calculatePercentage = (quiz) => {
    if (!quiz.total_questions || quiz.total_questions === 0) return 0;
    return Math.round((quiz.correct_answers / quiz.total_questions) * 100);
};


export const getKnowledgeLevelLabel = (level) => {
    return knowledgeMetaByKey[level]?.label || level;
};


export const getKnowledgeLevelShortLabel = (level) => {
    return knowledgeMetaByKey[level]?.shortLabel || getKnowledgeLevelLabel(level);
};


export const getKnowledgeLevelEmoji = (level) => {
    return knowledgeMetaByKey[level]?.emoji || '';
};


export const getKnowledgeBadgeLabel = (level) => {
    const meta = knowledgeMetaByKey[level];
    if (!meta) return level;
    return `${meta.emoji} ${meta.label}`;
};


export const getDifficultyLabel = (difficulty) => {
    return difficultyMetaByKey[difficulty]?.label || difficulty;
};

const normalizeDifficulty = (difficulty = '') =>
    difficulty
        .toString()
        .trim()
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');

const difficultyBadgeByNormalizedKey = (() => {
    const map = new Map();
    [...DIFFICULTY_LEVELS, ...QUESTION_DIFFICULTY_LEVELS].forEach((item) => {
        map.set(normalizeDifficulty(item.key), `${item.emoji} ${item.label}`);
    });
    return map;
})();


export const getDifficultyBadgeLabel = (difficulty) => {
    const key = normalizeDifficulty(difficulty);
    return difficultyBadgeByNormalizedKey.get(key) || '🔴 Trudny';
};


export const getDifficultyBadgeClass = (difficulty) => {
    const key = normalizeDifficulty(difficulty);
    if (['easy', 'latwy', 'łatwy'].includes(key)) {
        return 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-200';
    }
    if (['medium', 'sredni'].includes(key)) {
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-200';
    }
    return 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-200';
};


export const getKnowledgeBadgeClass = () =>
    'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/40 dark:text-indigo-200';


export const getAdaptiveBadgeClass = () =>
    'bg-cyan-100 text-cyan-800 border border-cyan-200 dark:bg-cyan-900/30 dark:text-cyan-200 dark:border-cyan-700/50';


export const formatDate = (dateString) => {
    if (!dateString) return '';

    const date = new Date(dateString);
    const options = {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    };

    return date.toLocaleDateString('pl-PL', options);
};


export const formatDuration = (seconds) => {
    if (!seconds || seconds < 0) return '00:00';

    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;

    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

export const formatQuizDuration = (
    startedAt,
    endedAt,
    totalQuestions = 0,
    timePerQuestion = 0
) => {
    let totalSeconds = 0;

    if (startedAt && endedAt) {
        const start = new Date(startedAt);
        const end = new Date(endedAt);
        if (!Number.isNaN(start.getTime()) && !Number.isNaN(end.getTime())) {
            totalSeconds = Math.max(0, Math.floor((end - start) / 1000));
        }
    } else if (totalQuestions && timePerQuestion) {
        totalSeconds = Math.max(0, Math.floor(Number(totalQuestions) * Number(timePerQuestion)));
    }

    const minutes = Math.floor(totalSeconds / 60);
    const seconds = totalSeconds % 60;
    return `${minutes} min ${seconds.toString().padStart(2, '0')} s`;
};

