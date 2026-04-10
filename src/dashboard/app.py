from __future__ import annotations

import sys
from pathlib import Path

import dash
from dash import Dash, Input, Output, dcc, html
import pandas as pd
import plotly.express as px


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database.mysql_utils import mysql_engine

PROCESSED_DIR = ROOT / "data" / "processed"


def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    scored = pd.read_csv(PROCESSED_DIR / "shipments_scored.csv", parse_dates=["shipment_date"])
    engine = mysql_engine(include_database=True)
    routes = pd.read_sql("SELECT * FROM routes", engine)
    carriers = pd.read_sql("SELECT * FROM carriers", engine)
    forecast = pd.read_csv(PROCESSED_DIR / "monthly_forecast.csv", parse_dates=["shipment_date"])

    df = scored.merge(routes, on="route_id", how="left").merge(carriers, on="carrier_id", how="left")
    df["month"] = df["shipment_date"].dt.to_period("M").astype(str)
    return df, routes, carriers, forecast


def _kpi_cards(df: pd.DataFrame) -> html.Div:
    on_time = (df["on_time_flag"].mean() * 100.0) if len(df) else 0.0
    avg_delay = df["delay_minutes"].mean() if len(df) else 0.0
    avg_cost_gap = (df["actual_cost"] - df["planned_cost"]).mean() if len(df) else 0.0
    risk_rate = (df["predicted_delay_risk"] > 0.6).mean() * 100 if len(df) else 0.0

    def card(title: str, value: str, subtitle: str) -> html.Div:
        return html.Div(
            [
                html.P(title, className="kpi-title"),
                html.H3(value, className="kpi-value"),
                html.P(subtitle, className="kpi-subtitle"),
            ],
            className="kpi-card",
        )

    return html.Div(
        [
            card("On-Time Delivery", f"{on_time:.1f}%", "Higher is better"),
            card("Average Delay", f"{avg_delay:.1f} min", "Lower is better"),
            card("Average Cost Overrun", f"INR {avg_cost_gap:,.0f}", "Actual - Planned"),
            card("Predicted High-Risk Share", f"{risk_rate:.1f}%", "Model risk > 0.6"),
        ],
        className="kpi-grid",
    )


def _layout(app: Dash, df: pd.DataFrame, carriers: pd.DataFrame) -> html.Div:
    months = sorted(df["month"].unique())
    carrier_options = [{"label": c, "value": c} for c in sorted(carriers["carrier_name"].unique())]

    return html.Div(
        [
            html.Div(className="bg-orb orb-1"),
            html.Div(className="bg-orb orb-2"),
            html.Div(
                [
                    html.H1("SCM Delivery Visibility Command Center"),
                    html.P("Real-time style analytics for delays, route risk, and transportation cost control."),
                ],
                className="hero",
            ),
            html.Div(
                [
                    html.Div(
                        [
                            html.Label("Select Month"),
                            dcc.Dropdown(
                                id="month-dropdown",
                                options=[{"label": "All", "value": "ALL"}] + [{"label": m, "value": m} for m in months],
                                value="ALL",
                                clearable=False,
                            ),
                        ],
                        className="filter-block",
                    ),
                    html.Div(
                        [
                            html.Label("Select Carrier"),
                            dcc.Dropdown(
                                id="carrier-dropdown",
                                options=[{"label": "All", "value": "ALL"}] + carrier_options,
                                value="ALL",
                                clearable=False,
                            ),
                        ],
                        className="filter-block",
                    ),
                ],
                className="filters",
            ),
            html.Div(id="kpi-section"),
            html.Div(
                [
                    dcc.Graph(id="delay-trend"),
                    dcc.Graph(id="carrier-performance"),
                ],
                className="chart-grid",
            ),
            html.Div(
                [
                    dcc.Graph(id="route-risk"),
                    dcc.Graph(id="forecast-chart"),
                ],
                className="chart-grid",
            ),
        ],
        className="page",
    )


def register_callbacks(app: Dash, df: pd.DataFrame, forecast: pd.DataFrame) -> None:
    @app.callback(
        Output("kpi-section", "children"),
        Output("delay-trend", "figure"),
        Output("carrier-performance", "figure"),
        Output("route-risk", "figure"),
        Output("forecast-chart", "figure"),
        Input("month-dropdown", "value"),
        Input("carrier-dropdown", "value"),
    )
    def update_dashboard(month_value: str, carrier_value: str):
        filtered = df.copy()

        if month_value != "ALL":
            filtered = filtered[filtered["month"] == month_value]
        if carrier_value != "ALL":
            filtered = filtered[filtered["carrier_name"] == carrier_value]

        kpis = _kpi_cards(filtered)

        trend = (
            filtered.set_index("shipment_date")
            .resample("W")
            .agg(avg_delay=("delay_minutes", "mean"), shipments=("shipment_id", "count"))
            .reset_index()
        )
        fig_delay = px.line(trend, x="shipment_date", y="avg_delay", markers=True, title="Weekly Average Delay")
        fig_delay.update_layout(template="plotly_white")

        carrier_perf = (
            filtered.groupby("carrier_name", as_index=False)
            .agg(on_time_rate=("on_time_flag", "mean"), avg_cost=("actual_cost", "mean"))
        )
        carrier_perf["on_time_rate"] = carrier_perf["on_time_rate"] * 100
        fig_carrier = px.bar(
            carrier_perf,
            x="carrier_name",
            y="on_time_rate",
            color="avg_cost",
            title="Carrier On-Time Rate vs Avg Cost",
            color_continuous_scale="Blues",
        )
        fig_carrier.update_layout(template="plotly_white")

        route_risk = (
            filtered.groupby("route_id", as_index=False)
            .agg(predicted_delay_risk=("predicted_delay_risk", "mean"), avg_delay=("delay_minutes", "mean"))
        )
        fig_risk = px.scatter(
            route_risk,
            x="route_id",
            y="predicted_delay_risk",
            size="avg_delay",
            color="avg_delay",
            title="Route Risk Map (Predicted)",
            color_continuous_scale="OrRd",
        )
        fig_risk.update_layout(template="plotly_white")

        fig_forecast = px.line(
            forecast,
            x="shipment_date",
            y=["shipment_count", "forecast_next_1m"],
            title="Monthly Shipment Demand and Forecast",
            markers=True,
        )
        fig_forecast.update_layout(template="plotly_white")

        return kpis, fig_delay, fig_carrier, fig_risk, fig_forecast


def build_app() -> Dash:
    df, _, carriers, forecast = load_data()
    app = dash.Dash(__name__)
    app.title = "SCM Delivery Visibility Dashboard"
    app.layout = _layout(app, df, carriers)
    register_callbacks(app, df, forecast)

    app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
            :root {
                --bg: #f4f7f2;
                --ink: #14281d;
                --brand: #2d6a4f;
                --accent: #ff9f1c;
                --panel: #ffffff;
                --muted: #516159;
            }
            body {
                margin: 0;
                font-family: 'IBM Plex Sans', sans-serif;
                background: radial-gradient(circle at 20% 10%, #d8f3dc 0%, transparent 35%),
                            radial-gradient(circle at 90% 5%, #ffd6a5 0%, transparent 30%),
                            var(--bg);
                color: var(--ink);
            }
            .page {
                max-width: 1200px;
                margin: 0 auto;
                padding: 24px;
                position: relative;
            }
            .hero h1 {
                font-family: 'Space Grotesk', sans-serif;
                font-size: 2.1rem;
                margin: 0;
            }
            .hero p {
                margin-top: 6px;
                color: var(--muted);
            }
            .filters {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 12px;
                margin: 16px 0 20px;
            }
            .filter-block {
                background: rgba(255, 255, 255, 0.78);
                border: 1px solid #cde5d8;
                padding: 10px;
                border-radius: 10px;
                backdrop-filter: blur(5px);
            }
            .kpi-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 12px;
                margin-bottom: 16px;
            }
            .kpi-card {
                background: var(--panel);
                border: 1px solid #d6eadf;
                border-left: 6px solid var(--brand);
                border-radius: 10px;
                padding: 12px;
                box-shadow: 0 8px 24px rgba(20, 40, 29, 0.05);
            }
            .kpi-title {
                margin: 0;
                color: var(--muted);
                font-size: 0.9rem;
            }
            .kpi-value {
                margin: 6px 0;
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.6rem;
                color: var(--brand);
            }
            .kpi-subtitle {
                margin: 0;
                color: #6a7c73;
                font-size: 0.85rem;
            }
            .chart-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
                gap: 12px;
                margin-bottom: 12px;
            }
            .bg-orb {
                position: fixed;
                border-radius: 50%;
                filter: blur(80px);
                pointer-events: none;
                opacity: 0.35;
                animation: floaty 8s ease-in-out infinite;
            }
            .orb-1 {
                width: 220px;
                height: 220px;
                background: #95d5b2;
                top: -30px;
                right: -40px;
            }
            .orb-2 {
                width: 180px;
                height: 180px;
                background: #ffd6a5;
                bottom: 20px;
                left: -50px;
            }
            @keyframes floaty {
                0%, 100% { transform: translateY(0px); }
                50% { transform: translateY(12px); }
            }
            @media (max-width: 760px) {
                .chart-grid {
                    grid-template-columns: 1fr;
                }
                .hero h1 {
                    font-size: 1.6rem;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

    return app


if __name__ == "__main__":
    app = build_app()
    app.run_server(debug=True)
