import random
from django.db.models import Q, Case, When, Value, IntegerField, F
from quiz_app.models import Question, QuizSession, QuizSessionQuestion
from quiz_app.utils.helpers import find_or_create_question, shuffle_answers
from core.exceptions import QuestionNotFound, InsufficientQuestionsError, QuestionGenerationError
from llm_integration.question_generator import QuestionGenerator
from cache_manager.question_cache import QuestionCache


class QuestionService:

    def __init__(self):
        self.generator = QuestionGenerator()
        self.cache = QuestionCache()

    def get_next_question(self, session):
        already_asked = QuizSessionQuestion.objects.filter(
            session=session
        ).values_list('question_id', flat=True)

        available_questions = Question.objects.filter(
            topic__iexact=session.topic,
            difficulty_level=session.current_difficulty,
        ).exclude(id__in=already_asked)

        if session.subtopic:
            available_questions = available_questions.filter(subtopic__icontains=session.subtopic)

        if session.knowledge_level:
            available_questions = available_questions.filter(knowledge_level=session.knowledge_level)

        if available_questions.exists():
            question = self._select_best_question(available_questions)
        else:
            question = self._generate_new_question(session)

        self._link_question_to_session(question, session)

        return question

    def _select_best_question(self, queryset):
        prioritized_questions = queryset.annotate(
            priority=Case(
                When(times_used=0, then=Value(3)),
                When(times_used__lte=5, then=Value(2)),
                default=Value(1),
                output_field=IntegerField()
            )
        ).order_by('-priority', 'times_used', '?')

        return prioritized_questions.first()

    def _generate_new_question(self, session):
        try:
            question_data = self.generator.generate_question(
                topic=session.topic,
                subtopic=session.subtopic or '',
                difficulty=session.current_difficulty,
                knowledge_level=session.knowledge_level or 'high_school'
            )

            question, created = find_or_create_question(
                question_data=question_data,
                topic=session.topic,
                difficulty_text=session.current_difficulty,
                user=session.user,
                subtopic=session.subtopic,
                knowledge_level=session.knowledge_level
            )

            return question

        except Exception as e:
            raise QuestionGenerationError(detail=f'Błąd generowania pytania: {str(e)}')

    def _link_question_to_session(self, question, session):
        QuizSessionQuestion.objects.create(
            session=session,
            question=question
        )

    def format_question_response(self, question, session):
        answers = shuffle_answers(question)

        answered_count = QuizSessionQuestion.objects.filter(
            session=session,
            answered_at__isnull=False
        ).count()

        question_number = min(answered_count + 1, session.questions_count)
        questions_remaining = max(session.questions_count - answered_count, 0)

        return {
            'question_id': question.id,
            'question_text': question.question_text,
            'topic': session.topic,
            'subtopic': session.subtopic,
            'answers': answers,
            'option_a': answers[0],
            'option_b': answers[1],
            'option_c': answers[2],
            'option_d': answers[3],
            'current_difficulty': session.current_difficulty,
            'difficulty_label': question.difficulty_level,
            'question_number': question_number,
            'questions_count': session.questions_count,
            'questions_remaining': questions_remaining,
            'time_per_question': session.time_per_question,
            'use_adaptive_difficulty': session.use_adaptive_difficulty,
            'times_used': question.times_used,
            'success_rate': question.success_rate,
        }

    def get_questions_library(self, filters=None, user=None):
        queryset = Question.objects.all()

        if filters:
            if filters.get('topic'):
                queryset = queryset.filter(topic__icontains=filters['topic'])

            if filters.get('difficulty'):
                queryset = queryset.filter(difficulty_level=filters['difficulty'])

            if filters.get('knowledge_level'):
                queryset = queryset.filter(knowledge_level=filters['knowledge_level'])

            if filters.get('subtopic'):
                queryset = queryset.filter(subtopic__icontains=filters['subtopic'])

            if filters.get('search'):
                search_term = filters['search']
                queryset = queryset.filter(
                    Q(question_text__icontains=search_term) |
                    Q(topic__icontains=search_term) |
                    Q(subtopic__icontains=search_term)
                )

        return queryset.order_by('-created_at')

    def get_question_with_details(self, question_id):
        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            raise QuestionNotFound()

        return question

    def update_question_statistics(self, question, is_correct, response_time):
        question.times_used = F('times_used') + 1

        if is_correct:
            question.times_correct = F('times_correct') + 1

        question.save()
        question.refresh_from_db()

        if question.times_used > 0:
            question.success_rate = (question.times_correct / question.times_used) * 100
            question.save(update_fields=['success_rate'])