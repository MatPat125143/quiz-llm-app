DEFAULT_QUESTIONS_COUNT = 10
DEFAULT_TIME_PER_QUESTION = 30
DEFAULT_USE_ADAPTIVE_DIFFICULTY = True

QUESTIONS_COUNT_MIN = 5
QUESTIONS_COUNT_MAX = 20
TIME_PER_QUESTION_MIN = 10
TIME_PER_QUESTION_MAX = 60

DIFFICULTY_NAME_MAP = {
    "easy": "łatwy",
    "medium": "średni",
    "hard": "trudny",
}

DIFFICULTY_VALUE_MAP = {
    "easy": 2.0,
    "medium": 5.0,
    "hard": 8.0,
}

DIFFICULTY_ALIAS_MAP = {
    "łatwy": "easy",
    "latwy": "easy",
    "easy": "easy",
    "średni": "medium",
    "sredni": "medium",
    "medium": "medium",
    "trudny": "hard",
    "hard": "hard",
}

SYNC_QUESTION_COUNT = 3
BACKGROUND_BATCH_SIZE = 5
GENERATION_BUFFER_RATIO = 1.1
GENERATION_BUFFER_MIN_EXTRA = 1
QUESTION_WAIT_MAX_SECONDS = 2
QUESTION_WAIT_POLL_SECONDS = 0.2
