/**
 * Quiz topics and categories
 */

export const QUIZ_TOPICS = [
  { value: 'Python', label: '🐍 Python', category: 'programming' },
  { value: 'JavaScript', label: '💛 JavaScript', category: 'programming' },
  { value: 'Java', label: '☕ Java', category: 'programming' },
  { value: 'C++', label: '⚙️ C++', category: 'programming' },
  { value: 'React', label: '⚛️ React', category: 'programming' },
  { value: 'Django', label: '🎸 Django', category: 'programming' },
  { value: 'SQL', label: '🗄️ SQL', category: 'programming' },
  { value: 'Data Structures', label: '📊 Struktury Danych', category: 'computer-science' },
  { value: 'Algorithms', label: '🧮 Algorytmy', category: 'computer-science' },
  { value: 'Machine Learning', label: '🤖 Machine Learning', category: 'ai' },
  { value: 'Deep Learning', label: '🧠 Deep Learning', category: 'ai' },
  { value: 'Mathematics', label: '➗ Matematyka', category: 'science' },
  { value: 'Physics', label: '⚛️ Fizyka', category: 'science' },
  { value: 'Chemistry', label: '🧪 Chemia', category: 'science' },
  { value: 'Biology', label: '🧬 Biologia', category: 'science' },
  { value: 'History', label: '📜 Historia', category: 'humanities' },
  { value: 'Geography', label: '🗺️ Geografia', category: 'humanities' },
  { value: 'English', label: '🇬🇧 Język Angielski', category: 'language' },
];

export const TOPIC_CATEGORIES = {
  programming: { label: 'Programowanie', icon: '💻' },
  'computer-science': { label: 'Informatyka', icon: '🖥️' },
  ai: { label: 'Sztuczna Inteligencja', icon: '🤖' },
  science: { label: 'Nauki Ścisłe', icon: '🔬' },
  humanities: { label: 'Nauki Humanistyczne', icon: '📚' },
  language: { label: 'Języki', icon: '🗣️' },
};

/**
 * Get topics by category
 */
export const getTopicsByCategory = (category) => {
  return QUIZ_TOPICS.filter(topic => topic.category === category);
};

/**
 * Get all unique categories
 */
export const getAllCategories = () => {
  return Object.keys(TOPIC_CATEGORIES);
};
