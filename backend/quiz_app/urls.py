from django.urls import path
from .views.quiz import start_quiz, end_quiz
from .views.question import get_question, questions_library
from .views.answer import submit_answer
from .views.history import quiz_history, quiz_details, quiz_api_root
from .views import admin_questions
from .views import leaderboard

urlpatterns = [
    # ==================== QUIZ ENDPOINTS ====================
    path('', quiz_api_root, name='quiz-root'),
    path('start/', start_quiz, name='start-quiz'),
    path('question/<int:session_id>/', get_question, name='get-question'),
    path('answer/', submit_answer, name='submit-answer'),
    path('end/<int:session_id>/', end_quiz, name='end-quiz'),
    path('history/', quiz_history, name='quiz-history'),
    path('details/<int:session_id>/', quiz_details, name='quiz-details'),
    path('questions/', questions_library, name='questions-library'),

    # ==================== LEADERBOARD ====================
    path('leaderboard/global/', leaderboard.global_leaderboard, name='leaderboard-global'),
    path('leaderboard/topic/', leaderboard.topic_leaderboard, name='leaderboard-topic'),
    path('leaderboard/me/', leaderboard.user_ranking, name='leaderboard-me'),
    path('leaderboard/stats/', leaderboard.leaderboard_stats, name='leaderboard-stats'),

    # ==================== ADMIN QUESTIONS ENDPOINTS ====================
    path('admin/questions/', admin_questions.list_questions, name='admin-list-questions'),
    path('admin/questions/stats/', admin_questions.question_stats, name='admin-question-stats'),
    path('admin/questions/<int:question_id>/', admin_questions.get_question_detail, name='admin-question-detail'),
    path('admin/questions/<int:question_id>/update/', admin_questions.update_question, name='admin-update-question'),
    path('admin/questions/<int:question_id>/delete/', admin_questions.delete_question, name='admin-delete-question'),
]
