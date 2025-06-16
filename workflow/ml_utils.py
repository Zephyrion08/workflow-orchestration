import joblib
import os
import pandas as pd

# This will get the root project directory (where manage.py is)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to ml_models folder
MODEL_DIR = os.path.join(BASE_DIR, 'ml_models')

# Load model and encoders once
model = joblib.load(os.path.join(MODEL_DIR, 'task_priority_model.joblib'))
le_status = joblib.load(os.path.join(MODEL_DIR, 'status_encoder.joblib'))
le_priority = joblib.load(os.path.join(MODEL_DIR, 'priority_encoder.joblib'))

def predict_task_priority(status, due_date, pending_tasks):
    import datetime
    import pandas as pd

    # Encode status
    status_encoded = le_status.transform([status])[0]

    # Calculate days to due
    today = datetime.date.today()
    days_to_due = (due_date - today).days if due_date else 0

    # Create input DataFrame with the correct structure
    X_input = pd.DataFrame([{
        'days_to_due': days_to_due,
        'pending_tasks': pending_tasks,
        'status_enc': status_encoded
    }])

    # Predict
    pred_encoded = model.predict(X_input)[0]
    priority = le_priority.inverse_transform([pred_encoded])[0]
    return priority


