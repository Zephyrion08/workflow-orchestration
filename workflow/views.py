from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Task
from .forms import TaskForm

def is_manager_or_admin(user):
    return user.is_superuser or user.groups.filter(name__in=['Manager']).exists()

@login_required
@user_passes_test(is_manager_or_admin)
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('task_list')
    else:
        form = TaskForm()
    return render(request, 'workflow/create_task.html', {'form': form})

@login_required
def task_list(request):
    if request.user.is_superuser or request.user.groups.filter(name='Manager').exists():
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(assigned_to=request.user)
    return render(request, 'workflow/task_list.html', {'tasks': tasks})

@login_required
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.user == task.assigned_to or request.user.is_superuser:
        if request.method == 'POST':
            status = request.POST.get('status')
            task.status = status
            task.save()
            return redirect('task_list')
    return render(request, 'workflow/update_task.html', {'task': task})


@login_required
def dashboard(request):
    user = request.user

    if user.is_superuser:
        # Admin sees all tasks
        tasks = Task.objects.all()
    else:
        # Regular user sees only their assigned tasks
        tasks = Task.objects.filter(assigned_to=user)

    total_tasks = tasks.count()
    pending_tasks = Task.objects.filter(status__in=['todo', 'in_progress']).count()
    completed_tasks = tasks.filter(status__iexact='done').count()

    notifications = [
        "Welcome back!",
        f"You have {pending_tasks} pending tasks.",
    ]

    context = {
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'notifications': notifications,
    }
    return render(request, 'workflow/dashboard.html', context)







