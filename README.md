# SCM P4 Project - Delivery Visibility Dashboard

This project implements the SCM course problem statement P4:

> Lack of real-time visibility into deliveries may result in delays and increased transportation costs.

The solution includes:
- A relational database design for shipments, routes, carriers, and tracking events.
- Realistic sample data generation.
- ML integration for ETA delay prediction and delivery risk classification.
- An interactive dashboard for executive decision-making.
- Complete documentation and presentation assets.

## Project Structure

- `src/database/schema.sql` - database schema
- `src/data_generate.py` - sample dataset generator
- `src/ml/train_models.py` - ML training and forecast generation
- `src/dashboard/app.py` - interactive Dash dashboard
- `scripts/setup_db.py` - initialize MySQL database and seed data
- `docs/` - analysis, methodology, business impact, and deliverables
- `report/` - consolidated project report draft

## Quick Start

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Generate data and train models:

```bash
python src/data_generate.py
python src/ml/train_models.py
```

4. Create database and load data:

```bash
python scripts/setup_db.py
```

5. Run dashboard:

```bash
python src/dashboard/app.py
```

Open http://127.0.0.1:8050 in a browser.

## MySQL Setup

This version uses MySQL through SQLAlchemy and PyMySQL.

You can keep the connection values in a local `.env` file at the project root. The app loads it automatically if `python-dotenv` is installed.

Default connection settings:
- Host: `localhost`
- Port: `3306`
- User: `root`
- Password: empty
- Database: `scm_delivery_visibility`

You can override these with environment variables:
- `SCM_MYSQL_HOST`
- `SCM_MYSQL_PORT`
- `SCM_MYSQL_USER`
- `SCM_MYSQL_PASSWORD`
- `SCM_MYSQL_DATABASE`

Recommended `.env` content:

```env
SCM_MYSQL_HOST=localhost
SCM_MYSQL_PORT=3306
SCM_MYSQL_USER=root
SCM_MYSQL_PASSWORD=your_mysql_password
SCM_MYSQL_DATABASE=scm_delivery_visibility
```

After running `python scripts/setup_db.py`, inspect the tables in MySQL Workbench, phpMyAdmin, or any SQL client connected to that database.

## Team Submission Notes

- Update `report/SCM22CS_P4_001-002-003.md` with your actual SRNs.
- Export the Markdown report to PDF using the required naming format.
- Use the class template when provided and merge content from this report.

## KPI Coverage

- On-time delivery rate
- Average delay minutes
- Delay by carrier and route
- Transit time trend
- Cost-per-km and delay-cost impact
- Predicted delay risk (next periods)

## ML Models Used

- Random Forest Regressor for delay magnitude estimation.
- Random Forest Classifier for high-risk delay prediction.
- Monthly demand proxy forecast based on shipments and route trend.
