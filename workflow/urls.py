from django.urls import path
from . import views

urlpatterns = [
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.create_task, name='create_task'),
    path('tasks/<int:task_id>/update/', views.update_task_status, name='update_task_status'),
    path('tasks/<int:pk>/status/htmx/', views.update_task_status_htmx, name='update_task_status_htmx'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('kanban/', views.kanban_board, name='kanban_board'),
    path('tasks/<int:pk>/edit/', views.edit_task, name='edit_task'),
    path('tasks/<int:pk>/delete/', views.delete_task, name='delete_task'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
]
