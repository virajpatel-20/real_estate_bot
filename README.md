# 🏠 Real Estate Analysis Chatbot

A full-stack mini chatbot that lets users query real estate data (prices and demand) by area name. It returns a plain-English summary, an interactive line chart, and a filtered data table.

**Stack:** Django · pandas · React · Bootstrap 5 · Recharts

---

## Project Structure

```
real_estate_bot/
├── backend/                        # Django project
│   ├── backend/                    # Project config (settings, urls, wsgi, asgi)
│   ├── realestate/                 # Main Django app
│   │   ├── data/
│   │   │   └── sample_data.xlsx    # Source data — edit columns in views.py if needed
│   │   ├── views.py                # Core API logic
│   │   ├── urls.py
│   │   └── models.py               # Intentionally empty (data loaded from Excel)
│   ├── requirements.txt
│   ├── .env.example                # Copy to .env for production config
│   └── manage.py
└── frontend/                       # React (Create React App)
    ├── public/
    └── src/
        ├── index.js                # Bootstrap CSS imported here
        └── App.js                  # Main UI component
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+

---

## Setup & Running

### 1. Backend (Django)

```bash
cd backend

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations (sets up session/admin tables)
python manage.py migrate

# Start the development server
python manage.py runserver
```

The API will be available at `http://localhost:8000`.

### 2. Frontend (React)

```bash
cd frontend

npm install
npm start
```

Opens at `http://localhost:3000`. API calls are proxied to `http://localhost:8000` via the `"proxy"` field in `package.json`.

---

## API

### `POST /api/analyze/`

**Request body:**
```json
{
  "query": "Analyze Wakad",
  "area": "Wakad"
}
```

`area` is optional — if omitted, the backend extracts the area name from `query` by matching against known values in the dataset. Use `area` to pass an explicit override.

**Success response `200`:**
```json
{
  "area": "Wakad",
  "query": "Analyze Wakad",
  "summary": "For Wakad, we have data from 2018 to 2023. The average price is...",
  "chartData": [{ "year": 2018, "price": 5200.5, "demand": 120000 }],
  "tableData":  [{ ... }]
}
```

**Error responses:**

| Status | Meaning |
|--------|---------|
| 400 | Invalid JSON or area could not be detected from query |
| 404 | No rows found in the dataset for the given area |
| 500 | A configured column name is missing from the Excel file |

---

## Data File

Place your Excel file at `backend/realestate/data/sample_data.xlsx`.

The following column names are expected. If your file uses different headers, update the four constants at the top of `realestate/views.py`:

| Constant | Default column name |
|----------|-------------------|
| `AREA_COL` | `final location` |
| `YEAR_COL` | `year` |
| `PRICE_COL` | `flat - weighted average rate` |
| `DEMAND_COL` | `total carpet area supplied (sqft)` |

Set `DEMAND_COL = None` to disable the demand series entirely.

---

## Environment Variables (Production)

Copy `backend/.env.example` to `backend/.env` and fill in your values. The settings that must be changed before going to production are:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | Django secret key — must be unique and kept private |
| `DEBUG` | Set to `False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed domain names |
| `CORS_ALLOWED_ORIGINS` | Comma-separated list of allowed frontend origins |

When `DEBUG=False`, `CORS_ALLOW_ALL_ORIGINS` is automatically disabled and `CORS_ALLOWED_ORIGINS` is used instead.

---

## How It Works

1. The user types a natural-language query (e.g. *"Analyze Baner"*) into the chat input.
2. The frontend POSTs the query to `/api/analyze/`.
3. The backend matches the query against the known area list (two-pass: full-name substring → single-token match), filters the in-memory DataFrame, and returns a summary, chart data, and table data.
4. The frontend renders a summary card, a Recharts line chart (price & demand over years), and a Bootstrap data table.

---

## License

For educational / assignment purposes.
