from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/update/', views.update_task_status, name='update_task_status'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
]
