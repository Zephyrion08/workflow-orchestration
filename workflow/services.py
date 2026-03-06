import logging
from datetime import date
from django.contrib.auth.models import Group
from accounts.models import CustomUser
from workflow.models import Task
from workflow.ml_utils import predict_task_priority, predict_best_assignee

logger = logging.getLogger(__name__)

def assign_task_and_set_priority(task: Task) -> None:
    """
    Handles predicting the initial priority, assigning to the best user,
    and recalculating the priority based on the assigned user's workload.
    """
    due_date = task.due_date
    if due_date:
        days_to_due = (due_date - date.today()).days
        days_to_due = max(days_to_due, 0)
    else:
        days_to_due = 999

    # Initial priority prediction (assignee unknown yet)
    task.priority = predict_task_priority(
        status=task.status,
        days_to_due=days_to_due,
        pending_tasks=0,
    )

    admin_group = Group.objects.filter(name='Admin').first()
    candidates = CustomUser.objects.filter(
        is_active=True,
        is_superuser=False
    )
    if admin_group:
        candidates = candidates.exclude(groups=admin_group)
    candidates = list(candidates)

    if candidates:
        best_user, scores = predict_best_assignee(
            users=candidates,
            days_to_due=days_to_due,
            priority=task.priority,
        )
        task.assigned_to = best_user

        # Recalculate priority with real assignee workload
        workload = Task.objects.filter(
            assigned_to=best_user,
            status__in=['todo', 'in_progress']
        ).count()

        task.priority = predict_task_priority(
            status=task.status,
            days_to_due=days_to_due,
            pending_tasks=workload,
        )
        task.workload = workload

        logger.info(
            f"Auto-assigned '{task.title}' to {best_user.username} "
            f"| scores: {scores}"
        )
    task.save()


def recalculate_task_priority(task: Task) -> None:
    """
    Recalculates a task's priority and workload when status or dates are changed.
    """
    due_date = task.due_date
    if due_date:
        days_to_due = max((due_date - date.today()).days, 0)
    else:
        days_to_due = 999

    workload = Task.objects.filter(
        assigned_to=task.assigned_to,
        status__in=['todo', 'in_progress']
    ).exclude(pk=task.pk).count()

    task.priority = predict_task_priority(
        status=task.status,
        days_to_due=days_to_due,
        pending_tasks=workload,
    )
    task.workload = workload
    task.save()
