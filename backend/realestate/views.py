import json
import os
import re

import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# ---- 1. Load Excel once at startup ----

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH = os.path.join(BASE_DIR, 'data', 'sample_data.xlsx')

try:
    df = pd.read_excel(EXCEL_PATH)
except Exception as e:
    print("ERROR reading Excel file:", e)
    df = pd.DataFrame()

# ==== IMPORTANT: match these to your EXACT Excel headers ====
AREA_COL   = "final location"
YEAR_COL   = "year"
PRICE_COL  = "flat - weighted average rate"
DEMAND_COL = "total carpet area supplied (sqft)"   # set to None to disable demand

print("Excel columns:", list(df.columns))


def get_area_from_query(query: str):
    """
    Extract the area name from a user query by matching against the known list
    of areas in the dataset.  Two passes are used:

    Pass 1 - try every known area name as a substring of the query (case-insensitive).
             This correctly handles multi-word area names such as 'Wakad - Hinjewadi'.
    Pass 2 - try each individual token from the query against the area list.
             This handles queries like 'Analyze Baner' where the area is one word.

    A plain last-word fallback is intentionally avoided because it caused false
    matches (e.g. 'What about Wakad please' -> 'please').
    """
    if AREA_COL not in df.columns:
        return None

    areas = df[AREA_COL].dropna().astype(str).unique()
    q = query.lower()

    # Pass 1: full area string contained in query
    for area in areas:
        if area.lower() in q:
            return str(area)

    # Pass 2: any query token matches an area name
    tokens = re.findall(r'[A-Za-z]+', query)
    for token in tokens:
        for area in areas:
            if token.lower() == area.lower():
                return str(area)

    return None


def _safe(value):
    """Convert numpy scalar types to plain Python types for JSON serialisation."""
    if pd.isna(value):
        return None
    if hasattr(value, 'item'):          # numpy int/float
        return value.item()
    return value


@csrf_exempt
@require_POST
def analyze_area(request):
    # --- parse JSON body ---
    try:
        body = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    query = body.get('query', '') or ''
    manual_area = body.get('area')  # optional override from frontend

    # --- choose area ---
    area = manual_area or get_area_from_query(query)
    if not area:
        return JsonResponse({'error': 'Could not detect area from query'}, status=400)

    # --- basic column checks ---
    missing = [col for col in [AREA_COL, YEAR_COL, PRICE_COL] if col not in df.columns]
    if DEMAND_COL is not None and DEMAND_COL not in df.columns:
        missing.append(DEMAND_COL)

    if missing:
        return JsonResponse(
            {'error': f"Configured columns not found in Excel: {', '.join(missing)}"},
            status=500
        )

    # --- filter rows for this area ---
    area_mask = df[AREA_COL].astype(str).str.contains(area, case=False, na=False)
    area_df = df[area_mask].copy()

    if area_df.empty:
        return JsonResponse({'error': f'No data found for area: {area}'}, status=404)

    # --- sort by year ---
    area_df = area_df.sort_values(by=YEAR_COL)

    # --- numeric conversions ---
    price_series = pd.to_numeric(area_df[PRICE_COL], errors='coerce')
    avg_price = float(price_series.mean(skipna=True))
    min_price = float(price_series.min(skipna=True))
    max_price = float(price_series.max(skipna=True))

    avg_demand = None
    if DEMAND_COL is not None:
        demand_series = pd.to_numeric(area_df[DEMAND_COL], errors='coerce')
        if demand_series.notna().any():
            avg_demand = float(demand_series.mean(skipna=True))

    years = list(area_df[YEAR_COL])
    first_year = _safe(years[0])
    last_year = _safe(years[-1])

    # --- summary text ---
    summary_parts = [
        f"For {area}, we have data from {first_year} to {last_year}.",
        f"The average price is about {avg_price:.2f}, with a minimum of {min_price:.2f} "
        f"and a maximum of {max_price:.2f}."
    ]
    if avg_demand is not None:
        summary_parts.append(
            f"Average supplied carpet area (as a proxy for demand) is roughly {avg_demand:.2f} sqft."
        )

    summary = " ".join(summary_parts)

    # --- chart data: all values serialisation-safe ---
    chart_data = [
        {
            "year":   _safe(row[YEAR_COL]),
            "price":  _safe(row[PRICE_COL]),
            "demand": _safe(row[DEMAND_COL]) if DEMAND_COL is not None else None,
        }
        for _, row in area_df.iterrows()
    ]

    # --- table data: full rows, all values safe ---
    table_data = [
        {k: _safe(v) for k, v in record.items()}
        for record in area_df.to_dict(orient='records')
    ]

    response = {
        "area":      area,
        "query":     query,
        "summary":   summary,
        "chartData": chart_data,
        "tableData": table_data,
    }
    return JsonResponse(response, safe=False)
