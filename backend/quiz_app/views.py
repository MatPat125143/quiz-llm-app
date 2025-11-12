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

generator = QuestionGenerator()
difficulty_adapter = DifficultyAdapter()
embeddings_service = EmbeddingsService()
question_cache = QuestionCache()


def _find_or_create_global_question(topic, question_data, difficulty_text, user=None, subtopic=None,
                                    knowledge_level=None):
    try:
        content = f"{question_data['question']}{question_data['correct_answer']}{topic}{subtopic or ''}{knowledge_level or ''}{difficulty_text}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()

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

        if created and embeddings_service.is_available():
            try:
                embedding = embeddings_service.encode_question(question_data['question'])
                if embedding is not None:
                    print(f"📝 Created question ID={question.id} with embedding")
                else:
                    print(f"📝 Created question ID={question.id} without embedding")
            except Exception as e:
                print(f"⚠️ Embedding failed: {e}")
        elif created:
            print(f"📝 Created question ID={question.id}")
        else:
            print(f"✅ Reusing question ID={question.id} ({question.times_used}x)")
            question.times_used += 1
            question.save(update_fields=['times_used'])

        return question, created

    except KeyError as e:
        print(f"❌ Missing key in question_data: {e}")
        raise ValueError(f"Invalid question_data format: missing {e}")
    except Exception as e:
        print(f"❌ Error in _find_or_create_global_question: {e}")
        raise


def _add_question_to_session(session, question, order=0):
    existing = QuizSessionQuestion.objects.filter(
        session=session,
        question=question
    ).exists()

    if existing:
        print(f"⚠️ Question {question.id} already in session {session.id}")
        return None

    if embeddings_service.is_available():
        try:
            session_questions = QuizSessionQuestion.objects.filter(session=session).select_related('question')

            if session_questions.exists():
                new_embedding = embeddings_service.encode_question(question.question_text)

                if new_embedding is not None:
                    for sq in session_questions:
                        existing_embedding = embeddings_service.encode_question(sq.question.question_text)

                        if existing_embedding is not None:
                            similarity = np.dot(new_embedding, existing_embedding) / (
                                    np.linalg.norm(new_embedding) * np.linalg.norm(existing_embedding)
                            )

                            if similarity > 0.90:
                                print(f"⚠️ Question {question.id} too similar to {sq.question.id} ({similarity:.2f})")
                                return None

        except Exception as e:
            print(f"⚠️ Similarity check failed: {e}")

    session_question = QuizSessionQuestion.objects.create(
        session=session,
        question=question,
        order=order
    )

    print(f"✅ Added question {question.id} to session {session.id}")
    return session_question


def _build_question_payload(session, question, generation_status):
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
    payload = _build_question_payload(session, question, generation_status='cached')
    cache.set(f'next_q:{session.id}', payload, timeout=120)


def _prepare_next_question_async(session_id):
    try:
        session = QuizSession.objects.get(id=session_id)
        if session.is_completed:
            return

        if cache.get(f'next_q:{session.id}'):
            return

        seen_texts = set(
            QuizSessionQuestion.objects.filter(session=session)
            .select_related('question')
            .values_list('question__question_text', flat=True)
        )
        seen_texts |= set(
            Answer.objects.filter(session=session, user=session.user)
            .values_list('question__question_text', flat=True)
        )

        difficulty_text = difficulty_adapter.get_difficulty_level(session.current_difficulty)

        cached_question_data = question_cache.get_cached_question(
            topic=session.topic,
            difficulty=difficulty_text,
            subtopic=session.subtopic,
            knowledge_level=session.knowledge_level
        )

        if cached_question_data:
            print(f"⚡ Found cached question for {session.topic}/{difficulty_text}")
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

        max_attempts, attempts = 7, 0
        while attempts < max_attempts:
            qdata = generator.generate_question(
                session.topic,
                session.current_difficulty,
                subtopic=session.subtopic,
                knowledge_level=session.knowledge_level
            )

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
            print(f"🔁 Duplicate, retry {attempts}/{max_attempts}")

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
        all_questions_data = generator.generate_multiple_questions(
            topic,
            initial_difficulty,
            to_generate,
            subtopic=subtopic if subtopic else None,
            knowledge_level=knowledge_level
        )

        difficulty_text = difficulty_adapter.get_difficulty_level(initial_difficulty)

        created_count = 0
        reused_count = 0

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

            _add_question_to_session(session, question, order=order)

        session.questions_generated_count = to_generate
        session.save(update_fields=['questions_generated_count'])

        print(f"✅ First batch: {created_count} new, {reused_count} reused")

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    if session.is_completed:
        return Response(
            {'error': 'Quiz already completed'},
            status=status.HTTP_404_NOT_FOUND
        )

    cached = cache.get(f'next_q:{session.id}')
    if cached:
        cache.delete(f'next_q:{session.id}')
        print("⚡ Served question from cache")
        return Response(cached)

    answered_question_ids = Answer.objects.filter(
        session=session,
        user=session.user
    ).values_list('question_id', flat=True)

    answered_texts = Answer.objects.filter(
        session=session,
        user=session.user
    ).values_list('question__question_text', flat=True)

    session_question = QuizSessionQuestion.objects.filter(
        session=session
    ).exclude(
        question_id__in=answered_question_ids
    ).exclude(
        question__question_text__in=answered_texts
    ).select_related('question').order_by('order').first()

    if not session_question:
        max_wait_time = 10
        poll_interval = 0.5
        waited = 0

        print(f"⏳ Waiting up to {max_wait_time}s for question...")

        while waited < max_wait_time:
            time.sleep(poll_interval)
            waited += poll_interval

            session_question = QuizSessionQuestion.objects.filter(
                session=session
            ).exclude(
                question_id__in=answered_question_ids
            ).exclude(
                question__question_text__in=answered_texts
            ).select_related('question').order_by('order').first()

            if session_question:
                print(f"⏱️ Question appeared after {waited}s")
                break

        if not session_question:
            print(f"❌ No question after {max_wait_time}s")
            return Response(
                {'error': 'No more questions available'},
                status=status.HTTP_404_NOT_FOUND
            )

    question = session_question.question
    generation_status = "pre_generated"
    print(f"📖 Question ID={question.id}")

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
                        try:
                            session_refresh = QuizSession.objects.get(id=session.id)

                            unused_questions = QuizSessionQuestion.objects.filter(
                                session=session_refresh
                            ).exclude(
                                question_id__in=Answer.objects.filter(session=session_refresh)
                                .values_list('question_id', flat=True)
                            )

                            unused_question_ids = list(unused_questions.values_list('question_id', flat=True))
                            deleted_count = len(unused_question_ids)

                            unused_questions.delete()
                            print(f"🗑️ Deleted {deleted_count} QuizSessionQuestion")

                            orphans_deleted = 0
                            for question_id in unused_question_ids:
                                try:
                                    other_sessions = QuizSessionQuestion.objects.filter(
                                        question_id=question_id).exists()
                                    has_answers = Answer.objects.filter(question_id=question_id).exists()

                                    if not other_sessions and not has_answers:
                                        Question.objects.filter(id=question_id).delete()
                                        orphans_deleted += 1
                                except Exception as e:
                                    print(f"⚠️ Could not delete Question ID={question_id}: {e}")

                            if orphans_deleted > 0:
                                print(f"✅ Deleted {orphans_deleted} orphan Questions")

                            all_questions_data = generator.generate_multiple_questions(
                                session_refresh.topic,
                                session_refresh.current_difficulty,
                                to_generate,
                                subtopic=session_refresh.subtopic,
                                knowledge_level=session_refresh.knowledge_level
                            )

                            all_questions_data = all_questions_data[:to_generate]

                            difficulty_text = difficulty_adapter.get_difficulty_level(
                                session_refresh.current_difficulty)

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

                                if q.question_text not in seen_texts:
                                    order = QuizSessionQuestion.objects.filter(session=session_refresh).count()
                                    _add_question_to_session(session_refresh, q, order=order)
                                    seen_texts.add(q.question_text)

                            session_refresh.questions_generated_count = answered_count + to_generate
                            session_refresh.save(update_fields=['questions_generated_count'])
                            print(f"✅ Generated {to_generate} questions")

                        except Exception as e:
                            print(f"❌ Error generating batch: {e}")
                            import traceback
                            traceback.print_exc()

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
                            try:
                                session_refresh = QuizSession.objects.get(id=session.id)
                                difficulty_text = difficulty_adapter.get_difficulty_level(
                                    session_refresh.current_difficulty)

                                seen_texts = set(
                                    Answer.objects.filter(session=session_refresh)
                                    .values_list('question__question_text', flat=True)
                                )
                                seen_texts |= set(
                                    QuizSessionQuestion.objects.filter(session=session_refresh)
                                    .select_related('question')
                                    .values_list('question__question_text', flat=True)
                                )

                                questions_added = 0
                                max_attempts_per_question = 3

                                for i in range(needed):
                                    question_added = False

                                    for attempt in range(max_attempts_per_question):
                                        question_data = generator.generate_question(
                                            session_refresh.topic,
                                            session_refresh.current_difficulty,
                                            subtopic=session_refresh.subtopic,
                                            knowledge_level=session_refresh.knowledge_level
                                        )

                                        q, created = _find_or_create_global_question(
                                            session_refresh.topic,
                                            question_data,
                                            difficulty_text,
                                            user=session_refresh.user,
                                            subtopic=session_refresh.subtopic,
                                            knowledge_level=session_refresh.knowledge_level
                                        )

                                        if q.question_text in seen_texts:
                                            continue

                                        order = QuizSessionQuestion.objects.filter(session=session_refresh).count()
                                        session_question = _add_question_to_session(session_refresh, q, order=order)

                                        if session_question is not None:
                                            questions_added += 1
                                            seen_texts.add(q.question_text)
                                            question_added = True
                                            break
                                        else:
                                            seen_texts.add(q.question_text)

                                            try:
                                                if not QuizSessionQuestion.objects.filter(
                                                        question_id=q.id).exists() and not Answer.objects.filter(
                                                    question_id=q.id).exists():
                                                    q.delete()
                                            except:
                                                pass

                                    if not question_added:
                                        print(f"❌ Failed to generate backup {i + 1}/{needed}")

                                if questions_added > 0:
                                    print(f"✅ Generated {questions_added}/{needed} backups")
                                else:
                                    fallback = Question.objects.filter(
                                        topic=session_refresh.topic,
                                        difficulty_level=difficulty_text,
                                        subtopic=session_refresh.subtopic if session_refresh.subtopic else None,
                                        knowledge_level=session_refresh.knowledge_level
                                    ).exclude(
                                        question_text__in=seen_texts
                                    ).order_by('-times_used').first()

                                    if not fallback and session_refresh.subtopic:
                                        fallback = Question.objects.filter(
                                            topic=session_refresh.topic,
                                            difficulty_level=difficulty_text,
                                            knowledge_level=session_refresh.knowledge_level
                                        ).exclude(
                                            question_text__in=seen_texts
                                        ).order_by('-times_used').first()

                                    if fallback:
                                        order = QuizSessionQuestion.objects.filter(session=session_refresh).count()
                                        session_question = _add_question_to_session(session_refresh, fallback,
                                                                                    order=order)
                                        if session_question:
                                            print(f"✅ Used fallback question")

                            except Exception as e:
                                print(f"❌ Error generating backup: {e}")

                        threading.Thread(target=generate_backup_questions, daemon=True).start()

            else:
                generated_count = session.questions_generated_count
                remaining_in_batch = generated_count - answered_count
                if remaining_in_batch <= 3 and generated_count < session.questions_count:
                    to_generate = min(4, session.questions_count - generated_count)
                    print(f"📚 Fixed mode: generating {to_generate} questions")

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

                            all_questions_data = all_questions_data[:to_generate]

                            difficulty_text = difficulty_adapter.get_difficulty_level(
                                session_refresh.current_difficulty)

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
                            print(f"✅ Generated batch of {to_generate}")

                        except Exception as e:
                            print(f"❌ Error generating batch: {e}")

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_history(request):
    qs = QuizSession.objects.filter(user=request.user, is_completed=True)

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

    order_by = request.GET.get('order_by', '-started_at')
    allowed = ['started_at', '-started_at', 'accuracy', '-accuracy', 'topic', '-topic', 'total_questions',
               '-total_questions']
    if order_by in allowed:
        qs = qs.order_by(order_by)

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
    try:
        user_role = request.user.profile.role
    except Exception:
        user_role = 'user'

    if user_role == 'admin':
        session = get_object_or_404(QuizSession, id=session_id)
    else:
        session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    answers = Answer.objects.filter(session=session).select_related('question').order_by('answered_at')

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

    qs = qs.filter(total_answers__gt=0)

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

    smin = request.GET.get('success_min')
    smax = request.GET.get('success_max')
    try:
        if smin not in (None, ''):
            qs = qs.filter(_success_rate__gte=float(smin))
        if smax not in (None, ''):
            qs = qs.filter(_success_rate__lte=float(smax))
    except ValueError:
        pass

    umin = request.GET.get('used_min')
    umax = request.GET.get('used_max')
    try:
        if umin not in (None, ''):
            qs = qs.filter(times_used__gte=int(umin))
        if umax not in (None, ''):
            qs = qs.filter(times_used__lte=int(umax))
    except ValueError:
        pass

    has_expl = (request.GET.get('has_explanation') or '').lower()
    if has_expl in ('true', 'false'):
        if has_expl == 'true':
            qs = qs.filter(~Q(explanation__isnull=True) & ~Q(explanation__exact=''))
        else:
            qs = qs.filter(Q(explanation__isnull=True) | Q(explanation__exact=''))

    order_by = request.GET.get('order_by', '-created_at')
    mapping = {
        'created_at': 'created_at',
        '-created_at': '-created_at',
        'success_rate': '_success_rate',
        '-success_rate': '-_success_rate',
    }
    qs = qs.order_by(mapping.get(order_by, '-created_at'))

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
    serializer_class = QuizSessionSerializer
    permission_classes = [IsAuthenticated, IsQuizOwnerOrAdmin]

    def get_queryset(self):
        return QuizSession.objects.filter(user=self.request.user).order_by('-started_at')


@api_view(['GET'])
def quiz_api_root(request):
    return Response({
        'message': 'Quiz LLM API',
        'version': '3.4',
        'endpoints': {
            'start_quiz': '/api/quiz/start/',
            'get_question': '/api/quiz/question/<session_id>/',
            'submit_answer': '/api/quiz/answer/',
            'end_quiz': '/api/quiz/end/<session_id>/',
            'quiz_history': '/api/quiz/history/',
            'quiz_details': '/api/quiz/details/<session_id>/',
            'questions_library': '/api/quiz/questions/',
        }
    })


print("✅ Views loaded - Stats from completed quizzes only")