import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

np.random.seed(42)
n = 3000

days_to_due = np.concatenate([
    np.random.randint(0, 3, 700),
    np.random.randint(3, 7, 800),
    np.random.randint(7, 30, 900),
    np.random.randint(30, 180, 600),
])

workload = np.random.randint(0, 12, len(days_to_due))
priorities = np.random.choice(['High', 'Medium', 'Low'], len(days_to_due))


def compute_success(days, wl, priority):
    base = 0.85
    if wl >= 10:
        base *= 0.4
    elif wl >= 5:
        base *= 1 - ((wl - 5) * 0.08)
    if days <= 2:
        base *= 0.75
    if priority == 'High':
        base *= 0.85
    return int(np.random.random() < base)


records = []
for d, w, p in zip(days_to_due, workload, priorities):
    records.append({
        'days_to_due': int(d),
        'workload': int(w),
        'priority': p,
        'was_on_time': compute_success(d, w, p),
    })

df = pd.DataFrame(records)
print("Overall completion rate:", df['was_on_time'].mean().round(3))
print("Completion by priority:\n", df.groupby('priority')['was_on_time'].mean())

le_priority = LabelEncoder()
df['priority_enc'] = le_priority.fit_transform(df['priority'])

X = df[['days_to_due', 'workload', 'priority_enc']]
y = df['was_on_time']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = GradientBoostingClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("\nAccuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'ml_models')
os.makedirs(MODEL_DIR, exist_ok=True)

joblib.dump(model,       os.path.join(MODEL_DIR, 'assignment_model.joblib'))
joblib.dump(le_priority, os.path.join(MODEL_DIR, 'assignment_priority_encoder.joblib'))

print(f"\nSaved to {MODEL_DIR}")
print("No user encoder needed — model works for any user.")
