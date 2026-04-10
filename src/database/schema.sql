DROP TABLE IF EXISTS tracking_events;
DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS routes;
DROP TABLE IF EXISTS carriers;
DROP TABLE IF EXISTS distribution_centers;
DROP TABLE IF EXISTS customers;

CREATE TABLE distribution_centers (
    dc_id INT PRIMARY KEY,
    dc_name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6)
);

CREATE TABLE customers (
    customer_id INT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    segment TEXT NOT NULL
);

CREATE TABLE carriers (
    carrier_id INT PRIMARY KEY,
    carrier_name TEXT NOT NULL,
    mode TEXT NOT NULL,
    base_cost_per_km DECIMAL(10, 2) NOT NULL,
    reliability_score DECIMAL(5, 4) NOT NULL
);

CREATE TABLE routes (
    route_id INT PRIMARY KEY,
    origin_dc_id INT NOT NULL,
    destination_customer_id INT NOT NULL,
    distance_km DECIMAL(10, 2) NOT NULL,
    typical_transit_hours DECIMAL(10, 2) NOT NULL,
    risk_zone TEXT NOT NULL,
    FOREIGN KEY (origin_dc_id) REFERENCES distribution_centers(dc_id),
    FOREIGN KEY (destination_customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE shipments (
    shipment_id INT PRIMARY KEY,
    order_id TEXT NOT NULL,
    route_id INT NOT NULL,
    carrier_id INT NOT NULL,
    shipment_date DATETIME NOT NULL,
    promised_delivery_date DATETIME NOT NULL,
    actual_delivery_date DATETIME,
    status TEXT NOT NULL,
    weight_kg DECIMAL(10, 2) NOT NULL,
    fuel_cost_index DECIMAL(6, 3) NOT NULL,
    weather_score DECIMAL(6, 3) NOT NULL,
    traffic_score DECIMAL(6, 3) NOT NULL,
    planned_cost DECIMAL(12, 2) NOT NULL,
    actual_cost DECIMAL(12, 2),
    delay_minutes INT,
    on_time_flag TINYINT(1),
    FOREIGN KEY (route_id) REFERENCES routes(route_id),
    FOREIGN KEY (carrier_id) REFERENCES carriers(carrier_id)
);

CREATE TABLE tracking_events (
    event_id INT PRIMARY KEY,
    shipment_id INT NOT NULL,
    event_timestamp DATETIME NOT NULL,
    event_type TEXT NOT NULL,
    event_city TEXT NOT NULL,
    latitude DECIMAL(10, 6),
    longitude DECIMAL(10, 6),
    event_delay_minutes INT DEFAULT 0,
    FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);
