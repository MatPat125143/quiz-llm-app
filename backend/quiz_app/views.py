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


def _find_similar_question(question_text, topic, difficulty, threshold=0.85):
    """
    Szuka podobnego pytania w bazie danych.

    Args:
        question_text: Tekst nowego pytania
        topic: Temat pytania
        difficulty: Poziom trudności
        threshold: Próg podobieństwa (0.85 = 85% podobne)

    Returns:
        Question object jeśli znaleziono podobne pytanie, inaczej None
    """
    # Szukaj pytań z tego samego tematu i podobnego poziomu trudności (+/- 1.0)
    similar_difficulty_questions = Question.objects.filter(
        session__topic__iexact=topic,
        difficulty_level__gte=difficulty - 1.0,
        difficulty_level__lte=difficulty + 1.0
    ).select_related('session')[:100]  # Ogranicz do 100 ostatnich

    # Sprawdź podobieństwo tekstu
    for existing_question in similar_difficulty_questions:
        similarity = _similarity_ratio(question_text, existing_question.question_text)

        if similarity >= threshold:
            print(f"🔄 Znaleziono podobne pytanie (similarity: {similarity:.2f})")
            print(f"   Nowe: {question_text[:60]}...")
            print(f"   Istniejące: {existing_question.question_text[:60]}...")
            return existing_question

    return None


def _find_or_create_question(session, question_data):
    """
    Znajduje istniejące podobne pytanie lub tworzy nowe.
    Zapobiega duplikatom w bazie danych.

    Returns:
        tuple: (Question object, created: bool)
    """
    # Sprawdź czy podobne pytanie już istnieje
    existing_question = _find_similar_question(
        question_data['question'],
        session.topic,
        session.current_difficulty
    )

    if existing_question:
        # Użyj istniejącego pytania - NIE TWORZYMY DUPLIKATU!
        print(f"✅ Używam istniejącego pytania ID={existing_question.id}")
        return existing_question, False

    # Nie znaleziono - utwórz nowe pytanie
    new_question = Question.objects.create(
        session=session,
        question_text=question_data['question'],
        correct_answer=question_data['correct_answer'],
        wrong_answer_1=question_data['wrong_answers'][0],
        wrong_answer_2=question_data['wrong_answers'][1],
        wrong_answer_3=question_data['wrong_answers'][2],
        explanation=question_data['explanation'],
        difficulty_level=session.current_difficulty
    )
    print(f"📝 Utworzono nowe pytanie ID={new_question.id}")
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

    # 🚀 PREFETCH: Wygeneruj pierwsze pytanie w tle
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

    # 🚀 SPRÓBUJ POBRAĆ Z CACHE
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
        'question_number': session.total_questions + 1,
        'time_per_question': session.time_per_question,
        'use_adaptive_difficulty': session.use_adaptive_difficulty,
        'generation_status': generation_status  # Debug info
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
    difficulty_min = request.GET.get('difficulty_min')
    difficulty_max = request.GET.get('difficulty_max')
    if difficulty_min:
        questions = questions.filter(difficulty_level__gte=float(difficulty_min))
    if difficulty_max:
        questions = questions.filter(difficulty_level__lte=float(difficulty_max))

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
            'difficulty_level': round(q.difficulty_level, 1),
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
