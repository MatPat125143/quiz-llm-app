from django.urls import path
from .views import (
    start_quiz,
    end_quiz,
    get_question,
    questions_library,
    submit_answer,
    quiz_history,
    quiz_details,
)

urlpatterns = [
    path('start/', start_quiz, name='start-quiz'),
    path('question/<int:session_id>/', get_question, name='get-question'),
    path('answer/', submit_answer, name='submit-answer'),
    path('end/<int:session_id>/', end_quiz, name='end-quiz'),
    path('history/', quiz_history, name='quiz-history'),
    path('details/<int:session_id>/', quiz_details, name='quiz-details'),
    path('questions/', questions_library, name='questions-library'),
]