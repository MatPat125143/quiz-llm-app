from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard),
    path('users/', views.all_users),
    path('users/<int:user_id>/delete/', views.delete_user),
    path('users/<int:user_id>/role/', views.change_user_role),
]