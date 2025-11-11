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
from llm_integration.embeddings_service import EmbeddingsService
from cache_manager.question_cache import QuestionCache
import json
import random
import threading
import time
import hashlib
import numpy as np

# Inicjalizuj wszystkie serwisy
generator = QuestionGenerator()
difficulty_adapter = DifficultyAdapter()
embeddings_service = EmbeddingsService()
question_cache = QuestionCache()


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


def _find_or_create_global_question(topic, question_data, difficulty_text, user=None, subtopic=None,
                                    knowledge_level=None):
    """
    Znajdź lub utwórz GLOBALNE pytanie używając hash'a i embeddings.
    """
    try:
        # Oblicz hash contentu (uwzględniając subtopic i knowledge_level)
        content = f"{question_data['question']}{question_data['correct_answer']}{topic}{subtopic or ''}{knowledge_level or ''}{difficulty_text}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Szukaj po hash'u - instant deduplikacja składniowa!
        question, created = Question.objects.get_or_create(
            content_hash=content_hash,
            defaults={
                'topic': topic,
                'subtopic': subtopic,
                'knowledge_level': knowledge_level,
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

        # ✨ Generuj embedding dla nowego pytania (jeśli embeddingi dostępne)
        if created and embeddings_service.is_available():
            try:
                embedding = embeddings_service.encode_question(question_data['question'])
                if embedding is not None:
                    print(
                        f"📝 Utworzono nowe globalne pytanie ID={question.id} z embeddingiem (subtopic={subtopic}, knowledge_level={knowledge_level})")
                else:
                    print(f"📝 Utworzono pytanie bez embeddingu ID={question.id} (embedding failed)")
            except Exception as e:
                print(f"⚠️ Nie udało się wygenerować embeddingu: {e}")
                print(f"📝 Utworzono pytanie bez embeddingu ID={question.id}")
        elif created:
            print(
                f"📝 Utworzono nowe globalne pytanie ID={question.id} (embeddings not available, subtopic={subtopic}, knowledge_level={knowledge_level})")
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
    Dodaje pytanie do sesji quizu, ale zapobiega duplikatom na poziomie treści i semantyki.
    """
    # Sprawdź czy to pytanie już jest w tej sesji (deduplikacja składniowa po ID)
    existing = QuizSessionQuestion.objects.filter(
        session=session,
        question=question
    ).exists()

    if existing:
        print(f"⚠️ Pytanie {question.id} już istnieje w sesji {session.id} - pomijam")
        return None

    # ✨ Sprawdź podobieństwo semantyczne z innymi pytaniami w sesji (jeśli embeddingi dostępne)
    if embeddings_service.is_available():
        try:
            # Pobierz wszystkie pytania z tej sesji
            session_questions = QuizSessionQuestion.objects.filter(session=session).select_related('question')

            if session_questions.exists():
                # Wygeneruj embedding dla nowego pytania
                new_embedding = embeddings_service.encode_question(question.question_text)

                if new_embedding is not None:
                    # Sprawdź podobieństwo z każdym pytaniem w sesji
                    for sq in session_questions:
                        existing_embedding = embeddings_service.encode_question(sq.question.question_text)

                        if existing_embedding is not None:
                            # Oblicz cosine similarity
                            similarity = np.dot(new_embedding, existing_embedding) / (
                                    np.linalg.norm(new_embedding) * np.linalg.norm(existing_embedding)
                            )

                            # Jeśli podobieństwo > 0.85 (85%), uznaj za duplikat semantyczny
                            if similarity > 0.85:
                                print(
                                    f"⚠️ Pytanie {question.id} jest semantycznie podobne do pytania {sq.question.id} (similarity={similarity:.2f}) - pomijam")
                                return None

        except Exception as e:
            print(f"⚠️ Nie udało się sprawdzić podobieństwa semantycznego: {e}")
            # Kontynuuj bez sprawdzania podobieństwa

    # Dodaj pytanie do sesji
    session_question = QuizSessionQuestion.objects.create(
        session=session,
        question=question,
        order=order
    )

    print(f"✅ Dodano pytanie {question.id} do sesji {session.id} (order={order})")
    return session_question


def _has_user_answered_question(user, question, session=None):
    """
    Sprawdza czy użytkownik już odpowiadał na to pytanie.
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
    W tle: przygotuj i zcache'uj następne pytanie (ADAPTIVE mode - pojedyncze pytania).
    """
    try:
        session = QuizSession.objects.get(id=session_id)
        if session.is_completed:
            return

        # Jeśli już czeka w cache – nie rób nic
        if cache.get(f'next_q:{session.id}'):
            return

        # Zbierz już „widziane" treści
        seen_texts = set(
            QuizSessionQuestion.objects.filter(session=session)
            .select_related('question')
            .values_list('question__question_text', flat=True)
        )
        seen_texts |= set(
            Answer.objects.filter(session=session, user=session.user)
            .values_list('question__question_text', flat=True)
        )

        difficulty_text = _convert_numeric_to_text_difficulty(session.current_difficulty)

        # ✨ Sprawdź cache przed generowaniem przez AI
        cached_question_data = question_cache.get_cached_question(
            topic=session.topic,
            difficulty=difficulty_text,
            subtopic=session.subtopic,
            knowledge_level=session.knowledge_level
        )

        if cached_question_data:
            print(f"⚡ Znaleziono pytanie w cache dla {session.topic}/{difficulty_text}")
            q, created = _find_or_create_global_question(
                session.topic,
                cached_question_data,
                difficulty_text,
                user=session.user,
                subtopic=session.subtopic,
                knowledge_level=session.knowledge_level
            )
            if q.question_text not in seen_texts:
                order = QuizSessionQuestion.objects.filter(session=session).count()
                _add_question_to_session(session, q, order=order)
                _cache_next_question_payload(session, q)
                return

        # Generuj nowe pytanie przez AI
        max_attempts, attempts = 7, 0
        while attempts < max_attempts:
            qdata = generator.generate_question(
                session.topic,
                session.current_difficulty,
                subtopic=session.subtopic,
                knowledge_level=session.knowledge_level
            )

            # ✨ Zapisz do cache
            question_cache.cache_question(
                topic=session.topic,
                difficulty=difficulty_text,
                question_data=qdata,
                subtopic=session.subtopic,
                knowledge_level=session.knowledge_level
            )

            q, created = _find_or_create_global_question(
                session.topic,
                qdata,
                difficulty_text,
                user=session.user,
                subtopic=session.subtopic,
                knowledge_level=session.knowledge_level
            )
            if q.question_text not in seen_texts:
                order = QuizSessionQuestion.objects.filter(session=session).count()
                _add_question_to_session(session, q, order=order)
                _cache_next_question_payload(session, q)
                return
            attempts += 1
            print(f"🔁 (pre-gen) duplicate by text, retry {attempts}/{max_attempts}")

        # Fallback
        fallback = Question.objects.filter(
            topic=session.topic,
            subtopic=session.subtopic if session.subtopic else None,
            knowledge_level=session.knowledge_level
        ).exclude(question_text__in=seen_texts).order_by('-times_used').first()

        if not fallback and session.subtopic:
            fallback = Question.objects.filter(
                topic=session.topic,
                knowledge_level=session.knowledge_level
            ).exclude(question_text__in=seen_texts).order_by('-times_used').first()

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
    subtopic = request.data.get('subtopic', '')
    knowledge_level = request.data.get('knowledge_level', 'high_school')
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
        subtopic=subtopic if subtopic else None,
        knowledge_level=knowledge_level,
        initial_difficulty=difficulty,
        current_difficulty=initial_difficulty,
        questions_count=questions_count,
        time_per_question=time_per_question,
        use_adaptive_difficulty=use_adaptive_difficulty,
        questions_generated_count=0
    )

    profile = request.user.profile
    profile.total_quizzes_played += 1
    profile.save()

    # 🎯 PRE-GENERUJ PIERWSZĄ SERIĘ (4 pytania) - dla OBU trybów!
    batch_size = 4
    to_generate = min(batch_size, questions_count)
    print(f"📚 Generating first batch of {to_generate} questions (adaptive={use_adaptive_difficulty})")

    try:
        # Wygeneruj pierwszą serię pytań
        all_questions_data = generator.generate_multiple_questions(
            topic,
            initial_difficulty,
            to_generate,
            subtopic=subtopic if subtopic else None,
            knowledge_level=knowledge_level
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
                user=request.user,
                subtopic=subtopic if subtopic else None,
                knowledge_level=knowledge_level
            )

            if was_created:
                created_count += 1
            else:
                reused_count += 1

            # Dodaj pytanie do sesji
            _add_question_to_session(session, question, order=order)

        session.questions_generated_count = to_generate
        session.save(update_fields=['questions_generated_count'])

        print(f"✅ Pre-generated first batch: {created_count} new, {reused_count} reused")

    except Exception as e:
        print(f"❌ Error pre-generating questions: {e}")
        import traceback
        traceback.print_exc()

    return Response({
        'session_id': session.id,
        'message': 'Quiz started successfully!',
        'topic': topic,
        'subtopic': subtopic,
        'knowledge_level': knowledge_level,
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

    # 📖 POBIERZ PYTANIE Z PRE-GENEROWANYCH (obie tryby używają tego samego mechanizmu)
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

    # 🔄 Jeśli nie ma pytania, czekaj max 10 sekund (może być w trakcie generowania)
    if not session_question:
        max_wait_time = 10  # sekund
        poll_interval = 0.5  # sekund
        waited = 0

        print(f"⏳ No question ready, waiting up to {max_wait_time}s for generation...")

        while waited < max_wait_time:
            time.sleep(poll_interval)
            waited += poll_interval

            # Sprawdź ponownie czy pytanie się pojawiło
            session_question = QuizSessionQuestion.objects.filter(
                session=session
            ).exclude(
                question_id__in=answered_question_ids
            ).exclude(
                question__question_text__in=answered_texts
            ).select_related('question').order_by('order').first()

            if session_question:
                print(f"⏱️ Question appeared after waiting {waited}s")
                break

        # Jeśli nadal nie ma pytania po 10 sekundach
        if not session_question:
            print(f"❌ No question available after {max_wait_time}s wait")
            return Response(
                {'error': 'No more questions available. Please try again or contact support.'},
                status=status.HTTP_404_NOT_FOUND
            )

    question = session_question.question
    generation_status = "pre_generated"
    print(f"📖 Fetched pre-generated question ID={question.id} (adaptive={session.use_adaptive_difficulty})")

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
        'times_used': question.times_used,
        'success_rate': question.success_rate,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    """Zapisz odpowiedź - aktualizuje statystyki GLOBALNEGO pytania i generuje kolejne pytanie"""
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
        response_time=response_time,
        difficulty_at_answer=session.current_difficulty
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

            # 🔥 WAŻNE: Usuń pre-wygenerowane pytanie z cache, bo ma starą trudność!
            cache.delete(f'next_q:{session.id}')
            print(f"🗑️ Cleared cached question due to difficulty change")

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

    if quiz_completed:
        session.is_completed = True
        session.ended_at = timezone.now()
        session.save()
        print(f"🏁 Quiz {session.id} completed!")
    else:
        # 🆕 GENERUJ KOLEJNE PYTANIA PO UDZIELENIU ODPOWIEDZI
        try:
            answered_count = Answer.objects.filter(session=session).count()
            generated_count = session.questions_generated_count
            batch_size = 4

            # 🎯 TRYB ADAPTIVE - inteligentne generowanie
            if session.use_adaptive_difficulty:

                # WAŻNE: Dopiero po 4+ odpowiedziach reaguj na zmiany trudności
                # Pytania 1-4 korzystają z początkowej serii (nie usuwamy pytań)
                if answered_count >= 4:
                    # SCENARIUSZ A: Trudność się ZMIENIŁA → Wygeneruj NOWĄ SERIĘ na nowym poziomie
                    if difficulty_changed:
                        to_generate = min(batch_size, session.questions_count - answered_count)
                        print(f"🔄 Adaptive mode - difficulty changed, generating NEW BATCH of {to_generate} questions")

                        def generate_new_batch_after_difficulty_change():
                            try:
                                session_refresh = QuizSession.objects.get(id=session.id)

                                # Usuń nieużyte pytania ze starej serii (z poprzedniej trudności)
                                unused_questions = QuizSessionQuestion.objects.filter(
                                    session=session_refresh
                                ).exclude(
                                    question_id__in=Answer.objects.filter(session=session_refresh)
                                    .values_list('question_id', flat=True)
                                )
                                deleted_count = unused_questions.count()
                                unused_questions.delete()
                                print(f"🗑️ Deleted {deleted_count} unused questions from previous difficulty level")

                                # Wygeneruj nową serię na nowym poziomie trudności
                                all_questions_data = generator.generate_multiple_questions(
                                    session_refresh.topic,
                                    session_refresh.current_difficulty,
                                    to_generate,
                                    subtopic=session_refresh.subtopic,
                                    knowledge_level=session_refresh.knowledge_level
                                )

                                difficulty_text = _convert_numeric_to_text_difficulty(
                                    session_refresh.current_difficulty)

                                # Pobierz już widziane teksty pytań (żeby nie duplikować)
                                seen_texts = set(
                                    Answer.objects.filter(session=session_refresh)
                                    .values_list('question__question_text', flat=True)
                                )

                                for i, question_data in enumerate(all_questions_data):
                                    q, created = _find_or_create_global_question(
                                        session_refresh.topic,
                                        question_data,
                                        difficulty_text,
                                        user=session_refresh.user,
                                        subtopic=session_refresh.subtopic,
                                        knowledge_level=session_refresh.knowledge_level
                                    )

                                    # Sprawdź czy pytanie nie było już pokazane (po treści)
                                    if q.question_text not in seen_texts:
                                        order = QuizSessionQuestion.objects.filter(session=session_refresh).count()
                                        _add_question_to_session(session_refresh, q, order=order)
                                        seen_texts.add(q.question_text)

                                # Ustaw licznik na liczbę pytań które gracz już odpowiedział + nowa seria
                                session_refresh.questions_generated_count = answered_count + to_generate
                                session_refresh.save(update_fields=['questions_generated_count'])
                                print(f"✅ Generated NEW batch of {to_generate} questions for new difficulty level")

                            except Exception as e:
                                print(f"❌ Error generating new batch after difficulty change: {e}")
                                import traceback
                                traceback.print_exc()

                        threading.Thread(target=generate_new_batch_after_difficulty_change, daemon=True).start()

                    # SCENARIUSZ B: Trudność się NIE ZMIENIŁA → Generuj POJEDYNCZE pytania
                    else:
                        print(
                            f"🔄 Adaptive mode - same difficulty, answered {answered_count} questions, generating single question")
                        threading.Thread(
                            target=_prepare_next_question_async,
                            args=(session.id,),
                            daemon=True
                        ).start()
                # Dla pierwszych 4 pytań nie generuj nic - używamy początkowej serii
                # Ignorujemy zmiany trudności w tym okresie (pytania są już wygenerowane)
                else:
                    print(
                        f"📖 Adaptive mode - using initial batch (answered {answered_count}/4) - ignoring difficulty changes")

            # 🎯 TRYB FIXED - serie po 4 pytania
            else:
                # Jeśli zostały 3 pytania z obecnej serii, wygeneruj kolejną serię
                remaining_in_batch = generated_count - answered_count
                if remaining_in_batch <= 3 and generated_count < session.questions_count:
                    to_generate = min(batch_size, session.questions_count - generated_count)
                    print(
                        f"📚 Fixed mode - generating next batch of {to_generate} questions (remaining: {remaining_in_batch})")

                    def generate_next_batch():
                        try:
                            session_refresh = QuizSession.objects.get(id=session.id)
                            all_questions_data = generator.generate_multiple_questions(
                                session_refresh.topic,
                                session_refresh.current_difficulty,
                                to_generate,
                                subtopic=session_refresh.subtopic,
                                knowledge_level=session_refresh.knowledge_level
                            )

                            difficulty_text = _convert_numeric_to_text_difficulty(session_refresh.current_difficulty)

                            for i, question_data in enumerate(all_questions_data):
                                q, created = _find_or_create_global_question(
                                    session_refresh.topic,
                                    question_data,
                                    difficulty_text,
                                    user=session_refresh.user,
                                    subtopic=session_refresh.subtopic,
                                    knowledge_level=session_refresh.knowledge_level
                                )
                                order = session_refresh.questions_generated_count + i
                                _add_question_to_session(session_refresh, q, order=order)

                            session_refresh.questions_generated_count += to_generate
                            session_refresh.save(update_fields=['questions_generated_count'])
                            print(f"✅ Generated next batch of {to_generate} questions")

                        except Exception as e:
                            print(f"❌ Error generating next batch: {e}")
                            import traceback
                            traceback.print_exc()

                    threading.Thread(target=generate_next_batch, daemon=True).start()

        except Exception as e:
            print(f"⚠️ Failed to spawn question generation thread: {e}")
            import traceback
            traceback.print_exc()

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
        'question_stats': {
            'times_used': question.times_used,
            'success_rate': question.success_rate
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_quiz(request, session_id):
    """
    Zakończ quiz przedwcześnie.
    UWAGA: Jeśli quiz nie jest ukończony (total_questions < questions_count),
    sesja oraz wszystkie powiązane dane zostaną USUNIĘTE z bazy.
    """
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    if session.is_completed:
        return Response(
            {'error': 'Quiz already completed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Jeśli gracz nie ukończył wszystkich pytań, USUŃ sesję
    if session.total_questions < session.questions_count:
        print(
            f"🗑️ Deleting incomplete session {session.id} (answered {session.total_questions}/{session.questions_count})")

        # Usuń odpowiedzi
        Answer.objects.filter(session=session).delete()

        # Usuń powiązania pytanie-sesja
        QuizSessionQuestion.objects.filter(session=session).delete()

        # Usuń sesję
        session.delete()

        # Zmniejsz licznik quizów w profilu użytkownika
        profile = request.user.profile
        if profile.total_quizzes_played > 0:
            profile.total_quizzes_played -= 1
            profile.save()

        return Response({
            'message': 'Incomplete quiz session deleted',
            'deleted': True
        })

    # Jeśli ukończył wszystkie pytania, oznacz jako ukończony
    session.ended_at = timezone.now()
    session.is_completed = True
    session.save()

    return Response({
        'message': 'Quiz ended successfully',
        'session_id': session.id,
        'total_questions': session.total_questions,
        'correct_answers': session.correct_answers,
        'accuracy': session.accuracy,
        'deleted': False
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_history(request):
    """
    Historia quizów użytkownika – zwraca { results, count, next, previous }.
    """
    qs = QuizSession.objects.filter(user=request.user, is_completed=True)

    # Filtry
    topic = request.GET.get('topic')
    difficulty = request.GET.get('difficulty')
    is_custom = request.GET.get('is_custom')

    if topic:
        qs = qs.filter(topic__icontains=topic)

    if difficulty in ['easy', 'medium', 'hard']:
        qs = qs.filter(initial_difficulty=difficulty)

    if is_custom in ['true', 'false']:
        ids = []
        for s in qs.only('id', 'questions_count', 'time_per_question', 'use_adaptive_difficulty'):
            custom = (s.questions_count != 10 or s.time_per_question != 30 or not s.use_adaptive_difficulty)
            if (is_custom == 'true' and custom) or (is_custom == 'false' and not custom):
                ids.append(s.id)
        qs = qs.filter(id__in=ids)

    # Sortowanie
    order_by = request.GET.get('order_by', '-started_at')
    allowed = ['started_at', '-started_at', 'accuracy', '-accuracy', 'topic', '-topic', 'total_questions',
               '-total_questions']
    if order_by in allowed:
        qs = qs.order_by(order_by)

    # Paginacja
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

    try:
        user_role = request.user.profile.role
    except Exception:
        user_role = 'user'

    if user_role == 'admin':
        session = get_object_or_404(QuizSession, id=session_id)
    else:
        session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    answers = Answer.objects.filter(session=session).select_related('question').order_by('answered_at')

    print(f"📦 Found {answers.count()} answers for this session")

    answers_data = AnswerSerializer(answers, many=True).data
    session_data = QuizSessionSerializer(session).data

    difficulty_progress = []
    if session.use_adaptive_difficulty:
        for i, ans in enumerate(answers):
            difficulty_progress.append({
                "question_number": i + 1,
                "answered_at": ans.answered_at,
                "difficulty": float(ans.difficulty_at_answer)
            })

    return Response({
        'session': session_data,
        'answers': answers_data,
        'difficulty_progress': difficulty_progress
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def questions_library(request):
    """
    Biblioteka wszystkich pytań – proste filtry i paginacja.
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

    difficulty_rank = Case(
        When(difficulty_level__iexact='łatwy', then=Value(1)),
        When(difficulty_level__iexact='latwy', then=Value(1)),
        When(difficulty_level__iexact='easy', then=Value(1)),
        When(difficulty_level__iexact='średni', then=Value(2)),
        When(difficulty_level__iexact='sredni', then=Value(2)),
        When(difficulty_level__iexact='medium', then=Value(2)),
        When(difficulty_level__iexact='trudny', then=Value(3)),
        When(difficulty_level__iexact='hard', then=Value(3)),
        default=Value(2), output_field=IntegerField()
    )

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

    # Filtry
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
                qf |= Q(difficulty_level__iexact='łatwy') | Q(difficulty_level__iexact='latwy') | Q(
                    difficulty_level__iexact='easy')
            if 'średni' in wanted:
                qf |= Q(difficulty_level__iexact='średni') | Q(difficulty_level__iexact='sredni') | Q(
                    difficulty_level__iexact='medium')
            if 'trudny' in wanted:
                qf |= Q(difficulty_level__iexact='trudny') | Q(difficulty_level__iexact='hard')
            qs = qs.filter(qf)

    # Success rate filters
    smin = request.GET.get('success_min')
    smax = request.GET.get('success_max')
    try:
        if smin not in (None, ''):
            qs = qs.filter(_success_rate__gte=float(smin))
        if smax not in (None, ''):
            qs = qs.filter(_success_rate__lte=float(smax))
    except ValueError:
        pass

    # Times used filters
    umin = request.GET.get('used_min')
    umax = request.GET.get('used_max')
    try:
        if umin not in (None, ''):
            qs = qs.filter(times_used__gte=int(umin))
        if umax not in (None, ''):
            qs = qs.filter(times_used__lte=int(umax))
    except ValueError:
        pass

    # Has explanation filter
    has_expl = (request.GET.get('has_explanation') or '').lower()
    if has_expl in ('true', 'false'):
        if has_expl == 'true':
            qs = qs.filter(~Q(explanation__isnull=True) & ~Q(explanation__exact=''))
        else:
            qs = qs.filter(Q(explanation__isnull=True) | Q(explanation__exact=''))

    # Sortowanie
    order_by = request.GET.get('order_by', '-created_at')
    mapping = {
        'created_at': 'created_at',
        '-created_at': '-created_at',
        'success_rate': '_success_rate',
        '-success_rate': '-_success_rate',
    }
    qs = qs.order_by(mapping.get(order_by, '-created_at'))

    # Paginacja
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

    def normalized_name(label):
        l = (label or '').strip().lower()
        if l in ('łatwy', 'latwy', 'easy'):
            return 'łatwy'
        if l in ('średni', 'sredni', 'medium'):
            return 'średni'
        if l in ('trudny', 'hard'):
            return 'trudny'
        return label or 'średni'

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
                'accuracy': getattr(q, 'success_rate', None) if getattr(q, 'success_rate', None) is not None else round(
                    getattr(q, '_success_rate', 0.0), 2),
                'times_used': getattr(q, 'times_used', 0),
            }
        })

    return Response({
        'count': paginator.count,
        'results': results
    })


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
        'message': 'Quiz LLM API - GLOBALNE PYTANIA + EMBEDDINGS + CACHE + ADAPTIVE BATCHING',
        'version': '3.1',
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
            'deduplication': 'hash-based + semantic (embeddings)',
            'statistics': 'centralized',
            'caching': 'question_cache',
            'batch_generation': {
                'fixed': 'Series of 4 questions, trigger at ≤2 remaining',
                'adaptive': 'Initial series of 4, then single questions OR new series on difficulty change'
            },
            'subtopics': True,
            'knowledge_levels': True,
            'race_condition_fix': True
        }
    })


print("✅ Views.py loaded with EMBEDDINGS + CACHE + SUBTOPICS + KNOWLEDGE LEVELS + ADAPTIVE BATCHING support!")