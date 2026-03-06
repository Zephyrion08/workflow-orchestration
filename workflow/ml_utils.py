import os
import joblib
import pandas as pd
import logging
from typing import List, Tuple, Dict, Any, Optional
from django.db.models import Model  # For CustomUser type hint

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'ml_models')

# --- Existing priority model ---
try:
    model = joblib.load(os.path.join(MODEL_DIR, 'task_priority_model.joblib'))
    le_status = joblib.load(os.path.join(MODEL_DIR, 'status_encoder.joblib'))
    le_priority = joblib.load(os.path.join(MODEL_DIR, 'priority_encoder.joblib'))
    ML_AVAILABLE = True
except Exception as e:
    logger.error(f"Priority model failed to load: {e}")
    ML_AVAILABLE = False

# --- Assignment model ---
try:
    assignment_model = joblib.load(os.path.join(MODEL_DIR, 'assignment_model.joblib'))
    le_assign_priority = joblib.load(os.path.join(MODEL_DIR, 'assignment_priority_encoder.joblib'))
    ASSIGNMENT_ML_AVAILABLE = True
except Exception as e:
    logger.error(f"Assignment model failed to load: {e}")
    ASSIGNMENT_ML_AVAILABLE = False

FALLBACK_STATUS = 'todo'


def predict_task_priority(status: str, days_to_due: int, pending_tasks: int, **kwargs: Any) -> str:
    """
    Predicts the priority of a task (High, Medium, Low) based on its status, 
    due date proximity, and the assignee's current workload using the trained ML model.
    """
    if not ML_AVAILABLE:
        return 'Medium'

    if status not in le_status.classes_:
        logger.warning(f"Unknown status '{status}', using fallback.")
        status = FALLBACK_STATUS

    status_enc = le_status.transform([status])[0]

    X_input = pd.DataFrame({
        'days_to_due': [days_to_due],
        'pending_tasks': [pending_tasks],
        'status_enc': [status_enc],
    })

    pred_enc = model.predict(X_input)[0]
    return le_priority.inverse_transform([pred_enc])[0]


def predict_best_assignee(users: List[Any], days_to_due: int, priority: str) -> Tuple[Optional[Any], Dict[str, Any]]:
    """
    Scores every user purely on situational features (workload, task priority) to determine
    the best candidate for assignment. Works natively with new accounts bypassing history reliance.
    
    Returns:
        Tuple containing the optimal CustomUser (or None) and a dictionary of prediction scores.
    """
    if not ASSIGNMENT_ML_AVAILABLE:
        logger.warning("Assignment model unavailable, falling back to first user.")
        return (users[0], {}) if users else (None, {})

    if priority not in le_assign_priority.classes_:
        priority = 'Medium'
    priority_enc = le_assign_priority.transform([priority])[0]

    from workflow.models import Task

    scores = {}
    for user in users:
        # Live workload — works for everyone including new users (returns 0)
        current_workload = Task.objects.filter(
            assigned_to=user,
            status__in=['todo', 'in_progress']
        ).count()

        X_input = pd.DataFrame({
            'days_to_due': [days_to_due],
            'workload': [current_workload],
            'priority_enc': [priority_enc],
        })

        success_prob = assignment_model.predict_proba(X_input)[0][1]

        # Burnout penalty
        if current_workload >= 10:
            burnout_penalty = 0.4
        elif current_workload >= 5:
            burnout_penalty = 1 - ((current_workload - 5) * 0.08)
        else:
            burnout_penalty = 1.0

        final_score = success_prob * burnout_penalty

        scores[user.username] = {
            'user': user,
            'success_prob': round(success_prob, 3),
            'current_workload': current_workload,
            'burnout_penalty': round(burnout_penalty, 3),
            'final_score': round(final_score, 3),
        }

        logger.debug(
            f"User: {user.username} | prob: {success_prob:.3f} | "
            f"workload: {current_workload} | penalty: {burnout_penalty:.3f} | "
            f"score: {final_score:.3f}"
        )

    if not scores:
        logger.warning("No scoreable users, falling back to first user.")
        return (users[0], {}) if users else (None, {})

    best_username = max(scores, key=lambda u: scores[u]['final_score'])
    return scores[best_username]['user'], scores