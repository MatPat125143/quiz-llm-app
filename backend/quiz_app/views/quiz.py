from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ..models import QuizSession, Answer, QuizSessionQuestion, Question
from ..services.quiz_service import QuizService
from ..services.question_service import QuestionService

quiz_service = QuizService()
question_service = QuestionService()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_quiz(request):
    topic = request.data.get('topic')
    subtopic = request.data.get('subtopic', '')
    knowledge_level = request.data.get('knowledge_level', 'high_school')
    difficulty = request.data.get('difficulty', 'medium')
    questions_count = request.data.get('questions_count', 10)
    time_per_question = request.data.get('time_per_question', 30)
    use_adaptive_difficulty = request.data.get('use_adaptive_difficulty', True)

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

    batch_size = 4
    to_generate = min(batch_size, questions_count)
    print(f"📚 Generating first batch of {to_generate} questions")

    try:
        quiz_service.generate_initial_batch(
            session=session,
            to_generate=to_generate,
            initial_difficulty=initial_difficulty,
            user=request.user
        )

        print(f"✅ First batch generated")

    except Exception as e:
        print(f"❌ Error generating questions: {e}")
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def end_quiz(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    if session.is_completed:
        return Response(
            {'error': 'Quiz already completed'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if session.total_questions < session.questions_count:
        print(f"🗑️ Deleting incomplete session {session.id}")

        answered_question_ids = Answer.objects.filter(session=session).values_list('question_id', flat=True)

        unanswered_session_questions = QuizSessionQuestion.objects.filter(
            session=session
        ).exclude(
            question_id__in=answered_question_ids
        )

        unanswered_question_ids = list(unanswered_session_questions.values_list('question_id', flat=True))

        Answer.objects.filter(session=session).delete()
        QuizSessionQuestion.objects.filter(session=session).delete()
        session.delete()

        orphans_deleted = 0
        if unanswered_question_ids:
            for question_id in unanswered_question_ids:
                try:
                    other_sessions_count = QuizSessionQuestion.objects.filter(
                        question_id=question_id
                    ).count()

                    answers_count = Answer.objects.filter(question_id=question_id).count()

                    if other_sessions_count == 0 and answers_count == 0:
                        Question.objects.filter(id=question_id).delete()
                        orphans_deleted += 1
                except Question.DoesNotExist:
                    pass
                except Exception as e:
                    print(f"⚠️ Could not delete question {question_id}: {e}")

        if orphans_deleted > 0:
            print(f"✅ Deleted {orphans_deleted} orphan questions")

        return Response({
            'message': 'Incomplete quiz session deleted',
            'deleted': True,
            'orphans_cleaned': orphans_deleted
        })

    session.ended_at = timezone.now()
    session.is_completed = True
    session.save()

    answered_question_ids = Answer.objects.filter(session=session).values_list('question_id', flat=True)

    unanswered_session_questions = QuizSessionQuestion.objects.filter(
        session=session
    ).exclude(
        question_id__in=answered_question_ids
    )

    orphans_deleted = 0
    if unanswered_session_questions.exists():
        unanswered_question_ids = list(unanswered_session_questions.values_list('question_id', flat=True))

        unanswered_session_questions.delete()

        for question_id in unanswered_question_ids:
            try:
                other_sessions_count = QuizSessionQuestion.objects.filter(question_id=question_id).count()
                answers_count = Answer.objects.filter(question_id=question_id).count()

                if other_sessions_count == 0 and answers_count == 0:
                    Question.objects.filter(id=question_id).delete()
                    orphans_deleted += 1
            except Question.DoesNotExist:
                pass
            except Exception as e:
                print(f"⚠️ Could not delete question {question_id}: {e}")

    if orphans_deleted > 0:
        print(f"✅ Deleted {orphans_deleted} orphan backup questions")

    return Response({
        'message': 'Quiz ended successfully',
        'session_id': session.id,
        'total_questions': session.total_questions,
        'correct_answers': session.correct_answers,
        'accuracy': session.accuracy,
        'deleted': False,
        'orphans_cleaned': orphans_deleted
    })