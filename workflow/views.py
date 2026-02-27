from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Task
from datetime import datetime, date
from .forms import TaskForm
from django.contrib import messages
from django.views.decorators.http import require_POST
from .ml_utils import predict_task_priority
from django.db.models import Case, When, IntegerField


def is_manager_or_admin(user):
    return user.is_superuser or user.groups.filter(name__in=['Manager']).exists()

@login_required
@user_passes_test(is_manager_or_admin)
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)

            status = form.cleaned_data['status']
            due_date = form.cleaned_data['due_date']

            # Calculate workload (number of pending tasks for assignee)
            workload = Task.objects.filter(
                assigned_to=task.assigned_to,
                status__in=['todo', 'in_progress']
            ).count()

            # Calculate days_to_due
            if due_date:
                days_to_due = (due_date - date.today()).days
                if days_to_due < 0:
                    days_to_due = 0
            else:
                days_to_due = 999  # Sentinel signaling no deadline pressure

            # Get created_day string, e.g., 'Mon', 'Tue'
            created_day = datetime.now().strftime('%a')

            # Calculate is_weekend_due based on due_date
            if due_date:
                is_weekend_due = 1 if due_date.weekday() >= 5 else 0
            else:
                is_weekend_due = 0

            # Assigned hour - could be current hour or from the form
            assigned_hour = datetime.now().hour

            # Call your prediction function with all needed params
            predicted_priority = predict_task_priority(
                status=status,
                days_to_due=days_to_due,
                pending_tasks=workload,  # or separate pending_tasks if you have that
                workload=workload,
                created_day=created_day,
                is_weekend_due=is_weekend_due,
                assigned_hour=assigned_hour
            )

            task.priority = predicted_priority
            task.save()
            return redirect('task_list')
    else:
        form = TaskForm()

    return render(request, 'workflow/create_task.html', {'form': form})

@login_required
def task_list(request):
    sort_by = request.GET.get('sort', 'priority')  # default sort by priority

    # Define priority order to sort by priority nicely
    priority_ordering = Case(
        When(priority='High', then=0),
        When(priority='Medium', then=1),
        When(priority='Low', then=2),
        default=3,
        output_field=IntegerField()
    )

    if request.user.is_superuser or request.user.groups.filter(name='Manager').exists():
        tasks = Task.objects.all()
    else:
        tasks = Task.objects.filter(assigned_to=request.user)

    # Apply sorting
    if sort_by == 'priority':
        tasks = tasks.order_by(priority_ordering, 'due_date')
    elif sort_by == 'due_date':
        tasks = tasks.order_by('due_date')
    elif sort_by == 'status':
        tasks = tasks.order_by('status')
    else:
        tasks = tasks.order_by('due_date')  # fallback

    context = {
        'tasks': tasks,
        'sort_by': sort_by,
    }
    return render(request, 'workflow/task_list.html', context)

@login_required
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    # Fix 2: expanded permission check to include Managers
    is_manager = request.user.groups.filter(name='Manager').exists()
    if not (request.user == task.assigned_to or request.user.is_superuser or is_manager):
        messages.error(request, "You do not have permission to update this task.")
        return redirect('task_list')

    if request.method == 'POST':
        new_status = request.POST.get('status')

        # Fix 1: validate status against Task.STATUS_CHOICES
        valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
        if new_status not in valid_statuses:
            messages.error(request, "Invalid status value.")
            return render(request, 'workflow/update_task.html', {'task': task})

        task.status = new_status

        # Fix 3: recalculate ML priority on status change
        due_date = task.due_date
        if due_date:
            days_to_due = (due_date - date.today()).days
            if days_to_due < 0:
                days_to_due = 0
        else:
            days_to_due = 999  # Sentinel signaling no deadline pressure

        workload = Task.objects.filter(
            assigned_to=task.assigned_to,
            status__in=['todo', 'in_progress']
        ).exclude(pk=task.pk).count()

        task.priority = predict_task_priority(
            status=new_status,
            days_to_due=days_to_due,
            pending_tasks=workload,
        )

        task.save()
        messages.success(request, "Task updated successfully.")
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
    pending_tasks = tasks.filter(status__in=['todo', 'in_progress']).count()
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


@login_required
@require_POST
def delete_task(request, pk):
    task = get_object_or_404(Task, pk=pk)

    if request.user.is_superuser or request.user.groups.filter(name='Manager').exists():
        task.delete()
        messages.success(request, "Task deleted successfully.")
    else:
        messages.error(request, "You do not have permission to delete this task.")

    return redirect('task_list')




