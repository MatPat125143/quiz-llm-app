from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value, IntegerField, FloatField, F, ExpressionWrapper
from django.db.models.functions import Coalesce
from .models import QuizSession, Question, QuizSessionQuestion, Answer
from .serializers import QuizSessionSerializer, AnswerSerializer
from .permissions import IsQuizOwnerOrAdmin
from llm_integration.question_generator import QuestionGenerator
from llm_integration.difficulty_adapter import DifficultyAdapter
import json
import random
import threading
import time
import hashlib

# Inicjalizuj generator
generator = QuestionGenerator()
difficulty_adapter = DifficultyAdapter()


# ============================================================================
# POMOCNICZE FUNKCJE DLA GLOBALNYCH PYTAŃ
# ============================================================================

def _convert_numeric_to_text_difficulty(difficulty_float):
    """Konwertuje numeryczny poziom trudności na tekstowy"""
    if difficulty_float <= 3.5:
        return 'łatwy'
    elif difficulty_float <= 7.0:
        return 'średni'
    else:
        return 'trudny'


def _find_or_create_global_question(topic, question_data, difficulty_text, user=None):
    """
    Znajdź lub utwórz GLOBALNE pytanie używając hash'a.

    Args:
        topic: Temat pytania
        question_data: dict z danymi pytania z LLM
        difficulty_text: 'łatwy', 'średni', lub 'trudny'
        user: Użytkownik który tworzy pytanie

    Returns:
        tuple: (Question object, created: bool)
    """
    try:
        # Oblicz hash contentu
        content = f"{question_data['question']}{question_data['correct_answer']}{topic}{difficulty_text}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Szukaj po hash'u - instant deduplikacja!
        question, created = Question.objects.get_or_create(
            content_hash=content_hash,
            defaults={
                'topic': topic,
                'question_text': question_data['question'],
                'correct_answer': question_data['correct_answer'],
                'wrong_answer_1': question_data['wrong_answers'][0],
                'wrong_answer_2': question_data['wrong_answers'][1],
                'wrong_answer_3': question_data['wrong_answers'][2],
                'explanation': question_data['explanation'],
                'difficulty_level': difficulty_text,
                'created_by': user
            }
        )

        if created:
            print(f"📝 Utworzono nowe globalne pytanie ID={question.id}")
        else:
            print(f"✅ Reużywam pytanie ID={question.id} (używane {question.times_used}x)")
            # Zwiększ licznik użycia
            question.times_used += 1
            question.save(update_fields=['times_used'])

        return question, created

    except KeyError as e:
        print(f"❌ Brak wymaganego klucza w question_data: {e}")
        raise ValueError(f"Invalid question_data format: missing {e}")
    except Exception as e:
        print(f"❌ Error in _find_or_create_global_question: {e}")
        raise


def _add_question_to_session(session, question, order=0):
    """
    Dodaje pytanie do sesji quizu, ale zapobiega duplikatom na poziomie treści.
    """

    # Sprawdź, czy pytanie o identycznej treści już jest w sesji
    existing_question_ids = QuizSessionQuestion.objects.filter(session=session) \
        .select_related('question') \
        .values_list('question__question_text', flat=True)

    if question.question_text in existing_question_ids:
        print(f"⚠️ Duplikat pytania \"{question.question_text}\" — pomijam dodanie do sesji {session.id}")
        return None  # lub zwróć False albo jakiś znacznik, że pominięto

    # Jeżeli nie ma duplikatu — dodaj pytanie
    session_question, created = QuizSessionQuestion.objects.get_or_create(
        session=session,
        question=question,
        defaults={'order': order}
    )

    if created:
        print(f"🔗 Dodano pytanie {question.id} do sesji {session.id} (order: {order})")
    else:
        print(f"⚠️ Pytanie {question.id} już jest w sesji {session.id}")

    return session_question


def _has_user_answered_question(user, question, session=None):
    """
    Sprawdza czy użytkownik już odpowiadał na to pytanie.

    Args:
        user: User object
        question: Question object
        session: QuizSession object (opcjonalnie - sprawdzi tylko w tej sesji)

    Returns:
        bool: True jeśli użytkownik już odpowiadał
    """
    filters = {'user': user, 'question': question}
    if session:
        filters['session'] = session

    return Answer.objects.filter(**filters).exists()


def _session_seen_question_texts(session):
    """Zwraca zbiór tekstów pytań już dołączonych do sesji (po treści)."""
    return set(
        QuizSessionQuestion.objects.filter(session=session)
        .select_related('question')
        .values_list('question__question_text', flat=True)
    )


def _generate_unique_question_for_session(session, max_attempts=7):
    """
    Generuje/znajduje pytanie, które NIE występuje jeszcze w tej sesji (po question_text).
    Zwraca (question, generation_status).
    """
    seen_texts = _session_seen_question_texts(session)
    difficulty_text = _convert_numeric_to_text_difficulty(session.current_difficulty)

    attempts = 0
    while attempts < max_attempts:
        question_data = generator.generate_question(session.topic, session.current_difficulty)
        question, created = _find_or_create_global_question(
            session.topic, question_data, difficulty_text, user=session.user
        )
        if question.question_text not in seen_texts:
            order = QuizSessionQuestion.objects.filter(session=session).count()
            _add_question_to_session(session, question, order=order)
            return question, ('generated' if created else 'reused')

        attempts += 1
        print(f"🔁 Duplicate question text detected, regenerating... (attempt {attempts})")

    # Fallback – dobierz istniejące globalne pytanie z tego tematu, którego nie było jeszcze w sesji
    fallback = Question.objects.filter(topic=session.topic) \
        .exclude(question_text__in=seen_texts) \
        .order_by('-times_used').first()

    if fallback:
        order = QuizSessionQuestion.objects.filter(session=session).count()
        _add_question_to_session(session, fallback, order=order)
        return fallback, 'fallback'

    raise ValueError("No unique question available for this session")


def _build_question_payload(session, question, generation_status):
    """Buduje payload odpowiedzi GET /question/ dla danego pytania + sesji."""
    answers = [
        question.correct_answer,
        question.wrong_answer_1,
        question.wrong_answer_2,
        question.wrong_answer_3
    ]
    random.shuffle(answers)

    question_number = min(session.total_questions + 1, session.questions_count)
    questions_remaining = max(session.questions_count - session.total_questions, 0)

    return {
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
        'questions_count': session.questions_count,
        'questions_remaining': questions_remaining,
        'time_per_question': session.time_per_question,
        'use_adaptive_difficulty': session.use_adaptive_difficulty,
        'generation_status': generation_status,
        'difficulty_label': question.difficulty_level,
        'times_used': question.times_used,
        'success_rate': question.success_rate,
    }


def _cache_next_question_payload(session, question):
    """Zapisuje gotowe następne pytanie w cache do szybkiego pobrania."""
    payload = _build_question_payload(session, question, generation_status='cached')
    cache.set(f'next_q:{session.id}', payload, timeout=120)  # 2 minuty cache


def _prepare_next_question_async(session_id):
    """
    W tle: przygotuj i zcache'uj następne pytanie, by kolejny GET był natychmiastowy.
    Unika duplikatów po TEKŚCIE w obrębie sesji.
    """
    try:
        session = QuizSession.objects.get(id=session_id)
        if session.is_completed:
            return

        # Jeśli już czeka w cache – nie rób nic
        if cache.get(f'next_q:{session.id}'):
            return

        # Zbierz już „widziane” treści
        answered_qids = Answer.objects.filter(session=session, user=session.user)\
            .values_list('question_id', flat=True)
        seen_texts = set(
            QuizSessionQuestion.objects.filter(session=session)
            .select_related('question')
            .values_list('question__question_text', flat=True)
        )
        # do seen_texts dołóż także teksty już odpowiedzianych
        seen_texts |= set(
            Answer.objects.filter(session=session, user=session.user)
            .values_list('question__question_text', flat=True)
        )

        # FIXED: wybierz z już przypiętych do sesji kolejne nieodpowiedziane + unikalne po TEKŚCIE
        if not session.use_adaptive_difficulty:
            qs = QuizSessionQuestion.objects.filter(session=session) \
                .exclude(question_id__in=answered_qids) \
                .exclude(question__question_text__in=seen_texts) \
                .select_related('question').order_by('order')

            session_question = qs.first()
            if session_question:
                _cache_next_question_payload(session, session_question.question)
            return

        # ADAPTIVE: generuj do skutku unikalne pytanie po TEKŚCIE
        difficulty_text = _convert_numeric_to_text_difficulty(session.current_difficulty)
        max_attempts, attempts = 7, 0
        while attempts < max_attempts:
            qdata = generator.generate_question(session.topic, session.current_difficulty)
            q, created = _find_or_create_global_question(session.topic, qdata, difficulty_text, user=session.user)
            if q.question_text not in seen_texts:
                order = QuizSessionQuestion.objects.filter(session=session).count()
                _add_question_to_session(session, q, order=order)
                _cache_next_question_payload(session, q)
                return
            attempts += 1
            print(f"🔁 (pre-gen) duplicate by text, retry {attempts}/{max_attempts}")

        # Fallback – globalne pytanie z tego tematu, którego nie było
        fallback = Question.objects.filter(topic=session.topic)\
            .exclude(question_text__in=seen_texts)\
            .order_by('-times_used').first()
        if fallback:
            order = QuizSessionQuestion.objects.filter(session=session).count()
            _add_question_to_session(session, fallback, order=order)
            _cache_next_question_payload(session, fallback)

    except Exception as e:
        print(f"❌ _prepare_next_question_async error: {e}")

# ============================================================================
# GŁÓWNE ENDPOINTY
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_quiz(request):
    """Rozpocznij nowy quiz - używa GLOBALNYCH pytań"""
    topic = request.data.get('topic')
    difficulty = request.data.get('difficulty', 'medium')
    questions_count = request.data.get('questions_count', 10)
    time_per_question = request.data.get('time_per_question', 30)
    use_adaptive_difficulty = request.data.get('use_adaptive_difficulty', True)

    # Walidacja
    questions_count = min(max(int(questions_count), 5), 20)
    time_per_question = min(max(int(time_per_question), 10), 60)

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

    # 🎯 FIXED DIFFICULTY: Pre-generuj pytania
    if not use_adaptive_difficulty:
        print(f"📚 Fixed difficulty - generating {questions_count} questions")

        try:
            # Wygeneruj pytania
            all_questions_data = generator.generate_multiple_questions(
                topic,
                initial_difficulty,
                questions_count
            )

            difficulty_text = _convert_numeric_to_text_difficulty(initial_difficulty)

            created_count = 0
            reused_count = 0

            # Dla każdego pytania: znajdź/utwórz globalne i dodaj do sesji
            for order, question_data in enumerate(all_questions_data):
                question, was_created = _find_or_create_global_question(
                    topic,
                    question_data,
                    difficulty_text,
                    user=request.user
                )

                if was_created:
                    created_count += 1
                else:
                    reused_count += 1

                # Dodaj pytanie do sesji
                _add_question_to_session(session, question, order=order)

            print(f"✅ Pre-generated: {created_count} new, {reused_count} reused")

        except Exception as e:
            print(f"❌ Error pre-generating questions: {e}")
            import traceback
            traceback.print_exc()

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
    """Pobierz następne pytanie - używa GLOBALNYCH pytań (z unikaniem duplikatów po treści)."""
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    if session.is_completed:
        return Response(
            {'error': 'Quiz already completed'},
            status=status.HTTP_404_NOT_FOUND
        )

    # ⚡ 0) Spróbuj zwrócić pytanie z cache (jeśli wcześniej zostało pre-wygenerowane po submit_answer)
    cached = cache.get(f'next_q:{session.id}')
    if cached:
        cache.delete(f'next_q:{session.id}')
        print("⚡ Served question from cache")
        return Response(cached)

    # 🎯 FIXED DIFFICULTY: Pobierz z pre-generowanych
    if not session.use_adaptive_difficulty:
        # Pytania które user JUŻ WIDZIAŁ w tej sesji (po ID)
        answered_question_ids = Answer.objects.filter(
            session=session,
            user=session.user
        ).values_list('question_id', flat=True)

        # Dodatkowo: unikaj duplikatów po TEKŚCIE (np. inne ID, ta sama treść)
        answered_texts = Answer.objects.filter(
            session=session,
            user=session.user
        ).values_list('question__question_text', flat=True)

        # Pobierz następne pytanie z sesji (przez QuizSessionQuestion), wykluczając:
        # - pytania już odpowiedziane (po ID)
        # - pytania o tej samej treści co już odpowiedziane (po TEKŚCIE)
        session_question = QuizSessionQuestion.objects.filter(
            session=session
        ).exclude(
            question_id__in=answered_question_ids
        ).exclude(
            question__question_text__in=answered_texts
        ).select_related('question').order_by('order').first()

        if not session_question:
            return Response(
                {'error': 'No more questions available'},
                status=status.HTTP_404_NOT_FOUND
            )

        question = session_question.question
        generation_status = "pre_generated"
        print(f"📖 Fetched pre-generated question ID={question.id}")

    # 🚀 ADAPTIVE DIFFICULTY: Generuj na bieżąco (z unikaniem duplikatów po TEKŚCIE)
    else:
        try:
            difficulty_text = _convert_numeric_to_text_difficulty(session.current_difficulty)

            # Unikaj duplikatów po treści: sprawdzaj, czy w sesji już było pytanie o takiej samej treści
            seen_texts = set(
                QuizSessionQuestion.objects.filter(session=session)
                .select_related('question')
                .values_list('question__question_text', flat=True)
            )

            max_attempts = 7
            attempts = 0
            question = None
            created = False

            while attempts < max_attempts:
                # Generuj nowe pytanie
                question_data = generator.generate_question(
                    session.topic,
                    session.current_difficulty
                )

                # Znajdź lub utwórz GLOBALNE pytanie
                q, was_created = _find_or_create_global_question(
                    session.topic,
                    question_data,
                    difficulty_text,
                    user=request.user
                )

                # Sprawdź unikalność po TEKŚCIE w obrębie sesji
                if q.question_text not in seen_texts:
                    # Dodaj do sesji
                    order = QuizSessionQuestion.objects.filter(session=session).count()
                    _add_question_to_session(session, q, order=order)
                    question = q
                    created = was_created
                    break

                attempts += 1
                print(f"🔁 Duplicate by text detected in session, regenerating... (attempt {attempts})")

            if not question:
                return Response(
                    {'error': 'Failed to generate unique question'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            generation_status = "generated" if created else "reused"

        except Exception as e:
            print(f"❌ Error generating question: {e}")
            return Response(
                {'error': 'Failed to generate question'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    # Przygotuj odpowiedzi
    answers = [
        question.correct_answer,
        question.wrong_answer_1,
        question.wrong_answer_2,
        question.wrong_answer_3
    ]
    random.shuffle(answers)

    question_number = min(session.total_questions + 1, session.questions_count)
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
        'questions_count': session.questions_count,
        'questions_remaining': questions_remaining,
        'time_per_question': session.time_per_question,
        'use_adaptive_difficulty': session.use_adaptive_difficulty,
        'generation_status': generation_status,
        'difficulty_label': question.difficulty_level,
        'times_used': question.times_used,  # Dodatkowa info
        'success_rate': question.success_rate,  # Dodatkowa info
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    """Zapisz odpowiedź - aktualizuje statystyki GLOBALNEGO pytania"""
    question_id = request.data.get('question_id')
    selected_answer = request.data.get('selected_answer')
    response_time = request.data.get('response_time', 0)

    question = get_object_or_404(Question, id=question_id)

    # Znajdź sesję tego pytania dla tego użytkownika
    session_question = QuizSessionQuestion.objects.filter(
        question=question,
        session__user=request.user,
        session__is_completed=False
    ).select_related('session').first()

    if not session_question:
        return Response(
            {'error': 'Question not found in any active session'},
            status=status.HTTP_404_NOT_FOUND
        )

    session = session_question.session

    # Sprawdź czy user już odpowiedział W TEJ SESJI
    existing_answer = Answer.objects.filter(
        question=question,
        user=request.user,
        session=session
    ).first()

    if existing_answer:
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

    # Utwórz odpowiedź
    answer = Answer.objects.create(
        question=question,
        user=request.user,
        session=session,
        selected_answer=selected_answer,
        is_correct=is_correct,
        response_time=response_time
    )

    # Zaktualizuj statystyki sesji
    session.total_questions += 1
    if session.total_questions > session.questions_count:
        session.total_questions = session.questions_count

    if is_correct:
        session.correct_answers += 1
        session.current_streak += 1
    else:
        session.current_streak = 0

    # Adaptacyjna zmiana trudności
    previous_difficulty = session.current_difficulty
    difficulty_changed = False

    if session.use_adaptive_difficulty:
        recent_answers_objs = Answer.objects.filter(
            session=session
        ).order_by('-answered_at')[:difficulty_adapter.streak_threshold]

        recent_answers = [ans.is_correct for ans in reversed(list(recent_answers_objs))]
        new_difficulty = difficulty_adapter.adjust_difficulty(
            session.current_difficulty,
            recent_answers
        )

        if new_difficulty != session.current_difficulty:
            difficulty_changed = True
            print(f"🎯 Difficulty changed: {session.current_difficulty} → {new_difficulty}")
            session.current_difficulty = new_difficulty

    session.save()

    # ⭐ ZAKTUALIZUJ STATYSTYKI GLOBALNEGO PYTANIA
    question.update_stats(is_correct)
    print(f"📊 Question {question.id} stats: {question.total_answers} answers, {question.success_rate}% success")

    # Zaktualizuj profil użytkownika
    profile = request.user.profile
    profile.total_questions_answered += 1
    if is_correct:
        profile.total_correct_answers += 1
    if session.current_streak > profile.highest_streak:
        profile.highest_streak = session.current_streak
    profile.save()

    # Sprawdź czy quiz zakończony
    quiz_completed = session.total_questions >= session.questions_count

    if not quiz_completed:
        try:
            threading.Thread(
                target=_prepare_next_question_async,
                args=(session.id,),
                daemon=True
            ).start()
        except Exception as e:
            print(f"⚠️ Failed to spawn pre-generation thread: {e}")

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
        },
        'question_stats': {  # Dodatkowe info o pytaniu
            'times_used': question.times_used,
            'success_rate': question.success_rate
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_quiz(request, session_id):
    """Zakończ quiz przedwcześnie"""
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    if session.is_completed:
        return Response(
            {'error': 'Quiz already completed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    session.ended_at = timezone.now()
    session.is_completed = True
    session.save()

    return Response({
        'message': 'Quiz ended successfully',
        'session_id': session.id,
        'total_questions': session.total_questions,
        'correct_answers': session.correct_answers,
        'accuracy': session.accuracy
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_history(request):
    """
    Historia quizów użytkownika – zwraca { results, count, next, previous }.
    Obsługuje: topic, difficulty (easy/medium/hard), is_custom, order_by, page, page_size.
    """
    qs = QuizSession.objects.filter(user=request.user, is_completed=True)

    # --- Filtry ---
    topic = request.GET.get('topic')
    difficulty = request.GET.get('difficulty')  # 'easy' / 'medium' / 'hard'
    is_custom = request.GET.get('is_custom')    # 'true' / 'false' / ''

    if topic:
        qs = qs.filter(topic__icontains=topic)

    if difficulty in ['easy', 'medium', 'hard']:
        qs = qs.filter(initial_difficulty=difficulty)

    if is_custom in ['true', 'false']:
        # "custom" wg Twojej definicji w serializerze (niestandardowe ustawienia)
        # Nie mamy bezpośredniego pola, więc przefiltrujemy w Pythonie:
        ids = []
        for s in qs.only('id', 'questions_count', 'time_per_question', 'use_adaptive_difficulty'):
            custom = (s.questions_count != 10 or s.time_per_question != 30 or not s.use_adaptive_difficulty)
            if (is_custom == 'true' and custom) or (is_custom == 'false' and not custom):
                ids.append(s.id)
        qs = qs.filter(id__in=ids)

    # --- Sortowanie ---
    order_by = request.GET.get('order_by', '-started_at')
    allowed = [
        'started_at', '-started_at',
        'accuracy', '-accuracy',
        'topic', '-topic',
        'total_questions', '-total_questions'
    ]
    if order_by in allowed:
        qs = qs.order_by(order_by)

    # --- Paginacja ---
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 10))
    except ValueError:
        page_size = 10

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    data = QuizSessionSerializer(page_obj.object_list, many=True).data

    # Front używa booleans: hasNext/hasPrevious = response.data.next/previous
    return Response({
        'results': data,
        'count': paginator.count,
        'next': page_obj.has_next(),
        'previous': page_obj.has_previous(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_details(request, session_id):
    """Szczegóły zakończonego quizu wraz z pytaniami i odpowiedziami"""
    print(f"👤 Request from user: {request.user} (id={request.user.id})")
    print(f"🔍 Looking for session {session_id}...")

    session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    # Pobierz wszystkie odpowiedzi użytkownika wraz z pytaniami
    answers = Answer.objects.filter(
        session=session,
        user=request.user
    ).select_related('question').order_by('answered_at')

    print(f"📦 Found {answers.count()} answers for this session")

    # Użyj poprawnego serializera
    answers_data = AnswerSerializer(answers, many=True).data
    session_data = QuizSessionSerializer(session).data

    return Response({
        'session': session_data,
        'answers': answers_data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def questions_library(request):
    """
    Biblioteka wszystkich pytań – proste filtry i paginacja.
    Filtry: search, topic, difficulty (łatwy/średni/trudny + aliasy),
            success_min/max, used_min/max, has_explanation.
    Sort: created_at / -created_at / success_rate / -success_rate.
    Zwraca: { count, results }, difficulty_level = nazwa (PL).
    """

    def normalize_diff_token(token: str):
        t = (token or '').strip().lower()
        if t in ('łatwy', 'latwy', 'easy'):
            return 'łatwy'
        if t in ('średni', 'sredni', 'medium'):
            return 'średni'
        if t in ('trudny', 'hard'):
            return 'trudny'
        return None

    # ranking do sortowania po nazwie trudności (zostawiamy w razie rozszerzeń)
    difficulty_rank = Case(
        When(difficulty_level__iexact='łatwy', then=Value(1)),
        When(difficulty_level__iexact='latwy', then=Value(1)),
        When(difficulty_level__iexact='easy',  then=Value(1)),
        When(difficulty_level__iexact='średni', then=Value(2)),
        When(difficulty_level__iexact='sredni', then=Value(2)),
        When(difficulty_level__iexact='medium', then=Value(2)),
        When(difficulty_level__iexact='trudny', then=Value(3)),
        When(difficulty_level__iexact='hard',   then=Value(3)),
        default=Value(2), output_field=IntegerField()
    )

    # 👇 wyliczana skuteczność: (correct_answers_count / total_answers) * 100
    safe_total = Case(
        When(total_answers__gt=0, then=F('total_answers')),
        default=Value(1),
        output_field=FloatField()
    )
    success_rate_expr = ExpressionWrapper(
        100.0 * Coalesce(F('correct_answers_count'), Value(0.0)) / safe_total,
        output_field=FloatField()
    )

    qs = Question.objects.all().annotate(
        _difficulty_rank=difficulty_rank,
        _success_rate=success_rate_expr
    )

    # --- FILTRY ---
    topic = request.GET.get('topic')
    search = request.GET.get('search')
    diff_param = request.GET.get('difficulty')

    if topic:
        qs = qs.filter(topic__icontains=topic)

    if search:
        qs = qs.filter(
            Q(question_text__icontains=search) |
            Q(correct_answer__icontains=search) |
            Q(wrong_answer_1__icontains=search) |
            Q(wrong_answer_2__icontains=search) |
            Q(wrong_answer_3__icontains=search) |
            Q(explanation__icontains=search)
        )

    if diff_param:
        tokens = [normalize_diff_token(t) for t in diff_param.split(',')]
        wanted = {t for t in tokens if t}
        if wanted:
            qf = Q()
            if 'łatwy' in wanted:
                qf |= Q(difficulty_level__iexact='łatwy') | Q(difficulty_level__iexact='latwy') | Q(difficulty_level__iexact='easy')
            if 'średni' in wanted:
                qf |= Q(difficulty_level__iexact='średni') | Q(difficulty_level__iexact='sredni') | Q(difficulty_level__iexact='medium')
            if 'trudny' in wanted:
                qf |= Q(difficulty_level__iexact='trudny') | Q(difficulty_level__iexact='hard')
            qs = qs.filter(qf)

    # success rate 0..100
    smin = request.GET.get('success_min')
    smax = request.GET.get('success_max')
    try:
        if smin not in (None, ''):
            qs = qs.filter(_success_rate__gte=float(smin))
        if smax not in (None, ''):
            qs = qs.filter(_success_rate__lte=float(smax))
    except ValueError:
        pass

    # times_used
    umin = request.GET.get('used_min')
    umax = request.GET.get('used_max')
    try:
        if umin not in (None, ''):
            qs = qs.filter(times_used__gte=int(umin))
        if umax not in (None, ''):
            qs = qs.filter(times_used__lte=int(umax))
    except ValueError:
        pass

    # has_explanation
    has_expl = (request.GET.get('has_explanation') or '').lower()
    if has_expl in ('true', 'false'):
        if has_expl == 'true':
            qs = qs.filter(~Q(explanation__isnull=True) & ~Q(explanation__exact=''))
        else:
            qs = qs.filter(Q(explanation__isnull=True) | Q(explanation__exact=''))

    # --- SORTOWANIE (tylko data i skuteczność, zgodnie z prośbą) ---
    order_by = request.GET.get('order_by', '-created_at')
    mapping = {
        'created_at': 'created_at',
        '-created_at': '-created_at',
        'success_rate': '_success_rate',
        '-success_rate': '-_success_rate',
    }
    qs = qs.order_by(mapping.get(order_by, '-created_at'))

    # --- PAGINACJA ---
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1
    try:
        page_size = int(request.GET.get('page_size', 20))
    except ValueError:
        page_size = 20

    paginator = Paginator(qs, page_size)
    page_obj = paginator.get_page(page)

    # --- helper: ujednolicona nazwa poziomu ---
    def normalized_name(label):
        l = (label or '').strip().lower()
        if l in ('łatwy', 'latwy', 'easy'):
            return 'łatwy'
        if l in ('średni', 'sredni', 'medium'):
            return 'średni'
        if l in ('trudny', 'hard'):
            return 'trudny'
        return label or 'średni'

    # --- PAYLOAD ---
    results = []
    for q in page_obj.object_list:
        results.append({
            'id': q.id,
            'question_text': q.question_text,
            'topic': q.topic,
            'difficulty_level': normalized_name(q.difficulty_level),
            'correct_answer': q.correct_answer,
            'wrong_answer_1': q.wrong_answer_1,
            'wrong_answer_2': q.wrong_answer_2,
            'wrong_answer_3': q.wrong_answer_3,
            'explanation': q.explanation,
            'created_at': q.created_at,
            'stats': {
                'total_answers': q.total_answers,
                'correct_answers': getattr(q, 'correct_answers_count', None),
                'wrong_answers': (q.total_answers - getattr(q, 'correct_answers_count', 0))
                                  if q.total_answers is not None and getattr(q, 'correct_answers_count', None) is not None else None,
                'accuracy': getattr(q, 'success_rate', None) if getattr(q, 'success_rate', None) is not None else round(getattr(q, '_success_rate', 0.0), 2),
                'times_used': getattr(q, 'times_used', 0),
            }
        })

    return Response({
        'count': paginator.count,
        'results': results
    })

# ViewSet dla QuizSession
class QuizSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet dla sesji quizów - tylko odczyt"""
    serializer_class = QuizSessionSerializer
    permission_classes = [IsAuthenticated, IsQuizOwnerOrAdmin]

    def get_queryset(self):
        return QuizSession.objects.filter(user=self.request.user).order_by('-started_at')


@api_view(['GET'])
def quiz_api_root(request):
    """Bazowy endpoint API quiz"""
    return Response({
        'message': 'Quiz LLM API - GLOBALNE PYTANIA',
        'version': '2.0',
        'endpoints': {
            'start_quiz': '/api/quiz/start/',
            'get_question': '/api/quiz/question/<session_id>/',
            'submit_answer': '/api/quiz/answer/',
            'end_quiz': '/api/quiz/end/<session_id>/',
            'quiz_history': '/api/quiz/history/',
            'quiz_details': '/api/quiz/details/<session_id>/',
            'questions_library': '/api/quiz/questions/',
        },
        'features': {
            'global_questions': True,
            'deduplication': 'hash-based',
            'statistics': 'centralized'
        }
    })


# ViewSet dla QuizSession
class QuizSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet dla sesji quizów - tylko odczyt"""
    serializer_class = QuizSessionSerializer
    permission_classes = [IsAuthenticated, IsQuizOwnerOrAdmin]

    def get_queryset(self):
        return QuizSession.objects.filter(user=self.request.user).order_by('-started_at')


print("✅ Views.py loaded with GLOBAL QUESTIONS support!")