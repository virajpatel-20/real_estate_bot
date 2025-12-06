from django.shortcuts import render

import json
import os
import re

import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

# ---- 1. Load Excel once ----

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
DEMAND_COL = "total carpet area supplied (sqft)"   # use None if you don't want demand

print("Excel columns:", list(df.columns))
print("AREA_COL  =", AREA_COL)
print("YEAR_COL  =", YEAR_COL)
print("PRICE_COL =", PRICE_COL)
print("DEMAND_COL =", DEMAND_COL)


def get_area_from_query(query: str):
    """
    Very simple extraction: check which area name appears inside the query.
    """
    if AREA_COL not in df.columns:
        return None

    areas = df[AREA_COL].dropna().astype(str).unique()
    q = query.lower()

    # 1) If the FULL area string appears in the query (rare but keep it)
    for area in areas:
        if str(area).lower() in q:
            return str(area)

    # 2) Fallback: last word (e.g. 'Analyze Wakad' -> 'Wakad')
    tokens = re.findall(r'[A-Za-z]+', query)
    if tokens:
        return tokens[-1]

    return None


@csrf_exempt
@require_POST
def analyze_area(request):
    # --- parse JSON body ---
    try:
        body = json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    query = body.get('query', '') or ''
    manual_area = body.get('area')  # optional field from frontend

    # --- choose area ---
    area = manual_area or get_area_from_query(query)
    if not area:
        return JsonResponse({'error': 'Could not detect area from query'}, status=400)

    # --- basic column checks ---
    missing = []
    for col in [AREA_COL, YEAR_COL, PRICE_COL]:
        if col not in df.columns:
            missing.append(col)

    if DEMAND_COL is not None and DEMAND_COL not in df.columns:
        missing.append(DEMAND_COL)

    if missing:
        return JsonResponse(
            {'error': f"Configured columns not found in Excel: {', '.join(missing)}"},
            status=500
        )

    # --- filter rows for this area ---
    # use 'contains' so 'Wakad' matches 'Wakad – Hinjewadi', etc.
    area_mask = df[AREA_COL].astype(str).str.contains(area, case=False, na=False)
    area_df = df[area_mask].copy()

    if area_df.empty:
        return JsonResponse({'error': f'No data found for area: {area}'}, status=404)

    # --- sort by year ---
    area_df = area_df.sort_values(by=YEAR_COL)

    # --- numeric conversions (safer) ---
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
    first_year = years[0]
    last_year = years[-1]

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

    # --- chart data: {year, price, demand} ---
    chart_data = []
    for _, row in area_df.iterrows():
        chart_data.append({
            "year": row[YEAR_COL],
            "price": row[PRICE_COL],
            "demand": row[DEMAND_COL] if DEMAND_COL is not None else None,
        })

    # --- table data: full rows ---
    table_data = area_df.to_dict(orient='records')

    response = {
        "area": area,
        "query": query,
        "summary": summary,
        "chartData": chart_data,
        "tableData": table_data,
    }
    return JsonResponse(response, safe=False)
