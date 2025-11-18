/**
 * Oblicza procent poprawnych odpowiedzi
 * @param {Object} quiz - Obiekt quizu z total_questions i correct_answers
 * @returns {number} - Procent (0-100)
 */
export const calculatePercentage = (quiz) => {
  if (!quiz.total_questions || quiz.total_questions === 0) return 0;
  return Math.round((quiz.correct_answers / quiz.total_questions) * 100);
};

/**
 * Zwraca czytelną etykietę dla poziomu wiedzy
 * @param {string} level - Klucz poziomu wiedzy
 * @returns {string} - Sformatowana etykieta z emoji
 */
export const getKnowledgeLevelLabel = (level) => {
  const labels = {
    elementary: '🎓 Podstawowy',
    high_school: '📚 Licealny',
    university: '🎓 Uniwersytecki',
    expert: '👨‍🔬 Ekspercki'
  };
  return labels[level] || level;
};

/**
 * Zwraca czytelną etykietę dla poziomu trudności
 * @param {string} difficulty - Klucz trudności
 * @returns {string} - Sformatowana etykieta
 */
export const getDifficultyLabel = (difficulty) => {
  const labels = {
    easy: '🟢 Łatwy',
    medium: '🟡 Średni',
    hard: '🔴 Trudny'
  };
  return labels[difficulty] || difficulty;
};

/**
 * Formatuje datę do czytelnego formatu
 * @param {string} dateString - Data w formacie ISO
 * @returns {string} - Sformatowana data (np. "15 listopada 2025, 14:30")
 */
export const formatDate = (dateString) => {
  if (!dateString) return '';

  const date = new Date(dateString);
  const options = {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  };

  return date.toLocaleDateString('pl-PL', options);
};

/**
 * Formatuje czas trwania w sekundach do formatu MM:SS
 * @param {number} seconds - Liczba sekund
 * @returns {string} - Sformatowany czas (np. "02:30")
 */
export const formatDuration = (seconds) => {
  if (!seconds || seconds < 0) return '00:00';

  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;

  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
};

/**
 * Zwraca kolor dla procentu poprawnych odpowiedzi
 * @param {number} percentage - Procent (0-100)
 * @returns {string} - Klasa Tailwind CSS dla koloru
 */
export const getScoreColor = (percentage) => {
  if (percentage >= 80) return 'text-green-600';
  if (percentage >= 60) return 'text-yellow-600';
  if (percentage >= 40) return 'text-orange-600';
  return 'text-red-600';
};

/**
 * Zwraca gradient dla procentu poprawnych odpowiedzi
 * @param {number} percentage - Procent (0-100)
 * @returns {string} - Klasa Tailwind CSS dla gradientu
 */
export const getScoreGradient = (percentage) => {
  if (percentage >= 80) return 'from-green-400 to-green-600';
  if (percentage >= 60) return 'from-yellow-400 to-yellow-600';
  if (percentage >= 40) return 'from-orange-400 to-orange-600';
  return 'from-red-400 to-red-600';
};