import os
import joblib
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Base directory (adjust if needed)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_DIR = os.path.join(BASE_DIR, 'ml_models')

# Load model and encoders once when the module is imported
try:
    model = joblib.load(os.path.join(MODEL_DIR, 'task_priority_model.joblib'))
    le_status = joblib.load(os.path.join(MODEL_DIR, 'status_encoder.joblib'))
    le_priority = joblib.load(os.path.join(MODEL_DIR, 'priority_encoder.joblib'))
    ML_AVAILABLE = True
except Exception as e:
    logger.error(f"ML models failed to load: {e}")
    ML_AVAILABLE = False

# Consistent explicit fallback as recommended
FALLBACK_STATUS = 'todo'

def predict_task_priority(status, days_to_due, pending_tasks, **kwargs):
    if not ML_AVAILABLE:
        return 'Medium'  # Safe fallback if models are missing/corrupted
        
    # Guard against previously unseen labels
    if status not in le_status.classes_:
        logger.warning(f"Unknown status '{status}' passed to ML model, using fallback '{FALLBACK_STATUS}'.")
        status = FALLBACK_STATUS
    
    status_enc = le_status.transform([status])[0]
    
    X_input = pd.DataFrame({
        'days_to_due': [days_to_due],
        'pending_tasks': [pending_tasks],
        'status_enc': [status_enc],
    })
    
    # Ensure columns are in the exact same order as training
    X_input = X_input[['days_to_due', 'pending_tasks', 'status_enc']]

    pred_enc = model.predict(X_input)[0]
    priority = le_priority.inverse_transform([pred_enc])[0]
    return priority