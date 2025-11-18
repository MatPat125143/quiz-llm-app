// ==================== QUIZ CONSTANTS ====================

export const KNOWLEDGE_LEVELS = [
  { key: 'elementary', label: 'Szkoła podstawowa', emoji: '📚' },
  { key: 'high_school', label: 'Liceum', emoji: '🎓' },
  { key: 'university', label: 'Studia', emoji: '🎯' },
  { key: 'expert', label: 'Ekspert', emoji: '🏆' },
];

export const DIFFICULTY_LEVELS = [
  { key: 'easy', emoji: '🟢', label: 'Łatwy' },
  { key: 'medium', emoji: '🟡', label: 'Średni' },
  { key: 'hard', emoji: '🔴', label: 'Trudny' },
];

export const PREDEFINED_TOPICS = [
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

export const TOPIC_SUBTOPICS = {
  'Matematyka': ['Algebra', 'Geometria', 'Trygonometria', 'Analiza matematyczna', 'Statystyka', 'Wielomiany', 'Funkcje'],
  'Fizyka': ['Mechanika', 'Termodynamika', 'Elektryczność', 'Magnetyzm', 'Optyka', 'Fizyka jądrowa'],
  'Chemia': ['Chemia organiczna', 'Chemia nieorganiczna', 'Chemia fizyczna', 'Biochemia', 'Stechiometria'],
  'Biologia': ['Genetyka', 'Ekologia', 'Anatomia', 'Fizjologia', 'Ewolucja', 'Botanika', 'Zoologia'],
  'Historia': ['Starożytność', 'Średniowiecze', 'Nowożytność', 'Historia Polski', 'Historia powszechna', 'XX wiek'],
  'Geografia': ['Geografia fizyczna', 'Geografia społeczno-ekonomiczna', 'Klimatologia', 'Geologia'],
  'Język polski': ['Literatura', 'Gramatyka', 'Ortografia', 'Lektury', 'Części mowy', 'Składnia'],
  'Język angielski': ['Gramatyka', 'Słownictwo', 'Czasy gramatyczne', 'Phrasal verbs', 'Idiomy'],
  'Wiedza o społeczeństwie': ['Prawo', 'Polityka', 'Ekonomia', 'Socjologia', 'Prawa człowieka'],
};

// ==================== USER ROLE CONSTANTS ====================

export const USER_ROLES = {
  USER: 'user',
  ADMIN: 'admin',
};

// ==================== QUIZ DEFAULT SETTINGS ====================

export const QUIZ_DEFAULTS = {
  QUESTIONS_COUNT: 10,
  TIME_PER_QUESTION: 30,
  USE_ADAPTIVE_DIFFICULTY: true,
  DIFFICULTY: 'medium',
  KNOWLEDGE_LEVEL: 'high_school',
};