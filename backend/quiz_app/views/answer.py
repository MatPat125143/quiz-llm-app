import logging
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..models import Question, QuizSessionQuestion, Answer
from llm_integration.difficulty_adapter import DifficultyAdapter
from ..services.background_generator import BackgroundQuestionGenerator

logger = logging.getLogger(__name__)

difficulty_adapter = DifficultyAdapter()
bg_generator = BackgroundQuestionGenerator()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    question_id = request.data.get('question_id')
    selected_answer = request.data.get('selected_answer')
    response_time = request.data.get('response_time', 0)

    question = get_object_or_404(Question, id=question_id)

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

    # KRYTYCZNE: Sprawdź czy sesja już zakończona
    if session.is_completed:
        return Response({
            'error': 'Quiz already completed',
            'quiz_completed': True
        }, status=status.HTTP_400_BAD_REQUEST)

    # KRYTYCZNE: Sprawdź czy osiągnięto już limit pytań
    if session.total_questions >= session.questions_count:
        session.is_completed = True
        session.ended_at = timezone.now()
        session.save()
        return Response({
            'error': 'Quiz limit reached',
            'quiz_completed': True,
            'session_stats': {
                'total_questions': session.total_questions,
                'correct_answers': session.correct_answers,
                'accuracy': session.accuracy
            }
        })

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

    # Pusta odpowiedź (timeout) = zawsze błędna
    is_timeout = not bool(selected_answer)

    # KRYTYCZNE: Porównanie z trim() i normalizacją białych znaków
    if selected_answer:
        # Normalizuj obie strony: trim + usuń multiple spaces + lowercase dla porównania
        selected_normalized = ' '.join(selected_answer.strip().split())
        correct_normalized = ' '.join(question.correct_answer.strip().split())
        is_correct = selected_normalized == correct_normalized

        # Debug log jeżeli nie match
        if not is_correct:
            logger.debug(f"Wrong answer: '{selected_answer}' != '{question.correct_answer}'")
        else:
            logger.debug(f"Correct answer: '{selected_answer}'")
    else:
        is_correct = False

    answer = Answer.objects.create(
        question=question,
        user=request.user,
        session=session,
        selected_answer=selected_answer,
        is_correct=is_correct,
        response_time=response_time,
        difficulty_at_answer=session.current_difficulty
    )

    session.total_questions += 1
    if session.total_questions > session.questions_count:
        session.total_questions = session.questions_count

    if is_correct:
        session.correct_answers += 1
        session.current_streak += 1
    else:
        session.current_streak = 0

    # USUNIĘTO: Pre-generowanie przeniesione do get_question.py (PRZED wyświetleniem pytania)
    # Teraz pytania generują się ZANIM gracz zobaczy pytanie decydujące, a nie PO odpowiedzi

    previous_difficulty_level = None
    new_difficulty_level = None
    level_changed = False

    if session.use_adaptive_difficulty:
        recent_answers_objs = Answer.objects.filter(session=session).order_by('-answered_at')[:difficulty_adapter.streak_threshold]
        recent_answers = [ans.is_correct for ans in reversed(list(recent_answers_objs))]

        previous_level = difficulty_adapter.get_difficulty_level(session.current_difficulty)

        difficulty_result = difficulty_adapter.adjust_difficulty_with_level_check(
            session.current_difficulty,
            recent_answers
        )

        if difficulty_result['difficulty_changed']:
            session.current_difficulty = difficulty_result['new_difficulty']

            if difficulty_result['level_changed']:
                level_changed = True
                previous_difficulty_level = difficulty_result['previous_level']
                new_difficulty_level = difficulty_result['new_level']
                logger.info(f"Level change: {previous_difficulty_level} -> {new_difficulty_level}")

                # KASOWANIE NIEWYKORZYSTANYCH PYTAŃ ze starego poziomu
                answered_question_ids = list(Answer.objects.filter(
                    session=session
                ).values_list('question_id', flat=True))

                logger.debug(f"Deleting unused questions: answered_question_ids = {answered_question_ids}")
                logger.debug(f"Previous difficulty level: '{previous_difficulty_level}'")

                # Znajdź pytania do usunięcia
                questions_to_delete = QuizSessionQuestion.objects.filter(
                    session=session,
                    question__difficulty_level=previous_difficulty_level
                ).exclude(
                    question_id__in=answered_question_ids
                )

                count_to_delete = questions_to_delete.count()
                logger.debug(f"Found {count_to_delete} questions to delete")

                if count_to_delete > 0:
                    # Wypisz pytania które będą usunięte
                    for sq in questions_to_delete[:5]:  # Max 5 dla przejrzystości
                        logger.debug(f"Deleting question ID={sq.question.id}, difficulty='{sq.question.difficulty_level}'")

                # Pobierz ID pytań które będą usunięte
                deleted_question_ids = list(questions_to_delete.values_list('question_id', flat=True))

                deleted_count = questions_to_delete.delete()[0]

                if deleted_count > 0:
                    logger.info(f"Deleted {deleted_count} QuizSessionQuestion entries for '{previous_difficulty_level}'")

                    # KRYTYCZNE: Usuń także Question objects które nie mają ŻADNYCH odpowiedzi
                    if deleted_question_ids:
                        orphaned_from_difficulty_change = Question.objects.filter(
                            id__in=deleted_question_ids,
                            total_answers=0
                        )

                        for orphan_q in orphaned_from_difficulty_change:
                            # Sprawdź czy nie jest używane w innych aktywnych sesjach
                            used_in_active = QuizSessionQuestion.objects.filter(
                                question=orphan_q,
                                session__is_completed=False
                            ).exists()

                            if not used_in_active:
                                logger.info(f"Deleting orphaned Question ID={orphan_q.id} (difficulty change, total_answers=0)")
                                orphan_q.delete()
                else:
                    logger.warning(f"No questions deleted for level '{previous_difficulty_level}'")

                # GENEROWANIE NOWYCH PYTAŃ dla nowego poziomu
                # NOWE: HYBRYDOWA STRATEGIA - 3 sync + reszta async
                # KRYTYCZNE: Tylko jeśli quiz NIE jest zakończony
                questions_answered = session.total_questions
                questions_remaining = session.questions_count - questions_answered

                logger.info(f"Level change: answered={questions_answered}, total_limit={session.questions_count}, remaining={questions_remaining}")

                # NOWE: Jeśli quiz się kończy (0 lub 1 pytanie pozostało), NIE generuj nowych pytań
                if questions_remaining <= 0:
                    logger.info(f"Quiz ending - skipping question generation (remaining={questions_remaining})")
                elif questions_remaining > 0:
                    # Sprawdź ile pytań już jest w kolejce (niewykorzystanych)
                    unused_questions_count = QuizSessionQuestion.objects.filter(
                        session=session
                    ).exclude(
                        question_id__in=answered_question_ids
                    ).count()

                    logger.debug(f"Unused questions in queue: {unused_questions_count}")

                    # Oblicz ile faktycznie potrzeba wygenerować
                    actually_needed = max(0, questions_remaining - unused_questions_count)

                    if actually_needed > 0:
                        # NOWE: Generuj 3 pytania SYNC (dla instant availability), resztę ASYNC
                        sync_count = min(3, actually_needed)

                        logger.info(f"Generating {sync_count} questions sync for new level '{new_difficulty_level}' (total need: {actually_needed})")

                        try:
                            generated = bg_generator.generate_adaptive_questions_sync(
                                session=session,
                                new_difficulty_level=new_difficulty_level,
                                count=sync_count
                            )
                            logger.info(f"Generated {generated} questions sync for level '{new_difficulty_level}'")

                            # Jeżeli potrzeba więcej niż sync_count, uruchom async generation
                            if actually_needed > sync_count:
                                async_count = actually_needed - sync_count
                                logger.info(f"Starting async generation of {async_count} more questions for level '{new_difficulty_level}'")

                                # Użyj generate_remaining_questions_async
                                current_total = QuizSessionQuestion.objects.filter(session=session).count()
                                bg_generator.generate_remaining_questions_async(
                                    session_id=session.id,
                                    total_needed=session.questions_count,
                                    already_generated=current_total
                                )

                        except Exception as e:
                            logger.error(f"Error generating adaptive questions: {e}")
                    else:
                        logger.info(f"No need to generate questions - enough in queue (need: {actually_needed}, have: {unused_questions_count})")

    session.save()
    question.update_stats(is_correct)

    quiz_completed = session.total_questions >= session.questions_count

    if quiz_completed:
        session.is_completed = True
        session.ended_at = timezone.now()
        session.save()

        # USUWANIE NIEWYKORZYSTANYCH PYTAŃ po zakończeniu gry
        answered_ids = Answer.objects.filter(session=session).values_list('question_id', flat=True)
        unused_session_questions = QuizSessionQuestion.objects.filter(
            session=session
        ).exclude(
            question_id__in=answered_ids
        )

        # Pobierz ID pytań które NIE zostały użyte w tej sesji
        unused_question_ids = list(unused_session_questions.values_list('question_id', flat=True))

        # Usuń QuizSessionQuestion entries
        unused_count = unused_session_questions.count()
        if unused_count > 0:
            unused_session_questions.delete()
            logger.info(f"Cleaned up {unused_count} QuizSessionQuestion entries")

        # KRYTYCZNE: Usuń Question objects bez ŻADNYCH odpowiedzi
        # Tylko te które nie są używane w innych aktywnych sesjach
        if unused_question_ids:
            from django.db.models import Q

            # Znajdź pytania które:
            # 1. Są w unused_question_ids (nie zostały użyte w tej sesji)
            # 2. total_answers = 0 (NIKT na nie nie odpowiedział)
            orphaned_questions = Question.objects.filter(
                id__in=unused_question_ids,
                total_answers=0
            )

            # Sprawdź czy nie są używane w innych AKTYWNYCH sesjach
            for orphan_q in orphaned_questions:
                # Sprawdź czy pytanie jest w jakiejś AKTYWNEJ sesji
                used_in_active = QuizSessionQuestion.objects.filter(
                    question=orphan_q,
                    session__is_completed=False
                ).exists()

                if not used_in_active:
                    # Bezpieczne usunięcie - pytanie nie jest nigdzie używane
                    logger.info(f"Deleting orphaned Question ID={orphan_q.id} (total_answers=0, not in active sessions)")
                    orphan_q.delete()
                else:
                    logger.debug(f"Keeping Question ID={orphan_q.id} (used in active session)")

        profile = request.user.profile
        profile.total_quizzes_played += 1

        completed_answers = Answer.objects.filter(user=request.user, session__is_completed=True)
        profile.total_questions_answered = completed_answers.count()
        profile.total_correct_answers = completed_answers.filter(is_correct=True).count()

        from ..models import QuizSession
        completed_sessions = QuizSession.objects.filter(user=request.user, is_completed=True)
        max_streak = 0
        for s in completed_sessions:
            session_answers = Answer.objects.filter(session=s).order_by('answered_at')
            current_streak = 0
            for ans in session_answers:
                if ans.is_correct:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0
        profile.highest_streak = max_streak
        profile.save()

        logger.info(f"Quiz {session.id} completed")

    return Response({
        'is_correct': is_correct,
        'was_timeout': is_timeout,
        'correct_answer': question.correct_answer,
        'explanation': question.explanation,
        'current_streak': session.current_streak,
        'quiz_completed': quiz_completed,
        'difficulty_changed': level_changed,
        'previous_difficulty': previous_difficulty_level if level_changed else None,
        'new_difficulty': new_difficulty_level if level_changed else None,
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
