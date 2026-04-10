# 1. Problem Statement Analysis (P4 Delivery Visibility)

## Scope Definition

The problem addresses delays and increased transportation costs caused by low visibility in delivery operations.

### In scope
- Shipment tracking visibility from dispatch to delivery.
- Delay monitoring by route, carrier, and risk zone.
- Transportation cost variance analysis.
- Predictive insight to identify high-risk delays in advance.

### Out of scope
- Warehouse slotting optimization.
- Supplier lead-time negotiation workflows.
- Fleet maintenance scheduling.

## SCM Area(s) Addressed
- Order and delivery tracking.
- Transportation management.
- Logistics cost control.
- Exception management and proactive intervention.

## Business Impact
- Reduced late deliveries through early warning.
- Better carrier selection using KPI-driven comparisons.
- Lower delay penalty costs and improved customer SLA adherence.
- Improved executive decision-making with a single dashboard.

## Proposed Solution Approach
1. Build a relational data model for DCs, customers, routes, carriers, shipments, and tracking events.
2. Generate realistic shipment and event data simulating weather, traffic, and route risk.
3. Compute KPIs and train ML models for delay prediction and high-risk detection.
4. Develop an interactive dashboard with filters, trends, and forecast visuals.
5. Document insights, assumptions, and improvement roadmap.
