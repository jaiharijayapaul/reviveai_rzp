"""
Trains the recovery-probability model on the synthetic dataset and
serializes it for the FastAPI prediction_service to load.

Usage: python ml/train.py
"""
from pathlib import Path
import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score, classification_report

DATA_PATH = Path(__file__).parent / "data" / "synthetic_recovery_dataset.csv"
ARTIFACT_PATH = Path(__file__).parent / "artifacts" / "recovery_model.joblib"

FEATURE_COLUMNS = [
    "amount",
    "previous_attempts",
    "previous_successful_payments",
    "previous_failed_payments",
    "checkout_abandonment_minutes",
    "hour_of_day",
    "is_temporary_failure",
]


def main():
    if not DATA_PATH.exists():
        raise SystemExit(f"Dataset not found at {DATA_PATH}. Run `python ml/generate_dataset.py` first.")

    df = pd.read_csv(DATA_PATH)
    X = df[FEATURE_COLUMNS]
    y = df["recovered"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    model = RandomForestClassifier(
        n_estimators=300, max_depth=10, min_samples_leaf=5, random_state=42, n_jobs=-1,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    print("=== Evaluation (synthetic holdout set) ===")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.3f}")
    print(f"ROC AUC:  {roc_auc_score(y_test, y_proba):.3f}")
    print(classification_report(y_test, y_pred))

    print("=== Feature importance ===")
    for name, imp in sorted(zip(FEATURE_COLUMNS, model.feature_importances_), key=lambda x: -x[1]):
        print(f"  {name:35s} {imp:.3f}")

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ARTIFACT_PATH)
    print(f"\nSaved model to {ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
