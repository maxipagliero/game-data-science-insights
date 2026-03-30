# Project 1 – In-Game Economy & Monetization Analytics

**Status: ✅ Complete**

## Objective
Analyze a free-to-play mobile game's in-game economy to understand player spending, retention, and monetization performance, and translate findings into actionable recommendations for game and monetization designers.

## Key Results

| Metric | Value |
|---|---|
| Average DAU | 164 |
| Total Revenue | $478.46 |
| Overall ARPU | $0.03 |
| Overall ARPPU | $8.86 |
| Payer Conversion Rate | 0.4% |
| Avg D1 Retention | 39.1% |
| Avg D7 Retention | 19.6% |
| Avg D30 Retention | 8.1% |

→ **[Read the full analysis report](reports/game_economy_report.md)**

---

## Tech Stack
- PostgreSQL (schema, KPI views)
- Python (pandas, numpy, matplotlib, seaborn)
- sqlalchemy + psycopg2 (database connectivity)
- python-dotenv (credential management)
- Jupyter Notebooks

## Key Questions
- Which player segments drive most revenue?
- How do retention and spending evolve over time?
- Which items or offers are underperforming or overperforming?
- What monetization changes would I recommend?

## Structure
- `data/` – raw and processed datasets
- `sql/` – table definitions and KPI views
- `notebooks/` – exploration and analysis
- `src/` – synthetic data generator and reusable functions
- `reports/` – stakeholder-oriented report and figures

---

## Setup

1. Copy `.env.example` to `.env` and fill in your PostgreSQL credentials:
```
   DATABASE_URL=postgresql+psycopg2://user:password@host:5432/dbname
```
2. Generate synthetic data:
```bash
   python src/generate_data.py
```
3. Create schemas, tables, and load data — see **Database Setup** below
4. Run notebooks in order:
   - `notebooks/01_explore_data.ipynb`
   - `notebooks/02_kpis_and_visuals.ipynb`

---

## Database Setup

### Schemas
The database uses two schemas:

| Schema | Purpose |
|---|---|
| `raw` | Data as-is from source CSVs — no transformations |
| `curated` | Business-ready views built on top of `raw` |

### SQL Files

| File | Description |
|---|---|
| `sql/01_schema.sql` | Creates `raw` and `curated` schemas, and defines the four `raw` tables |
| `sql/02_kpi_queries.sql` | Creates KPI views in the `curated` schema |

### Curated Views

| View | Description |
|---|---|
| `curated.daily_dau` | Daily active users |
| `curated.daily_revenue` | Daily revenue and payer count |
| `curated.daily_arpu_arppu` | ARPU and ARPPU joined with DAU |
| `curated.retention_cohorts` | D1 / D7 / D30 retention rates by install cohort |
| `curated.funnel` | 4-step conversion funnel (install → session → soft spend → IAP) |

---

## psql Reference

### Database server
This project runs against a local PostgreSQL server hosted on a home network and exposed on port 5432. Replace the placeholders below with your own connection details.

| Placeholder | Description |
|---|---|
| `<database_url>` | Hostname or IP of your PostgreSQL server |
| `<database_user>` | PostgreSQL user |
| `<database_name>` | Target database name |

### Connect to the database
```bash
psql -h <database_url> -p 5432 -U <database_user> -d <database_name>
```
You will be prompted for a password. To avoid repeated prompts, create `~/.pgpass`:
```
<database_url>:5432:*:<database_user>:YOUR_PASSWORD
```
Then restrict permissions:
```bash
chmod 600 ~/.pgpass
```

### Execute a SQL file
```bash
psql -h <database_url> -p 5432 -U <database_user> -d <database_name> -f path/to/file.sql
```

### Create schemas and tables
```bash
psql -h <database_url> -p 5432 -U <database_user> -d <database_name> \
  -f sql/01_schema.sql
```

### Load CSV data
Run these in order to respect foreign key constraints:
```bash
psql -h <database_url> -p 5432 -U <database_user> -d <database_name>
```
Then inside the psql session:
```sql
\copy raw.users          FROM 'data/raw/users.csv'          WITH (FORMAT csv, HEADER true);
\copy raw.items          FROM 'data/raw/items.csv'          WITH (FORMAT csv, HEADER true);
\copy raw.sessions       FROM 'data/raw/sessions.csv'       WITH (FORMAT csv, HEADER true);
\copy raw.economy_events FROM 'data/raw/economy_events.csv' WITH (FORMAT csv, HEADER true);
```

> Note: Use absolute paths if running `\copy` from outside the project directory.

### Create KPI views
```bash
psql -h <database_url> -p 5432 -U <database_user> -d <database_name> \
  -f sql/02_kpi_queries.sql
```

### Query a view
```sql
SELECT * FROM curated.daily_dau;
SELECT * FROM curated.funnel;
```