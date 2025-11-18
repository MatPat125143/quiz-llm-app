from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.cache import cache
from ..models import Question, QuizSessionQuestion, Answer
from ..services.answer_service import AnswerService
from llm_integration.difficulty_adapter import DifficultyAdapter
import threading

answer_service = AnswerService()
difficulty_adapter = DifficultyAdapter()


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

    previous_difficulty = session.current_difficulty
    difficulty_level_changed = False
    previous_difficulty_level = None
    new_difficulty_level = None

    if session.use_adaptive_difficulty:
        recent_answers_objs = Answer.objects.filter(
            session=session
        ).order_by('-answered_at')[:difficulty_adapter.streak_threshold]

        recent_answers = [ans.is_correct for ans in reversed(list(recent_answers_objs))]

        difficulty_result = difficulty_adapter.adjust_difficulty_with_level_check(
            session.current_difficulty,
            recent_answers
        )

        if difficulty_result['difficulty_changed']:
            print(f"📊 Difficulty: {session.current_difficulty} → {difficulty_result['new_difficulty']}")
            session.current_difficulty = difficulty_result['new_difficulty']

            if difficulty_result['level_changed']:
                difficulty_level_changed = True
                previous_difficulty_level = difficulty_result['previous_level']
                new_difficulty_level = difficulty_result['new_level']

                print(f"🎯 Level changed: {previous_difficulty_level} → {new_difficulty_level}")

                cache.delete(f'next_q:{session.id}')

    session.save()

    question.update_stats(is_correct)
    print(f"📊 Question ID={question.id}: {question.total_answers} answers, {question.success_rate}%")

    quiz_completed = session.total_questions >= session.questions_count

    if quiz_completed:
        session.is_completed = True
        session.ended_at = timezone.now()
        session.save()

        profile = request.user.profile
        profile.total_quizzes_played += 1

        completed_answers = Answer.objects.filter(
            user=request.user,
            session__is_completed=True
        )

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

        print(f"🏁 Quiz {session.id} completed")
    else:
        try:
            answered_count = Answer.objects.filter(session=session).count()
            TARGET_BUFFER_SIZE = 2
            BATCH_SIZE = 4

            if session.use_adaptive_difficulty:

                if difficulty_level_changed:
                    to_generate = min(BATCH_SIZE, session.questions_count - answered_count)
                    print(f"🔄 Generating {to_generate} questions for new level")

                    def generate_new_batch_after_difficulty_change():
                        answer_service.generate_new_batch_after_difficulty_change(
                            session_id=session.id,
                            to_generate=to_generate
                        )

                    threading.Thread(target=generate_new_batch_after_difficulty_change, daemon=True).start()

                else:
                    unanswered_count = QuizSessionQuestion.objects.filter(
                        session=session
                    ).exclude(
                        question_id__in=Answer.objects.filter(session=session)
                        .values_list('question_id', flat=True)
                    ).count()

                    current_level = difficulty_adapter.get_difficulty_level(session.current_difficulty)
                    remaining_to_complete = session.questions_count - answered_count

                    if remaining_to_complete > TARGET_BUFFER_SIZE and unanswered_count < TARGET_BUFFER_SIZE:
                        needed = TARGET_BUFFER_SIZE - unanswered_count
                        print(f"🔄 Generating {needed} backup question(s)")

                        def generate_backup_questions():
                            answer_service.generate_backup_questions(
                                session_id=session.id,
                                needed=needed
                            )

                        threading.Thread(target=generate_backup_questions, daemon=True).start()

            else:
                generated_count = session.questions_generated_count
                remaining_in_batch = generated_count - answered_count
                if remaining_in_batch <= 3 and generated_count < session.questions_count:
                    to_generate = min(4, session.questions_count - generated_count)
                    print(f"📚 Fixed mode: generating {to_generate} questions")

                    def generate_next_batch():
                        answer_service.generate_next_batch_fixed_mode(
                            session_id=session.id,
                            to_generate=to_generate
                        )

                    threading.Thread(target=generate_next_batch, daemon=True).start()

        except Exception as e:
            print(f"⚠️ Failed to spawn generation thread: {e}")

    return Response({
        'is_correct': is_correct,
        'correct_answer': question.correct_answer,
        'explanation': question.explanation,
        'current_streak': session.current_streak,
        'quiz_completed': quiz_completed,
        'difficulty_changed': difficulty_level_changed,
        'previous_difficulty': previous_difficulty if difficulty_level_changed else None,
        'new_difficulty': session.current_difficulty if difficulty_level_changed else None,
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