import random
import hashlib
from quiz_app.models import Question


def shuffle_answers(question):
    answers = [
        question.correct_answer,
        question.wrong_answer_1,
        question.wrong_answer_2,
        question.wrong_answer_3
    ]
    random.shuffle(answers)
    return answers


def generate_content_hash(question_text, correct_answer, topic, subtopic='', knowledge_level='', difficulty=''):
    content = f"{question_text}{correct_answer}{topic}{subtopic}{knowledge_level}{difficulty}"
    return hashlib.sha256(content.encode()).hexdigest()


def find_or_create_question(question_data, topic, difficulty_text, user=None, subtopic=None, knowledge_level=None):
    content_hash = generate_content_hash(
        question_data['question'],
        question_data['correct_answer'],
        topic,
        subtopic or '',
        knowledge_level or '',
        difficulty_text
    )

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
            'created_by': user,
        }
    )

    return question, created


def calculate_score_percentage(correct_count, total_count):
    if total_count == 0:
        return 0.0
    return round((correct_count / total_count) * 100, 2)


def format_time_display(seconds):
    if seconds < 60:
        return f"{seconds}s"

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    if remaining_seconds == 0:
        return f"{minutes}min"

    return f"{minutes}min {remaining_seconds}s"


def get_difficulty_display(difficulty):
    difficulty_map = {
        'easy': 'Łatwy',
        'medium': 'Średni',
        'hard': 'Trudny',
    }
    return difficulty_map.get(difficulty, difficulty)


def get_knowledge_level_display(knowledge_level):
    knowledge_map = {
        'elementary': 'Podstawowy',
        'high_school': 'Liceum',
        'university': 'Uniwersytet',
        'expert': 'Ekspert',
    }
    return knowledge_map.get(knowledge_level, knowledge_level)


def calculate_average_response_time(total_time, questions_count):
    if questions_count == 0:
        return 0.0
    return round(total_time / questions_count, 2)


def determine_performance_level(score_percentage):
    if score_percentage >= 90:
        return 'Wybitny'
    elif score_percentage >= 75:
        return 'Bardzo dobry'
    elif score_percentage >= 60:
        return 'Dobry'
    elif score_percentage >= 50:
        return 'Dostateczny'
    else:
        return 'Niedostateczny'


def build_question_filters(request):
    filters = {}

    topic = request.GET.get('topic')
    if topic:
        filters['topic__icontains'] = topic

    difficulty = request.GET.get('difficulty')
    if difficulty:
        filters['difficulty_level'] = difficulty

    knowledge_level = request.GET.get('knowledge_level')
    if knowledge_level:
        filters['knowledge_level'] = knowledge_level

    subtopic = request.GET.get('subtopic')
    if subtopic:
        filters['subtopic__icontains'] = subtopic

    return filters


def get_question_statistics(question):
    total_uses = question.times_used or 0
    success_rate = question.success_rate or 0.0

    return {
        'times_used': total_uses,
        'success_rate': round(success_rate, 2),
        'difficulty': question.difficulty_level,
        'average_time': getattr(question, 'average_response_time', 0),
    }