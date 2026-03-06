import pytest
from django.contrib.auth.models import Group
from accounts.models import CustomUser
from workflow.models import Task
from workflow.services import assign_task_and_set_priority, recalculate_task_priority

@pytest.mark.django_db
def test_task_assignment():
    """Test the ML assignment task logic runs gracefully without crashing."""
    
    # Setup users
    admin_group, _ = Group.objects.get_or_create(name='Admin')
    manager_group, _ = Group.objects.get_or_create(name='Manager')
    
    admin = CustomUser.objects.create_superuser(
        username='admin', password='password', employee_id='1'
    )
    user1 = CustomUser.objects.create_user(
        username='user1', password='password', employee_id='2'
    )
    user2 = CustomUser.objects.create_user(
        username='user2', password='password', employee_id='3'
    )
    
    # Create a task with NO assignee initially
    task = Task.objects.create(
        title='Fix testing bug',
        description='Test descriptions',
        status='todo'
    )

    assign_task_and_set_priority(task)
    
    # The task should be assigned to someone (user1 or user2, NOT admin)
    assert task.assigned_to is not None
    assert task.assigned_to != admin
    assert task.priority in ['Low', 'Medium', 'High']


@pytest.mark.django_db
def test_recalculate_task_priority():
    """Test that calculating priority properly counts workloads."""
    user1 = CustomUser.objects.create_user(
        username='user1', password='password', employee_id='2'
    )

    task1 = Task.objects.create(title='Task 1', assigned_to=user1, status='todo')
    task2 = Task.objects.create(title='Task 2', assigned_to=user1, status='todo')
    
    # Update status for task 2
    task2.status = 'in_progress'
    task2.save()

    # Priority recalculation should see "1" other pending task for this user
    recalculate_task_priority(task2)
    
    # It shouldn't crash and workload must correctly calculate as 1 (ignoring itself)
    assert task2.workload == 1
    assert task2.priority in ['Low', 'Medium', 'High']
