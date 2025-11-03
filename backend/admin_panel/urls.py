from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('users/', views.all_users, name='admin-users'),
    path('users/search/', views.search_users, name='admin-search-users'),
    path('users/<int:user_id>/quizzes/', views.user_quiz_history, name='admin-user-quizzes'),
    path('sessions/<int:session_id>/delete/', views.delete_quiz_session, name='admin-delete-session'),
    path('users/<int:user_id>/delete/', views.delete_user, name='admin-delete-user'),
    path('users/<int:user_id>/role/', views.change_user_role, name='admin-change-role'),
    path('users/<int:user_id>/toggle/', views.toggle_user_status),
]
