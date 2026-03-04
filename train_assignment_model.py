import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

df = pd.read_csv('assignment_data.csv')

# Encode categorical features
le_user = LabelEncoder()
df['user_enc'] = le_user.fit_transform(df['user'])

le_priority = LabelEncoder()
df['priority_enc'] = le_priority.fit_transform(df['priority'])

X = df[['user_enc', 'days_to_due', 'workload', 'priority_enc']]
y = df['was_on_time']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# GradientBoosting gives probability estimates which we need for ranking
model = GradientBoostingClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

# Save artifacts
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'ml_models')
os.makedirs(MODEL_DIR, exist_ok=True)

joblib.dump(model,       os.path.join(MODEL_DIR, 'assignment_model.joblib'))
joblib.dump(le_user,     os.path.join(MODEL_DIR, 'assignment_user_encoder.joblib'))
joblib.dump(le_priority, os.path.join(MODEL_DIR, 'assignment_priority_encoder.joblib'))
print(f"Assignment model saved to {MODEL_DIR}")
