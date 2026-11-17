"""Clean the raw dataset and engineer features.

Input : data/raw/customer_shopping_behavior.csv
Output: data/processed/customer_shopping_behavior_cleaned.csv
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "customer_shopping_behavior.csv"
OUT = ROOT / "data" / "processed" / "customer_shopping_behavior_cleaned.csv"

FREQUENCY_DAYS = {
    "Weekly": 7,
    "Fortnightly": 14,
    "Bi-Weekly": 14,
    "Monthly": 30,
    "Quarterly": 90,
    "Every 3 Months": 90,
    "Annually": 365,
}


def clean(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Impute missing review ratings with the category median
    df["Review Rating"] = df.groupby("Category")["Review Rating"].transform(
        lambda s: s.fillna(s.median())
    )

    # 2. snake_case column names
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    df = df.rename(columns={"purchase_amount_(usd)": "purchase_amount"})

    # 3. Feature engineering
    df["age_group"] = pd.qcut(
        df["age"], q=4, labels=["Young Adult", "Adult", "Middle-aged", "Senior"]
    )
    df["purchase_frequency_days"] = df["frequency_of_purchases"].map(FREQUENCY_DAYS)

    # 4. promo_code_used is identical to discount_applied -> redundant
    assert (df["discount_applied"] == df["promo_code_used"]).all()
    return df.drop(columns="promo_code_used")


def main() -> None:
    df = clean(pd.read_csv(RAW))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"Saved {len(df)} rows x {df.shape[1]} cols -> {OUT.relative_to(ROOT)}")
    print("Missing values left:", int(df.isna().sum().sum()))


if __name__ == "__main__":
    main()
