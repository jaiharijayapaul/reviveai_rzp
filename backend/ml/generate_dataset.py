"""
Generates a SYNTHETIC/DEMO dataset for training the recovery-probability
model. This is not real merchant data — it is randomly generated with
realistic-looking correlations so the model has meaningful signal to learn.

Usage: python ml/generate_dataset.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

OUT_PATH = Path(__file__).parent / "data" / "synthetic_recovery_dataset.csv"

FAILURE_REASONS = ["temporary", "network_error", "card_declined", "insufficient_funds", "checkout_abandoned"]


def generate(n=8000, seed=42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    amount = rng.lognormal(mean=8.5, sigma=1.0, size=n).astype(int)  # paise, skewed toward smaller amounts
    amount = np.clip(amount, 5000, 10_000_000)

    previous_attempts = rng.integers(1, 4, size=n)
    previous_successful = rng.poisson(2.0, size=n)
    previous_failed = rng.poisson(0.8, size=n)
    abandonment_minutes = rng.choice([0, 0, 0, 1, 2, 5, 10, 30], size=n)
    hour_of_day = rng.integers(0, 24, size=n)
    failure_reason = rng.choice(FAILURE_REASONS, size=n)
    is_temporary = np.isin(failure_reason, ["temporary", "network_error"]).astype(int)

    # Latent "true" recovery probability with realistic correlations, then
    # sample a binary outcome from it to create labeled training data.
    logit = (
        -0.3
        + 0.9 * is_temporary
        + 0.30 * np.minimum(previous_successful, 6)
        - 0.55 * np.minimum(previous_failed, 5)
        - 0.35 * (previous_attempts - 1)
        + 0.6 * ((abandonment_minutes.astype(float) > 0) & (abandonment_minutes <= 5))
        - 1.1 * (amount > 5_000_000)
        - 0.0000015 * amount
    )
    true_proba = 1 / (1 + np.exp(-logit))
    recovered = rng.binomial(1, true_proba)

    df = pd.DataFrame({
        "amount": amount,
        "previous_attempts": previous_attempts,
        "previous_successful_payments": previous_successful,
        "previous_failed_payments": previous_failed,
        "checkout_abandonment_minutes": abandonment_minutes,
        "hour_of_day": hour_of_day,
        "is_temporary_failure": is_temporary,
        "failure_reason": failure_reason,  # kept for reference / EDA, not used as a model feature directly
        "recovered": recovered,
    })
    return df


if __name__ == "__main__":
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df = generate()
    df.to_csv(OUT_PATH, index=False)
    print(f"Wrote {len(df)} SYNTHETIC rows to {OUT_PATH}")
    print(f"Positive rate (recovered=1): {df['recovered'].mean():.2%}")
