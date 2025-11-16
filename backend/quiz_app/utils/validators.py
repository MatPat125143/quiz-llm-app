from core.exceptions import ValidationException

DIFFICULTY_CHOICES = ['easy', 'medium', 'hard']
KNOWLEDGE_LEVEL_CHOICES = ['elementary', 'high_school', 'university', 'expert']

MIN_QUESTIONS_COUNT = 1
MAX_QUESTIONS_COUNT = 50
MIN_TIME_PER_QUESTION = 10
MAX_TIME_PER_QUESTION = 300


def validate_quiz_parameters(data):
    errors = {}

    topic = data.get('topic', '').strip()
    if not topic:
        errors['topic'] = 'Temat jest wymagany'
    elif len(topic) < 2:
        errors['topic'] = 'Temat musi mieć co najmniej 2 znaki'
    elif len(topic) > 200:
        errors['topic'] = 'Temat nie może przekraczać 200 znaków'

    difficulty = data.get('difficulty')
    if not difficulty:
        errors['difficulty'] = 'Poziom trudności jest wymagany'
    elif difficulty not in DIFFICULTY_CHOICES:
        errors['difficulty'] = f'Poziom trudności musi być jedną z wartości: {", ".join(DIFFICULTY_CHOICES)}'

    questions_count = data.get('questions_count')
    if questions_count is None:
        errors['questions_count'] = 'Liczba pytań jest wymagana'
    else:
        try:
            questions_count = int(questions_count)
            if questions_count < MIN_QUESTIONS_COUNT:
                errors['questions_count'] = f'Liczba pytań musi wynosić co najmniej {MIN_QUESTIONS_COUNT}'
            elif questions_count > MAX_QUESTIONS_COUNT:
                errors['questions_count'] = f'Liczba pytań nie może przekraczać {MAX_QUESTIONS_COUNT}'
        except (ValueError, TypeError):
            errors['questions_count'] = 'Liczba pytań musi być liczbą całkowitą'

    time_per_question = data.get('time_per_question')
    if time_per_question is None:
        errors['time_per_question'] = 'Czas na pytanie jest wymagany'
    else:
        try:
            time_per_question = int(time_per_question)
            if time_per_question < MIN_TIME_PER_QUESTION:
                errors['time_per_question'] = f'Czas na pytanie musi wynosić co najmniej {MIN_TIME_PER_QUESTION} sekund'
            elif time_per_question > MAX_TIME_PER_QUESTION:
                errors['time_per_question'] = f'Czas na pytanie nie może przekraczać {MAX_TIME_PER_QUESTION} sekund'
        except (ValueError, TypeError):
            errors['time_per_question'] = 'Czas na pytanie musi być liczbą całkowitą'

    knowledge_level = data.get('knowledge_level', 'high_school')
    if knowledge_level not in KNOWLEDGE_LEVEL_CHOICES:
        errors['knowledge_level'] = f'Poziom wiedzy musi być jedną z wartości: {", ".join(KNOWLEDGE_LEVEL_CHOICES)}'

    if errors:
        raise ValidationException(field_errors=errors)

    return True


def validate_difficulty_level(difficulty):
    if not difficulty:
        raise ValidationException(detail='Poziom trudności jest wymagany')

    if difficulty not in DIFFICULTY_CHOICES:
        raise ValidationException(
            detail=f'Nieprawidłowy poziom trudności. Dostępne: {", ".join(DIFFICULTY_CHOICES)}'
        )

    return difficulty


def validate_knowledge_level(knowledge_level):
    if not knowledge_level:
        return 'high_school'

    if knowledge_level not in KNOWLEDGE_LEVEL_CHOICES:
        raise ValidationException(
            detail=f'Nieprawidłowy poziom wiedzy. Dostępne: {", ".join(KNOWLEDGE_LEVEL_CHOICES)}'
        )

    return knowledge_level


def validate_topic(topic):
    if not topic or not topic.strip():
        raise ValidationException(detail='Temat jest wymagany')

    topic = topic.strip()

    if len(topic) < 2:
        raise ValidationException(detail='Temat musi mieć co najmniej 2 znaki')

    if len(topic) > 200:
        raise ValidationException(detail='Temat nie może przekraczać 200 znaków')

    return topic


def validate_answer_submission(question_id, selected_answer):
    errors = {}

    if not question_id:
        errors['question_id'] = 'ID pytania jest wymagane'

    if not selected_answer or not selected_answer.strip():
        errors['selected_answer'] = 'Odpowiedź jest wymagana'

    if errors:
        raise ValidationException(field_errors=errors)

    return True


def validate_pagination_params(page, page_size):
    errors = {}

    try:
        page = int(page)
        if page < 1:
            errors['page'] = 'Numer strony musi być większy od 0'
    except (ValueError, TypeError):
        errors['page'] = 'Numer strony musi być liczbą całkowitą'

    try:
        page_size = int(page_size)
        if page_size < 1:
            errors['page_size'] = 'Rozmiar strony musi być większy od 0'
        elif page_size > 100:
            errors['page_size'] = 'Rozmiar strony nie może przekraczać 100'
    except (ValueError, TypeError):
        errors['page_size'] = 'Rozmiar strony musi być liczbą całkowitą'

    if errors:
        raise ValidationException(field_errors=errors)

    return int(page), int(page_size)