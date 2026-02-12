export const KNOWLEDGE_LEVELS = [
    {key: 'elementary', label: 'Szkoła Podstawowa', shortLabel: 'Szkoła Podstawowa', emoji: '🏫'},
    {key: 'high_school', label: 'Liceum', shortLabel: 'Liceum', emoji: '🎓'},
    {key: 'university', label: 'Studia', shortLabel: 'Studia', emoji: '🏛️'},
    {key: 'expert', label: 'Ekspert', shortLabel: 'Ekspert', emoji: '⭐'},
];

export const DIFFICULTY_LEVELS = [
    {key: 'easy', apiValue: 'łatwy', emoji: '🟢', label: 'Łatwy'},
    {key: 'medium', apiValue: 'średni', emoji: '🟡', label: 'Średni'},
    {key: 'hard', apiValue: 'trudny', emoji: '🔴', label: 'Trudny'},
];

export const QUESTION_DIFFICULTY_LEVELS = DIFFICULTY_LEVELS.map(({apiValue, emoji, label}) => ({
    key: apiValue,
    emoji,
    label,
}));

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
    Matematyka: ['Algebra', 'Geometria', 'Trygonometria', 'Analiza matematyczna', 'Statystyka', 'Wielomiany', 'Funkcje'],
    Fizyka: ['Mechanika', 'Termodynamika', 'Elektryczność', 'Magnetyzm', 'Optyka', 'Fizyka jądrowa'],
    Chemia: ['Chemia organiczna', 'Chemia nieorganiczna', 'Chemia fizyczna', 'Biochemia', 'Stechiometria'],
    Biologia: ['Genetyka', 'Ekologia', 'Anatomia', 'Fizjologia', 'Ewolucja', 'Botanika', 'Zoologia'],
    Historia: ['Starożytność', 'Średniowiecze', 'Nowożytność', 'Historia Polski', 'Historia powszechna', 'XX wiek'],
    Geografia: ['Geografia fizyczna', 'Geografia społeczno-ekonomiczna', 'Klimatologia', 'Geologia'],
    'Język polski': ['Literatura', 'Gramatyka', 'Ortografia', 'Lektury', 'Części mowy', 'Składnia'],
    'Język angielski': ['Gramatyka', 'Słownictwo', 'Czasy gramatyczne', 'Phrasal verbs', 'Idiomy'],
    'Wiedza o społeczeństwie': ['Prawo', 'Polityka', 'Ekonomia', 'Socjologia', 'Prawa człowieka'],
};


export const QUIZ_DEFAULTS = {
    QUESTIONS_COUNT: 10,
    TIME_PER_QUESTION: 30,
    USE_ADAPTIVE_DIFFICULTY: true,
    DIFFICULTY: 'medium',
    KNOWLEDGE_LEVEL: 'high_school',
};

