from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Q, Count
from .models import QuizSession, Question, Answer
from .serializers import QuizSessionSerializer, QuestionSerializer
from .permissions import IsQuizOwnerOrAdmin
from llm_integration.question_generator import QuestionGenerator
from llm_integration.difficulty_adapter import DifficultyAdapter
import json
import random
import threading
import time
from difflib import SequenceMatcher

# Inicjalizuj generator
generator = QuestionGenerator()
difficulty_adapter = DifficultyAdapter()


def _get_next_question_cache_key(session_id, difficulty):
    """Klucz cache dla następnego pytania"""
    # Zaokrąglij trudność do 1 miejsca po przecinku dla lepszego cache hit rate
    difficulty_rounded = round(difficulty, 1)
    return f"next_question_{session_id}_{difficulty_rounded}"


def _prefetch_next_question(session_id, topic, difficulty):
    """
    Generuj i cache'uj następne pytanie w tle.
    Działa w osobnym wątku, żeby nie blokować odpowiedzi.
    """
    cache_key = _get_next_question_cache_key(session_id, difficulty)

    # Jeśli już jest w cache, nie generuj ponownie
    if cache.get(cache_key):
        print(f"✅ Pytanie już w cache (difficulty: {difficulty})")
        return

    try:
        print(f"🔄 Rozpoczynam prefetch pytania (session: {session_id}, difficulty: {difficulty})")
        start_time = time.time()

        # Wygeneruj pytanie
        question_data = generator.generate_question(topic, difficulty)

        elapsed = time.time() - start_time
        print(f"✅ Pytanie wygenerowane w {elapsed:.2f}s")

        # Zapisz w cache na 10 minut
        cache.set(cache_key, question_data, timeout=600)
        print(f"📦 Pytanie zapisane w cache: {cache_key}")

    except Exception as e:
        print(f"❌ Error podczas prefetch: {e}")


def _prefetch_multiple_difficulties(session_id, topic, current_difficulty):
    """
    Prefetch pytań dla różnych poziomów trudności.
    Zwiększa szansę na cache hit gdy trudność się zmieni.
    """
    # Prefetch dla obecnej trudności
    _prefetch_next_question(session_id, topic, current_difficulty)

    # Prefetch dla trudniejszego poziomu (+1.0)
    if current_difficulty < 10:
        _prefetch_next_question(session_id, topic, min(current_difficulty + 1.0, 10.0))

    # Prefetch dla łatwiejszego poziomu (-1.0)
    if current_difficulty > 1:
        _prefetch_next_question(session_id, topic, max(current_difficulty - 1.0, 1.0))


def _similarity_ratio(text1, text2):
    """Oblicza podobieństwo między dwoma tekstami (0.0 - 1.0)"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def _convert_numeric_to_text_difficulty(difficulty_float):
    """
    Konwertuje numeryczny poziom trudności na tekstowy.

    Args:
        difficulty_float: Poziom trudności 1.0-10.0

    Returns:
        str: 'łatwy', 'średni' lub 'trudny'
    """
    if difficulty_float <= 3.5:
        return 'łatwy'
    elif difficulty_float <= 7.0:
        return 'średni'
    else:
        return 'trudny'


def _find_similar_question(question_text, topic, difficulty_text, *, session=None, threshold=0.85):
    """
    Szuka podobnego pytania w bazie danych.

    Args:
        question_text: Tekst nowego pytania
        topic: Temat pytania
        difficulty_text: Poziom trudności ('łatwy', 'średni', 'trudny')
        session: Opcjonalnie konkretna sesja quizu do przeszukania
        threshold: Próg podobieństwa (0.85 = 85% podobne)

    Returns:
        Question object jeśli znaleziono podobne pytanie, inaczej None
    """
    # Szukaj pytań z tego samego poziomu trudności
    similar_questions = Question.objects.filter(
        difficulty_level=difficulty_text
    )

    if session is not None:
        # Ogranicz do bieżącej sesji – zapobiega korzystaniu z pytań innych użytkowników
        similar_questions = similar_questions.filter(session=session)
    else:
        # Zachowaj dotychczasowe zachowanie (fallback) jeśli nie podano sesji
        similar_questions = similar_questions.filter(session__topic__iexact=topic)

    similar_questions = similar_questions.select_related('session')[:100]

    # Sprawdź podobieństwo tekstu
    for existing_question in similar_questions:
        similarity = _similarity_ratio(question_text, existing_question.question_text)

        if similarity >= threshold:
            print(f"🔄 Znaleziono podobne pytanie (similarity: {similarity:.2f})")
            print(f"   Nowe: {question_text[:60]}...")
            print(f"   Istniejące: {existing_question.question_text[:60]}...")
            return existing_question

    return None


def _find_or_create_question(session, question_data, similarity_threshold=0.85):
    """
    Znajduje istniejące podobne pytanie lub tworzy nowe.
    Zapobiega duplikatom w bazie danych.
    WAŻNE: Sprawdza też czy użytkownik już odpowiadał na to pytanie w tej sesji!

    Args:
        session: QuizSession object
        question_data: dict with question data
        similarity_threshold: float (0.0-1.0) - próg podobieństwa dla deduplication
                             Wyższy = bardziej restrykcyjny (tylko prawie identyczne pytania)

    Returns:
        tuple: (Question object, created: bool)
    """
    # Konwertuj numeryczny poziom trudności sesji na tekstowy
    difficulty_text = _convert_numeric_to_text_difficulty(session.current_difficulty)

    # Sprawdź czy podobne pytanie już istnieje
    existing_question = _find_similar_question(
        question_data['question'],
        session.topic,
        difficulty_text,
        session=session,
        threshold=similarity_threshold
    )

    if existing_question:
        # Sprawdź czy użytkownik JUŻ ODPOWIADAŁ na to pytanie w TEJ SESJI
        # Jeśli tak, NIE używaj tego pytania ponownie!
        already_answered = Answer.objects.filter(
            question=existing_question,
            user=session.user,
            question__session=session
        ).exists()

        if already_answered:
            print(f"⚠️ Użytkownik już odpowiadał na to pytanie w tej sesji - generuję nowe")
            # Nie używaj tego pytania, utwórz nowe
        else:
            # Użyj istniejącego pytania - użytkownik jeszcze nie odpowiadał
            print(f"✅ Używam istniejącego pytania ID={existing_question.id}")
            return existing_question, False

    # Nie znaleziono odpowiedniego - utwórz nowe pytanie
    new_question = Question.objects.create(
        session=session,
        question_text=question_data['question'],
        correct_answer=question_data['correct_answer'],
        wrong_answer_1=question_data['wrong_answers'][0],
        wrong_answer_2=question_data['wrong_answers'][1],
        wrong_answer_3=question_data['wrong_answers'][2],
        explanation=question_data['explanation'],
        difficulty_level=difficulty_text
    )
    print(f"📝 Utworzono nowe pytanie ID={new_question.id} (trudność: {difficulty_text})")
    return new_question, True


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_quiz(request):
    topic = request.data.get('topic')
    difficulty = request.data.get('difficulty', 'medium')
    questions_count = request.data.get('questions_count', 10)
    time_per_question = request.data.get('time_per_question', 30)
    use_adaptive_difficulty = request.data.get('use_adaptive_difficulty', True)

    # Walidacja parametrów
    questions_count = min(max(int(questions_count), 5), 20)  # 5-20
    time_per_question = min(max(int(time_per_question), 10), 60)  # 10-60

    difficulty_map = {
        'easy': 2.0,
        'medium': 5.0,
        'hard': 8.0
    }

    initial_difficulty = difficulty_map.get(difficulty, 5.0)

    session = QuizSession.objects.create(
        user=request.user,
        topic=topic,
        initial_difficulty=difficulty,
        current_difficulty=initial_difficulty,
        questions_count=questions_count,
        time_per_question=time_per_question,
        use_adaptive_difficulty=use_adaptive_difficulty
    )

    profile = request.user.profile
    profile.total_quizzes_played += 1
    profile.save()

    # 🎯 FIXED DIFFICULTY: Wygeneruj WSZYSTKIE pytania na raz (różnorodne!)
    if not use_adaptive_difficulty:
        print(f"📚 Fixed difficulty mode - generating {questions_count} DIVERSE questions")

        try:
            # Wygeneruj WSZYSTKIE pytania jednocześnie z instrukcją o różnorodności
            all_questions_data = generator.generate_multiple_questions(
                topic,
                initial_difficulty,
                questions_count
            )

            # Zapisz każde pytanie z WYSOKIM progiem deduplikacji (0.98)
            # Tylko prawie IDENTYCZNE pytania będą reużywane
            # "pierwiastek z 49" ≠ "pierwiastek z 25" mimo 96% podobieństwa
            created_count = 0
            reused_count = 0
            for question_data in all_questions_data:
                question, created = _find_or_create_question(
                    session,
                    question_data,
                    similarity_threshold=0.98  # Bardzo wysoki próg dla fixed mode
                )
                if created:
                    created_count += 1
                else:
                    reused_count += 1

            print(f"✅ Pre-generated {len(all_questions_data)} questions: {created_count} new, {reused_count} reused")

        except Exception as e:
            print(f"❌ Error pre-generating questions: {e}")
            # Fallback - będą generowane na bieżąco

    else:
        # 🚀 ADAPTIVE DIFFICULTY: PREFETCH pierwszego pytania w tle
        thread = threading.Thread(
            target=_prefetch_multiple_difficulties,
            args=(session.id, topic, initial_difficulty)
        )
        thread.daemon = True
        thread.start()
        print(f"🔄 Prefetch pierwszego pytania uruchomiony (session: {session.id})")

    return Response({
        'session_id': session.id,
        'message': 'Quiz started successfully!',
        'topic': topic,
        'difficulty': difficulty,
        'questions_count': questions_count,
        'time_per_question': time_per_question,
        'use_adaptive_difficulty': use_adaptive_difficulty
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    # Check if quiz is already completed
    if session.is_completed:
        return Response(
            {'error': 'Quiz already completed'},
            status=status.HTTP_404_NOT_FOUND
        )

    # 🎯 FIXED DIFFICULTY: Pobierz z pre-generowanych pytań dla TEJ SESJI
    if not session.use_adaptive_difficulty:
        # WAŻNE: Pobieramy pytania TYLKO z tej sesji (pre-wygenerowane w start_quiz)
        # oraz te które user jeszcze nie widział
        answered_question_ids_in_session = Answer.objects.filter(
            question__session=session,
            user=session.user
        ).values_list('question_id', flat=True)

        # Pobierz pytania TYLKO z tej sesji, w kolejności created_at
        # To zapewnia że każde pytanie jest unikalne w ramach quizu
        question = Question.objects.filter(
            session=session  # TYLKO z tej sesji!
        ).exclude(
            id__in=answered_question_ids_in_session
        ).order_by('created_at').first()  # Deterministyczna kolejność

        if not question:
            # Brak pytań - prawdopodobnie błąd pre-generowania, wygeneruj fallback
            print(f"⚠️ No pre-generated questions found - generating fallback")
            try:
                question_data = generator.generate_question(
                    session.topic,
                    session.current_difficulty
                )
                question, created = _find_or_create_question(
                    session,
                    question_data,
                    similarity_threshold=0.98  # Wysoki próg też dla fallback w fixed mode
                )
                generation_status = "fallback_generated"
            except Exception as e:
                print(f"❌ Błąd podczas generowania fallback: {e}")
                return Response(
                    {'error': 'Failed to generate question. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            print(f"📖 Fetched pre-generated question ID={question.id}")
            generation_status = "pre_generated"

    # 🚀 ADAPTIVE DIFFICULTY: SPRÓBUJ POBRAĆ Z CACHE
    else:
        cache_key = _get_next_question_cache_key(session_id, session.current_difficulty)
        question_data = cache.get(cache_key)

        if question_data:
            # Pytanie gotowe w cache - instant!
            cache.delete(cache_key)  # Usuń z cache po użyciu
            print(f"⚡ Pytanie pobrane z cache (instant!) - difficulty: {session.current_difficulty}")
            generation_status = "cached"
        else:
            # Fallback - czekamy na generowanie
            print(f"⏳ Cache miss - generuję pytanie synchronicznie (difficulty: {session.current_difficulty})")

            try:
                start_time = time.time()
                question_data = generator.generate_question(
                    session.topic,
                    session.current_difficulty
                )
                elapsed = time.time() - start_time
                print(f"✅ Pytanie wygenerowane w {elapsed:.2f}s")
                generation_status = f"generated_in_{elapsed:.1f}s"

            except Exception as e:
                print(f"❌ Błąd podczas generowania: {e}")
                return Response(
                    {'error': 'Failed to generate question. Please try again.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        # Znajdź istniejące podobne pytanie lub utwórz nowe (deduplikacja!)
        # W adaptive mode używamy niższego progu (0.85 - default)
        # bo pytania są generowane pojedynczo i częściej chcemy reużywać
        question, created = _find_or_create_question(session, question_data)

        if not created:
            generation_status = "reused_existing"

    answers = [
        question.correct_answer,
        question.wrong_answer_1,
        question.wrong_answer_2,
        question.wrong_answer_3
    ]
    random.shuffle(answers)

    # Map answers to option letters A, B, C, D
    option_mapping = {}
    for i, answer in enumerate(answers):
        option_letter = chr(65 + i)  # A=65, B=66, C=67, D=68
        option_mapping[option_letter] = answer

    question_number = min(session.total_questions + 1, session.questions_count)
    difficulty_label = question.difficulty_level
    questions_remaining = max(session.questions_count - session.total_questions, 0)

    return Response({
        'question_id': question.id,
        'question_text': question.question_text,
        'topic': session.topic,
        'answers': answers,
        'option_a': answers[0],
        'option_b': answers[1],
        'option_c': answers[2],
        'option_d': answers[3],
        'current_difficulty': session.current_difficulty,
        'question_number': question_number,
        'questions_count': session.questions_count,  # Dodano: całkowita liczba pytań w quizie
        'questions_remaining': questions_remaining,
        'time_per_question': session.time_per_question,
        'use_adaptive_difficulty': session.use_adaptive_difficulty,
        'generation_status': generation_status,  # Debug info
        'difficulty_label': difficulty_label
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    question_id = request.data.get('question_id')
    selected_answer = request.data.get('selected_answer')
    response_time = request.data.get('response_time', 0)

    question = get_object_or_404(Question, id=question_id)
    session = question.session

    if session.user != request.user:
        return Response(
            {'error': 'Unauthorized access to this quiz session'},
            status=status.HTTP_403_FORBIDDEN
        )

    # Check if user already answered this question (prevent duplicate submissions)
    existing_answer = Answer.objects.filter(question=question, user=request.user).first()
    if existing_answer:
        # Return the existing answer instead of creating duplicate
        return Response({
            'is_correct': existing_answer.is_correct,
            'correct_answer': question.correct_answer,
            'explanation': question.explanation,
            'current_streak': session.current_streak,
            'quiz_completed': session.is_completed,
            'session_stats': {
                'total_questions': session.total_questions,
                'correct_answers': session.correct_answers,
                'accuracy': session.accuracy
            }
        })

    is_correct = selected_answer == question.correct_answer

    answer = Answer.objects.create(
        question=question,
        user=request.user,
        selected_answer=selected_answer,
        is_correct=is_correct,
        response_time=response_time
    )

    # Increment total_questions AFTER user submits answer
    session.total_questions += 1
    if session.total_questions > session.questions_count:
        session.total_questions = session.questions_count

    if is_correct:
        session.correct_answers += 1
        session.current_streak += 1
    else:
        session.current_streak = 0

    # Adaptacyjna zmiana poziomu trudności (jeśli włączona)
    previous_difficulty = session.current_difficulty
    difficulty_changed = False
    if session.use_adaptive_difficulty:
        # Pobierz ostatnie odpowiedzi dla tej sesji
        recent_answers_objs = Answer.objects.filter(
            question__session=session
        ).order_by('-answered_at')[:difficulty_adapter.streak_threshold]

        # Przekonwertuj na listę boolean (True = poprawna, False = błędna)
        recent_answers = [ans.is_correct for ans in reversed(list(recent_answers_objs))]

        # Dostosuj poziom trudności
        new_difficulty = difficulty_adapter.adjust_difficulty(
            session.current_difficulty,
            recent_answers
        )

        if new_difficulty != session.current_difficulty:
            difficulty_changed = True
            print(f"🎯 Trudność zmieniona: {session.current_difficulty} → {new_difficulty}")
            session.current_difficulty = new_difficulty

    session.save()

    # Zaktualizuj statystyki użytkownika
    profile = request.user.profile
    profile.total_questions_answered += 1
    if is_correct:
        profile.total_correct_answers += 1
    if session.current_streak > profile.highest_streak:
        profile.highest_streak = session.current_streak
    profile.save()

    # Check if quiz should be completed
    quiz_completed = session.total_questions >= session.questions_count

    if quiz_completed and not session.is_completed:
        session.ended_at = timezone.now()
        session.is_completed = True
        session.save()
        print(f"🏁 Quiz zakończony (session: {session.id})")
    else:
        # 🚀 PREFETCH: Generuj następne pytania W TLE
        # Uruchom w osobnym wątku, żeby nie blokować odpowiedzi
        thread = threading.Thread(
            target=_prefetch_multiple_difficulties,
            args=(session.id, session.topic, session.current_difficulty)
        )
        thread.daemon = True
        thread.start()
        print(f"🔄 Prefetch następnych pytań uruchomiony (difficulty: {session.current_difficulty})")

    return Response({
        'is_correct': is_correct,
        'correct_answer': question.correct_answer,
        'explanation': question.explanation,
        'current_streak': session.current_streak,
        'quiz_completed': quiz_completed,
        'difficulty_changed': difficulty_changed,
        'previous_difficulty': previous_difficulty if difficulty_changed else None,
        'new_difficulty': session.current_difficulty if difficulty_changed else None,
        'session_stats': {
            'total_questions': session.total_questions,
            'correct_answers': session.correct_answers,
            'accuracy': session.accuracy
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_quiz(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)
    session.ended_at = timezone.now()
    session.is_completed = True
    session.save()

    return Response({
        'message': 'Quiz completed!',
        'final_stats': {
            'topic': session.topic,
            'total_questions': session.total_questions,
            'correct_answers': session.correct_answers,
            'accuracy': session.accuracy,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_history(request):
    sessions = QuizSession.objects.filter(user=request.user)

    # Filtracja
    topic = request.GET.get('topic')
    difficulty = request.GET.get('difficulty')
    is_custom = request.GET.get('is_custom')

    if topic:
        sessions = sessions.filter(topic__icontains=topic)
    if difficulty:
        sessions = sessions.filter(initial_difficulty=difficulty)
    if is_custom == 'true':
        sessions = sessions.exclude(
            questions_count=10,
            time_per_question=30,
            use_adaptive_difficulty=True
        )
    elif is_custom == 'false':
        sessions = sessions.filter(
            questions_count=10,
            time_per_question=30,
            use_adaptive_difficulty=True
        )

    # Sortowanie
    order_by = request.GET.get('order_by', '-started_at')
    allowed_sorts = ['started_at', '-started_at', 'topic', '-topic',
                     'accuracy', '-accuracy', 'total_questions', '-total_questions']
    if order_by in allowed_sorts:
        # Dla accuracy potrzebujemy sortować po obliczonym polu
        if order_by in ['accuracy', '-accuracy']:
            sessions_list = list(sessions)
            sessions_list.sort(key=lambda x: x.accuracy, reverse=order_by.startswith('-'))

            # Paginacja dla posortowanej listy
            page = int(request.GET.get('page', 1))
            page_size = int(request.GET.get('page_size', 10))
            start = (page - 1) * page_size
            end = start + page_size

            serializer = QuizSessionSerializer(sessions_list[start:end], many=True)

            return Response({
                'count': len(sessions_list),
                'next': page * page_size < len(sessions_list),
                'previous': page > 1,
                'results': serializer.data
            })
        else:
            sessions = sessions.order_by(order_by)

    # Paginacja
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))

    total_count = sessions.count()
    sessions = sessions[(page - 1) * page_size:page * page_size]

    serializer = QuizSessionSerializer(sessions, many=True)

    return Response({
        'count': total_count,
        'next': page * page_size < total_count,
        'previous': page > 1,
        'results': serializer.data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_details(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)
    questions = Question.objects.filter(session=session).prefetch_related('answers')

    questions_data = []
    for q in questions:
        answer = q.answers.first()
        if answer:
            # Create shuffled answers list matching how they were presented
            answers = [
                q.correct_answer,
                q.wrong_answer_1,
                q.wrong_answer_2,
                q.wrong_answer_3
            ]
            random.shuffle(answers)

            # Map to A, B, C, D options
            option_mapping = {}
            for i, ans in enumerate(answers):
                option_letter = chr(65 + i)  # A=65, B=66, C=67, D=68
                option_mapping[ans] = option_letter

            questions_data.append({
                'id': q.id,
                'question_text': q.question_text,
                'option_a': answers[0],
                'option_b': answers[1],
                'option_c': answers[2],
                'option_d': answers[3],
                'selected_answer': option_mapping.get(answer.selected_answer, ''),
                'correct_answer': option_mapping.get(q.correct_answer, 'A'),
                'is_correct': answer.is_correct,
                'explanation': q.explanation,
                'response_time': answer.response_time,
                'difficulty': q.difficulty_level
            })

    # Mapuj initial_difficulty string na wartość numeryczną
    difficulty_map = {
        'easy': 2.0,
        'medium': 5.0,
        'hard': 8.0
    }
    initial_difficulty_value = difficulty_map.get(session.initial_difficulty, 5.0)

    # Sprawdź czy używa custom settings
    is_custom = (session.questions_count != 10 or
                 session.time_per_question != 30 or
                 not session.use_adaptive_difficulty)

    return Response({
        'id': session.id,
        'session_id': session.id,
        'topic': session.topic,
        'difficulty': session.initial_difficulty,
        'initial_difficulty_value': initial_difficulty_value,
        'current_difficulty': session.current_difficulty,
        'started_at': session.started_at,
        'ended_at': session.ended_at,
        'completed_at': session.ended_at,
        'total_questions': session.total_questions,
        'correct_answers': session.correct_answers,
        'score': session.correct_answers,
        'accuracy': session.accuracy,
        'questions_count': session.questions_count,
        'time_per_question': session.time_per_question,
        'use_adaptive_difficulty': session.use_adaptive_difficulty,
        'is_custom': is_custom,
        'questions': questions_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def questions_library(request):
    """
    API endpoint do przeglądania wszystkich pytań z filtrowaniem i wyszukiwaniem.
    Używany przez frontend do wyświetlenia biblioteki pytań.
    """
    questions = Question.objects.all().select_related('session').prefetch_related('answers')

    # Filtracja po temacie
    topic = request.GET.get('topic')
    if topic:
        questions = questions.filter(session__topic__icontains=topic)

    # Filtracja po poziomie trudności
    difficulty = request.GET.get('difficulty')
    if difficulty and difficulty in ['łatwy', 'średni', 'trudny']:
        questions = questions.filter(difficulty_level=difficulty)

    # Wyszukiwanie po tekście pytania lub odpowiedziach
    search = request.GET.get('search')
    if search:
        questions = questions.filter(
            Q(question_text__icontains=search) |
            Q(correct_answer__icontains=search) |
            Q(wrong_answer_1__icontains=search) |
            Q(wrong_answer_2__icontains=search) |
            Q(wrong_answer_3__icontains=search) |
            Q(explanation__icontains=search)
        )

    # Unikalne tematy (dla filtra)
    if request.GET.get('get_topics') == 'true':
        topics = Question.objects.values_list('session__topic', flat=True).distinct()
        return Response({'topics': list(topics)})

    # Sortowanie
    order_by = request.GET.get('order_by', '-created_at')
    allowed_sorts = ['created_at', '-created_at', 'difficulty_level', '-difficulty_level']
    if order_by in allowed_sorts:
        questions = questions.order_by(order_by)

    # Paginacja
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))

    total_count = questions.count()
    questions = questions[(page - 1) * page_size:page * page_size]

    # Przygotuj dane
    questions_data = []
    for q in questions:
        # Policz statystyki odpowiedzi
        total_answers = q.answers.count()
        correct_answers_count = q.answers.filter(is_correct=True).count()
        wrong_answers_count = total_answers - correct_answers_count

        questions_data.append({
            'id': q.id,
            'question_text': q.question_text,
            'topic': q.session.topic,
            'difficulty_level': q.difficulty_level,  # Teraz jest tekstem: 'łatwy', 'średni', 'trudny'
            'correct_answer': q.correct_answer,
            'wrong_answer_1': q.wrong_answer_1,
            'wrong_answer_2': q.wrong_answer_2,
            'wrong_answer_3': q.wrong_answer_3,
            'explanation': q.explanation,
            'created_at': q.created_at,
            'stats': {
                'total_answers': total_answers,
                'correct_answers': correct_answers_count,
                'wrong_answers': wrong_answers_count,
                'accuracy': round((correct_answers_count / total_answers * 100), 1) if total_answers > 0 else 0
            }
        })

    return Response({
        'count': total_count,
        'next': page * page_size < total_count,
        'previous': page > 1,
        'results': questions_data
    })

@api_view(['GET'])
def quiz_api_root(request):
    """Bazowy endpoint API quiz"""
    return Response({
        'message': 'Quiz LLM API',
        'endpoints': {
            'start_quiz': '/api/quiz/start/',
            'get_question': '/api/quiz/question/<session_id>/',
            'submit_answer': '/api/quiz/answer/',
            'end_quiz': '/api/quiz/end/<session_id>/',
            'quiz_history': '/api/quiz/history/',
            'quiz_details': '/api/quiz/details/<session_id>/',
            'all_questions': '/api/quiz/questions/',
        }
    })