from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import classification_report, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"


def _prepare_data() -> pd.DataFrame:
    shipments = pd.read_csv(RAW_DIR / "shipments.csv", parse_dates=["shipment_date", "promised_delivery_date", "actual_delivery_date"])
    routes = pd.read_csv(RAW_DIR / "routes.csv")
    carriers = pd.read_csv(RAW_DIR / "carriers.csv")

    df = shipments.merge(routes, on="route_id", how="left").merge(carriers, on="carrier_id", how="left")

    df["is_high_risk_delay"] = (df["delay_minutes"] > 60).astype(int)
    df["shipment_month"] = df["shipment_date"].dt.month
    df["shipment_weekday"] = df["shipment_date"].dt.weekday

    mode_map = {"Road": 0, "Rail": 1, "Air": 2}
    risk_map = {"Low": 0, "Medium": 1, "High": 2}

    df["mode_code"] = df["mode"].map(mode_map).fillna(0)
    df["risk_zone_code"] = df["risk_zone"].map(risk_map).fillna(0)

    return df


def train_models() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = _prepare_data()

    feature_cols = [
        "distance_km",
        "typical_transit_hours",
        "fuel_cost_index",
        "weather_score",
        "traffic_score",
        "weight_kg",
        "base_cost_per_km",
        "reliability_score",
        "mode_code",
        "risk_zone_code",
        "shipment_month",
        "shipment_weekday",
    ]

    X = df[feature_cols]
    y_reg = df["delay_minutes"]
    y_clf = df["is_high_risk_delay"]

    X_train, X_test, y_reg_train, y_reg_test = train_test_split(X, y_reg, test_size=0.2, random_state=42)
    _, _, y_clf_train, y_clf_test = train_test_split(X, y_clf, test_size=0.2, random_state=42)

    reg = RandomForestRegressor(n_estimators=240, random_state=42, max_depth=12)
    reg.fit(X_train, y_reg_train)

    clf = RandomForestClassifier(n_estimators=240, random_state=42, max_depth=12)
    clf.fit(X_train, y_clf_train)

    reg_preds = reg.predict(X_test)
    clf_preds = clf.predict(X_test)

    mae = mean_absolute_error(y_reg_test, reg_preds)
    r2 = r2_score(y_reg_test, reg_preds)

    print(f"Delay Regression MAE: {mae:.2f}")
    print(f"Delay Regression R2: {r2:.3f}")
    print("Risk Classification Report:")
    print(classification_report(y_clf_test, clf_preds))

    full_pred_delay = reg.predict(X)
    full_pred_risk = clf.predict_proba(X)[:, 1]

    scored = df.copy()
    scored["predicted_delay_minutes"] = np.round(full_pred_delay, 2)
    scored["predicted_delay_risk"] = np.round(full_pred_risk, 4)

    scored.to_csv(PROCESSED_DIR / "shipments_scored.csv", index=False)

    monthly = scored.set_index("shipment_date").resample("ME").agg(
        shipment_count=("shipment_id", "count"),
        avg_delay=("delay_minutes", "mean"),
    )
    monthly["forecast_next_1m"] = monthly["shipment_count"].shift(1).rolling(3).mean().round(0)
    monthly["forecast_next_1m"] = monthly["forecast_next_1m"].fillna(monthly["shipment_count"].mean()).astype(int)
    monthly.reset_index().to_csv(PROCESSED_DIR / "monthly_forecast.csv", index=False)

    joblib.dump(reg, MODELS_DIR / "delay_regressor.joblib")
    joblib.dump(clf, MODELS_DIR / "risk_classifier.joblib")

    feature_importance = pd.DataFrame(
        {
            "feature": feature_cols,
            "importance": reg.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    feature_importance.to_csv(PROCESSED_DIR / "feature_importance.csv", index=False)
    print("Model artifacts and scored data generated successfully.")


if __name__ == "__main__":
    train_models()
