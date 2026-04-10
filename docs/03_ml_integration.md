# 3. Machine Learning Integration

## Objective
Apply ML to anticipate delivery delays and support proactive decisions.

## Models Used
- RandomForestRegressor: predicts delay minutes.
- RandomForestClassifier: predicts probability of high-risk delay (>60 min).

## Features Used
- Lane factors: distance_km, typical_transit_hours, risk_zone.
- Operational factors: weather_score, traffic_score, fuel_cost_index.
- Shipment factors: weight_kg.
- Carrier factors: base_cost_per_km, reliability_score, mode.
- Time factors: shipment month and weekday.

## Output Artifacts
- models/delay_regressor.joblib
- models/risk_classifier.joblib
- data/processed/shipments_scored.csv
- data/processed/monthly_forecast.csv
- data/processed/feature_importance.csv

## Decision-Making Value
- Detect high-risk deliveries before SLA breach.
- Prioritize interventions for routes with repeated predicted risk.
- Evaluate carriers on both cost and reliability.
- Estimate future shipment load for resource planning.

## Validation Metrics
The training script prints:
- Regression MAE and R2.
- Classification precision, recall, and F1 report.

These metrics support model quality justification in the report.
