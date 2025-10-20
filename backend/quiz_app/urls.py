from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.start_quiz),
    path('question/<int:session_id>/', views.get_question),
    path('answer/', views.submit_answer),
    path('end/<int:session_id>/', views.end_quiz),
    path('history/', views.quiz_history),
    path('details/<int:session_id>/', views.quiz_details),
]