"""
Standalone CLI for sanity-checking the trained model outside the API.

Usage:
    python ml/predict.py --amount 99900 --prev-success 4 --prev-failed 0 \
        --attempts 1 --abandon-min 0 --hour 14 --temporary 1
"""
import argparse
from pathlib import Path
import joblib

ARTIFACT_PATH = Path(__file__).parent / "artifacts" / "recovery_model.joblib"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--amount", type=int, required=True, help="Amount in paise")
    parser.add_argument("--attempts", type=int, default=1)
    parser.add_argument("--prev-success", type=int, default=0)
    parser.add_argument("--prev-failed", type=int, default=0)
    parser.add_argument("--abandon-min", type=int, default=0)
    parser.add_argument("--hour", type=int, default=12)
    parser.add_argument("--temporary", type=int, default=0, choices=[0, 1])
    args = parser.parse_args()

    if not ARTIFACT_PATH.exists():
        raise SystemExit("No trained model found. Run `python ml/train.py` first.")

    model = joblib.load(ARTIFACT_PATH)
    features = [[
        args.amount, args.attempts, args.prev_success, args.prev_failed,
        args.abandon_min, args.hour, args.temporary,
    ]]
    proba = model.predict_proba(features)[0][1]
    print(f"Recovery probability: {proba:.3f}")


if __name__ == "__main__":
    main()
