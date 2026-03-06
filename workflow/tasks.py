from celery import shared_task
from .models import Task
from .services import assign_task_and_set_priority, recalculate_task_priority
import logging

logger = logging.getLogger(__name__)


@shared_task
def assign_and_score_task_async(task_id: int):
    """
    Background job to run the ML priority & assignment engine.
    """
    try:
        task = Task.objects.get(id=task_id)
        assign_task_and_set_priority(task)
        return True
    except Task.DoesNotExist:
        logger.error(f"Task with ID {task_id} not found during async assignment.")
        return False


@shared_task
def recalculate_task_priority_async(task_id: int):
    """
    Background job to recalculate priority on demand.
    """
    try:
        task = Task.objects.get(id=task_id)
        recalculate_task_priority(task)
        return True
    except Task.DoesNotExist:
        logger.error(f"Task with ID {task_id} not found during async priority recalc.")
        return False
