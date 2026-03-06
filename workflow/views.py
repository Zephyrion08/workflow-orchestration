from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Task
from datetime import datetime, date
from django.utils import timezone
import datetime as dt_module
from .forms import TaskForm
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Case, When, IntegerField, Q
from django.core.paginator import Paginator
import logging

from .services import assign_task_and_set_priority, recalculate_task_priority
from .tasks import assign_and_score_task_async, recalculate_task_priority_async

logger = logging.getLogger(__name__)

from accounts.models import CustomUser

def is_manager_or_admin(user):
    return user.is_superuser or user.groups.filter(name__in=['Manager']).exists()

@login_required
@user_passes_test(is_manager_or_admin)
def manager_dashboard(request):
    tasks = Task.objects.select_related('assigned_to').all()

    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status__in=['todo', 'in_progress']).count()
    completed_tasks = tasks.filter(status='done').count()
    total_users = CustomUser.objects.filter(is_superuser=False).count()

    # Status chart data
    todo_count = tasks.filter(status='todo').count()
    in_progress_count = tasks.filter(status='in_progress').count()
    done_count = tasks.filter(status='done').count()

    # Priority chart data
    high_count = tasks.filter(priority='High').count()
    medium_count = tasks.filter(priority='Medium').count()
    low_count = tasks.filter(priority='Low').count()

    context = {
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'total_users': total_users,
        'todo_count': todo_count,
        'in_progress_count': in_progress_count,
        'done_count': done_count,
        'high_count': high_count,
        'medium_count': medium_count,
        'low_count': low_count,
    }
    return render(request, 'workflow/manager_dashboard.html', context)

@login_required
@user_passes_test(is_manager_or_admin)
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            assign_and_score_task_async.delay(task.id)

            messages.success(request, "Task created! The ML assignment engine is evaluating candidates in the background.")
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
        tasks = Task.objects.select_related('assigned_to').all()
    else:
        tasks = Task.objects.select_related('assigned_to').filter(assigned_to=request.user)

    # Apply search filter
    query = request.GET.get('q', '')
    if query:
        tasks = tasks.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    # Apply sorting
    if sort_by == 'priority':
        tasks = tasks.order_by(priority_ordering, 'due_date')
    elif sort_by == 'due_date':
        tasks = tasks.order_by('due_date')
    elif sort_by == 'status':
        tasks = tasks.order_by('status')
    else:
        tasks = tasks.order_by('due_date')  # fallback

    # Apply pagination (25 tasks per page)
    paginator = Paginator(tasks, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'tasks': page_obj,  # Pass the paginated object instead of the full queryset
        'sort_by': sort_by,
        'query': query,
    }
    return render(request, 'workflow/task_list.html', context)

@login_required
def update_task_status(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    is_manager = request.user.groups.filter(name='Manager').exists()
    if not (request.user == task.assigned_to or request.user.is_superuser or is_manager):
        messages.error(request, "You do not have permission to update this task.")
        return redirect('task_list')

    if request.method == 'POST':
        new_status = request.POST.get('status')

        valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
        if new_status not in valid_statuses:
            messages.error(request, "Invalid status value.")
            return render(request, 'workflow/update_task.html', {'task': task})

        task.status = new_status

        # Record ground truth when marked done
        if new_status == 'done':

            now = timezone.now()

            task.completed_at = now

            if task.due_date:
                # Convert due_date to aware datetime for comparison
                due_datetime = timezone.make_aware(
                    dt_module.datetime.combine(task.due_date, dt_module.time.max)
                )
                task.was_on_time = now <= due_datetime
            else:
                task.was_on_time = True  # no due date = can't be late

        task.save()

        # Recalculate priority on status change asynchronously
        recalculate_task_priority_async.delay(task.id)

        if request.headers.get('HX-Request'):
            # Return just the updated row for HTMX
            # We must fetch it fresh to ensure priority is accurate if sync
            return render(request, 'workflow/task_row_partial.html', {'task': task})

        messages.success(request, "Task updated successfully.")
        return redirect('task_list')

    return render(request, 'workflow/update_task.html', {'task': task})


@login_required
def dashboard(request):
    user = request.user

    if user.is_superuser or user.groups.filter(name='Manager').exists():
        # Admin and Managers see all tasks
        tasks = Task.objects.select_related('assigned_to').all()
    else:
        # Regular user sees only their assigned tasks
        tasks = Task.objects.select_related('assigned_to').filter(assigned_to=user)

    total_tasks = tasks.count()
    pending_tasks = tasks.filter(status__in=['todo', 'in_progress']).count()
    completed_tasks = tasks.filter(status='done').count()

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




@login_required
@user_passes_test(is_manager_or_admin)
def edit_task(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save()
            recalculate_task_priority_async.delay(task.id)

            messages.success(request, "Task updated successfully.")
            return redirect('task_list')
    else:
        form = TaskForm(instance=task)
    return render(request, 'workflow/edit_task.html', {'form': form, 'task': task})
