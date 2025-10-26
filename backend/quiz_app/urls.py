from django.urls import path
from . import views

urlpatterns = [
    path('', views.quiz_api_root, name='quiz-root'),  # <-- DODAJ TEN
    path('start/', views.start_quiz, name='start-quiz'),
    path('question/<int:session_id>/', views.get_question, name='get-question'),
    path('answer/', views.submit_answer, name='submit-answer'),
    path('end/<int:session_id>/', views.end_quiz, name='end-quiz'),
    path('history/', views.quiz_history, name='quiz-history'),
    path('details/<int:session_id>/', views.quiz_details, name='quiz-details'),
]