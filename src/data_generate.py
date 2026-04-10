from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import random

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"


def _ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def build_master_data(seed: int = 42) -> dict[str, pd.DataFrame]:
    random.seed(seed)
    np.random.seed(seed)

    distribution_centers = pd.DataFrame(
        [
            [1, "Bengaluru DC", "Bengaluru", "Karnataka", 12.9716, 77.5946],
            [2, "Chennai DC", "Chennai", "Tamil Nadu", 13.0827, 80.2707],
            [3, "Hyderabad DC", "Hyderabad", "Telangana", 17.3850, 78.4867],
            [4, "Mumbai DC", "Mumbai", "Maharashtra", 19.0760, 72.8777],
        ],
        columns=["dc_id", "dc_name", "city", "state", "latitude", "longitude"],
    )

    customers = pd.DataFrame(
        [
            [101, "RetailHub A", "Mysuru", "Karnataka", "Retail"],
            [102, "RetailHub B", "Coimbatore", "Tamil Nadu", "Retail"],
            [103, "ECom Fulfillment C", "Pune", "Maharashtra", "E-Commerce"],
            [104, "Wholesale D", "Vijayawada", "Andhra Pradesh", "Wholesale"],
            [105, "RetailHub E", "Kochi", "Kerala", "Retail"],
            [106, "Wholesale F", "Nagpur", "Maharashtra", "Wholesale"],
            [107, "ECom Fulfillment G", "Visakhapatnam", "Andhra Pradesh", "E-Commerce"],
            [108, "RetailHub H", "Mangalore", "Karnataka", "Retail"],
        ],
        columns=["customer_id", "customer_name", "city", "state", "segment"],
    )

    carriers = pd.DataFrame(
        [
            [201, "SwiftFreight", "Road", 32.5, 0.91],
            [202, "RapidHaul", "Road", 30.2, 0.86],
            [203, "AeroExpress", "Air", 75.0, 0.95],
            [204, "RailMove", "Rail", 24.0, 0.84],
        ],
        columns=["carrier_id", "carrier_name", "mode", "base_cost_per_km", "reliability_score"],
    )

    routes = pd.DataFrame(
        [
            [301, 1, 101, 150, 6.0, "Low"],
            [302, 1, 108, 360, 10.0, "Medium"],
            [303, 2, 102, 510, 14.0, "Medium"],
            [304, 3, 104, 280, 8.0, "Low"],
            [305, 4, 103, 145, 5.0, "Low"],
            [306, 4, 106, 840, 21.0, "High"],
            [307, 3, 107, 620, 16.0, "Medium"],
            [308, 2, 105, 680, 18.0, "High"],
        ],
        columns=[
            "route_id",
            "origin_dc_id",
            "destination_customer_id",
            "distance_km",
            "typical_transit_hours",
            "risk_zone",
        ],
    )

    return {
        "distribution_centers": distribution_centers,
        "customers": customers,
        "carriers": carriers,
        "routes": routes,
    }


def build_shipments(master: dict[str, pd.DataFrame], n: int = 900, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)

    routes = master["routes"]
    carriers = master["carriers"]

    start_date = datetime(2024, 1, 1)
    records = []

    for i in range(1, n + 1):
        route = routes.sample(1).iloc[0]
        carrier = carriers.sample(1).iloc[0]

        shipment_date = start_date + timedelta(days=int(np.random.randint(0, 450)))
        promised_hours = float(route["typical_transit_hours"]) + np.random.normal(0, 1.0)

        weather_score = np.clip(np.random.normal(0.55, 0.25), 0.0, 1.0)
        traffic_score = np.clip(np.random.normal(0.5, 0.2), 0.0, 1.0)
        fuel_cost_index = np.clip(np.random.normal(1.0, 0.12), 0.7, 1.5)

        zone_penalty = {"Low": 0.0, "Medium": 18.0, "High": 42.0}[route["risk_zone"]]
        reliability_bonus = (1.0 - carrier["reliability_score"]) * 120.0

        delay_minutes = int(
            max(
                -90,
                np.random.normal(0, 50)
                + zone_penalty
                + (weather_score - 0.45) * 85.0
                + (traffic_score - 0.45) * 95.0
                + reliability_bonus,
            )
        )

        promised_delivery_date = shipment_date + timedelta(hours=max(3.0, promised_hours))
        actual_delivery_date = promised_delivery_date + timedelta(minutes=delay_minutes)

        weight_kg = float(np.clip(np.random.normal(420, 180), 40, 1200))
        planned_cost = float(route["distance_km"] * carrier["base_cost_per_km"] * fuel_cost_index)
        delay_cost = max(0, delay_minutes) * 2.0
        actual_cost = planned_cost + delay_cost + np.random.normal(0, 180)

        status = "Delivered"
        on_time_flag = 1 if delay_minutes <= 0 else 0

        records.append(
            [
                i,
                f"ORD{i:05d}",
                int(route["route_id"]),
                int(carrier["carrier_id"]),
                shipment_date.isoformat(sep=" "),
                promised_delivery_date.isoformat(sep=" "),
                actual_delivery_date.isoformat(sep=" "),
                status,
                round(weight_kg, 2),
                round(fuel_cost_index, 3),
                round(weather_score, 3),
                round(traffic_score, 3),
                round(planned_cost, 2),
                round(actual_cost, 2),
                delay_minutes,
                on_time_flag,
            ]
        )

    return pd.DataFrame(
        records,
        columns=[
            "shipment_id",
            "order_id",
            "route_id",
            "carrier_id",
            "shipment_date",
            "promised_delivery_date",
            "actual_delivery_date",
            "status",
            "weight_kg",
            "fuel_cost_index",
            "weather_score",
            "traffic_score",
            "planned_cost",
            "actual_cost",
            "delay_minutes",
            "on_time_flag",
        ],
    )


def build_tracking_events(shipments: pd.DataFrame, seed: int = 42) -> pd.DataFrame:
    random.seed(seed)
    np.random.seed(seed)

    event_types = ["Picked Up", "In Transit", "At Hub", "Out For Delivery", "Delivered"]
    rows = []
    event_id = 1

    for _, s in shipments.iterrows():
        ship_ts = datetime.fromisoformat(s["shipment_date"])
        actual_ts = datetime.fromisoformat(s["actual_delivery_date"])
        lead_minutes = max(90, int((actual_ts - ship_ts).total_seconds() / 60))

        checkpoints = [0.0, 0.28, 0.56, 0.83, 1.0]

        for idx, ratio in enumerate(checkpoints):
            ts = ship_ts + timedelta(minutes=int(lead_minutes * ratio))
            city = random.choice(["Bengaluru", "Chennai", "Hyderabad", "Mumbai", "Pune", "Mysuru"])
            delay_jump = 0 if idx < 2 else int(np.random.normal(5, 15))

            rows.append(
                [
                    event_id,
                    int(s["shipment_id"]),
                    ts.isoformat(sep=" "),
                    event_types[idx],
                    city,
                    round(np.random.uniform(11.5, 20.2), 5),
                    round(np.random.uniform(72.5, 81.3), 5),
                    max(0, delay_jump),
                ]
            )
            event_id += 1

    return pd.DataFrame(
        rows,
        columns=[
            "event_id",
            "shipment_id",
            "event_timestamp",
            "event_type",
            "event_city",
            "latitude",
            "longitude",
            "event_delay_minutes",
        ],
    )


def main() -> None:
    _ensure_dirs()
    master = build_master_data()
    shipments = build_shipments(master)
    tracking_events = build_tracking_events(shipments)

    for name, df in master.items():
        df.to_csv(RAW_DIR / f"{name}.csv", index=False)

    shipments.to_csv(RAW_DIR / "shipments.csv", index=False)
    tracking_events.to_csv(RAW_DIR / "tracking_events.csv", index=False)

    print("Sample data generated in data/raw")


if __name__ == "__main__":
    main()
