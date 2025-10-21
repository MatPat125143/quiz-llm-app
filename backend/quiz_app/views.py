from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import QuizSession, Question, Answer
from .serializers import QuizSessionSerializer, QuestionSerializer
from .permissions import IsQuizOwnerOrAdmin
from llm_integration.question_generator import QuestionGenerator
import json
import random

# Inicjalizuj generator (bezpieczny - używa fake questions jeśli brak API key)
generator = QuestionGenerator()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_quiz(request):
    topic = request.data.get('topic')
    difficulty = request.data.get('difficulty', 'medium')

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
        current_difficulty=initial_difficulty
    )

    profile = request.user.profile
    profile.total_quizzes_played += 1
    profile.save()

    return Response({
        'session_id': session.id,
        'message': 'Quiz started successfully!',
        'topic': topic,
        'difficulty': difficulty
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_question(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)

    # Generuj pytanie (użyje LLM jeśli dostępny, inaczej fake)
    question_data = generator.generate_question(
        session.topic,
        session.current_difficulty
    )

    question = Question.objects.create(
        session=session,
        question_text=question_data['question'],
        correct_answer=question_data['correct_answer'],
        wrong_answer_1=question_data['wrong_answers'][0],
        wrong_answer_2=question_data['wrong_answers'][1],
        wrong_answer_3=question_data['wrong_answers'][2],
        explanation=question_data['explanation'],
        difficulty_level=session.current_difficulty
    )

    answers = [
        question.correct_answer,
        question.wrong_answer_1,
        question.wrong_answer_2,
        question.wrong_answer_3
    ]
    random.shuffle(answers)

    session.total_questions += 1
    session.save()

    return Response({
        'id': question.id,
        'question_text': question.question_text,
        'option_a': answers[0],
        'option_b': answers[1],
        'option_c': answers[2],
        'option_d': answers[3],
        'current_difficulty': session.current_difficulty,
        'question_number': session.total_questions,
        'topic': session.topic
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

    is_correct = selected_answer == question.correct_answer

    answer = Answer.objects.create(
        question=question,
        user=request.user,
        selected_answer=selected_answer,
        is_correct=is_correct,
        response_time=response_time
    )

    if is_correct:
        session.correct_answers += 1
        session.current_streak += 1
    else:
        session.current_streak = 0

    # Sprawdź czy quiz powinien się zakończyć (np. po 10 pytaniach)
    quiz_completed = session.total_questions >= 10
    if quiz_completed and not session.is_completed:
        session.ended_at = timezone.now()
        session.is_completed = True

    session.save()

    profile = request.user.profile
    profile.total_questions_answered += 1
    if is_correct:
        profile.total_correct_answers += 1
    if session.current_streak > profile.highest_streak:
        profile.highest_streak = session.current_streak
    profile.save()

    return Response({
        'is_correct': is_correct,
        'correct_answer': question.correct_answer,
        'explanation': question.explanation,
        'current_streak': session.current_streak,
        'quiz_completed': quiz_completed,
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
    serializer = QuizSessionSerializer(sessions, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_details(request, session_id):
    session = get_object_or_404(QuizSession, id=session_id, user=request.user)
    questions = Question.objects.filter(session=session).prefetch_related('answers')

    questions_data = []
    for q in questions:
        answer = q.answers.first()
        if answer:
            # Stwórz losowe mapowanie opcji (jak w get_question)
            answers = [
                q.correct_answer,
                q.wrong_answer_1,
                q.wrong_answer_2,
                q.wrong_answer_3
            ]
            random.shuffle(answers)

            # Znajdź która litera odpowiada wybranej i poprawnej odpowiedzi
            selected_letter = None
            correct_letter = None
            for idx, ans in enumerate(answers):
                letter = chr(65 + idx)  # A=65, B=66, C=67, D=68
                if ans == answer.selected_answer:
                    selected_letter = letter
                if ans == q.correct_answer:
                    correct_letter = letter

            questions_data.append({
                'id': q.id,
                'question_text': q.question_text,
                'option_a': answers[0],
                'option_b': answers[1],
                'option_c': answers[2],
                'option_d': answers[3],
                'selected_answer': selected_letter,
                'correct_answer': correct_letter,
                'is_correct': answer.is_correct,
                'explanation': q.explanation,
                'response_time': answer.response_time,
                'difficulty': q.difficulty_level
            })

    return Response({
        'session_id': session.id,
        'topic': session.topic,
        'difficulty': session.initial_difficulty,
        'started_at': session.started_at,
        'ended_at': session.ended_at,
        'completed_at': session.ended_at,
        'total_questions': session.total_questions,
        'correct_answers': session.correct_answers,
        'score': session.correct_answers,
        'accuracy': session.accuracy,
        'questions': questions_data
    })