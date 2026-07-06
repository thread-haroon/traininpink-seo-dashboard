"""
Daily GSC fetch - writes to 4 tables for accuracy + breakdowns:
  1. gsc_data (full dimensions - for queries/pages/countries)
  2. gsc_totals (daily totals - matches GSC UI exactly)
  3. gsc_by_device (date+device only - matches GSC UI device tab)
  4. gsc_by_country (date+country only - matches GSC UI countries tab)  ← NEW
"""

import json
import logging
from datetime import datetime, timedelta

import functions_framework
from google.cloud import bigquery, secretmanager
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

PROJECT_ID = "seo-and-aso-dashboard"
DATASET_ID = "seo_data"
SITE_URL = "https://www.traininpink.net/"
SECRET_NAME = "gsc-refresh-token"
GSC_API_SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]
DAYS_TO_FETCH = 14  # Re-fetch last 14 days each run (handles GSC's data delay)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_oauth_credentials_from_secret():
    secret_client = secretmanager.SecretManagerServiceClient()
    secret_path = f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}/versions/latest"
    response = secret_client.access_secret_version(request={"name": secret_path})
    token_data = json.loads(response.payload.data.decode("UTF-8"))
    return Credentials(
        token=None,
        refresh_token=token_data["refresh_token"],
        token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=token_data["client_id"],
        client_secret=token_data["client_secret"],
        scopes=token_data.get("scopes", GSC_API_SCOPES),
    )


# ─── FETCH 1: Full dimensional data ───
def fetch_gsc_full(service, site_url, start_date, end_date):
    request_body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["date", "query", "page", "country", "device"],
        "type": "web",
        "rowLimit": 25000,
        "startRow": 0,
    }
    all_rows = []
    while True:
        response = service.searchanalytics().query(
            siteUrl=site_url, body=request_body
        ).execute()
        rows = response.get("rows", [])
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < 25000:
            break
        request_body["startRow"] += 25000
    return all_rows


def transform_full_rows(rows, site_url):
    transformed = []
    for row in rows:
        keys = row.get("keys", [])
        if len(keys) < 5:
            continue
        transformed.append({
            "date": keys[0],
            "site_url": site_url,
            "query": keys[1],
            "page": keys[2],
            "country": keys[3],
            "device": keys[4],
            "clicks": int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "ctr": float(row.get("ctr", 0.0)),
            "position": float(row.get("position", 0.0)),
        })
    return transformed


# ─── FETCH 2: Daily totals (no dimensions) ───
def fetch_gsc_totals(service, site_url, start_date, end_date):
    request_body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["date"],
        "type": "web",
        "rowLimit": 25000,
    }
    response = service.searchanalytics().query(
        siteUrl=site_url, body=request_body
    ).execute()
    return response.get("rows", [])


def transform_totals_rows(rows, site_url):
    transformed = []
    for row in rows:
        keys = row.get("keys", [])
        if len(keys) < 1:
            continue
        transformed.append({
            "date": keys[0],
            "site_url": site_url,
            "search_type": "web",
            "clicks": int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "ctr": float(row.get("ctr", 0.0)),
            "position": float(row.get("position", 0.0)),
        })
    return transformed


# ─── FETCH 3: Device breakdown ───
def fetch_gsc_device(service, site_url, start_date, end_date):
    request_body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["date", "device"],
        "type": "web",
        "rowLimit": 25000,
    }
    response = service.searchanalytics().query(
        siteUrl=site_url, body=request_body
    ).execute()
    return response.get("rows", [])


def transform_device_rows(rows, site_url):
    transformed = []
    for row in rows:
        keys = row.get("keys", [])
        if len(keys) < 2:
            continue
        transformed.append({
            "date": keys[0],
            "site_url": site_url,
            "device": keys[1],
            "search_type": "web",
            "clicks": int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "ctr": float(row.get("ctr", 0.0)),
            "position": float(row.get("position", 0.0)),
        })
    return transformed


# ─── FETCH 4: Country breakdown (NEW - accurate country totals) ───
def fetch_gsc_country(service, site_url, start_date, end_date):
    request_body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": ["date", "country"],
        "type": "web",
        "rowLimit": 25000,
        "startRow": 0,
    }
    all_rows = []
    while True:
        response = service.searchanalytics().query(
            siteUrl=site_url, body=request_body
        ).execute()
        rows = response.get("rows", [])
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < 25000:
            break
        request_body["startRow"] += 25000
    return all_rows


def transform_country_rows(rows, site_url):
    transformed = []
    for row in rows:
        keys = row.get("keys", [])
        if len(keys) < 2:
            continue
        transformed.append({
            "date": keys[0],
            "site_url": site_url,
            "country": keys[1],
            "search_type": "web",
            "clicks": int(row.get("clicks", 0)),
            "impressions": int(row.get("impressions", 0)),
            "ctr": float(row.get("ctr", 0.0)),
            "position": float(row.get("position", 0.0)),
        })
    return transformed


# ─── Schemas ───
def get_full_schema():
    return [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("site_url", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("query", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("page", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("country", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("device", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("clicks", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("impressions", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("ctr", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("position", "FLOAT64", mode="NULLABLE"),
    ]


def get_totals_schema():
    return [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("site_url", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("search_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("clicks", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("impressions", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("ctr", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("position", "FLOAT64", mode="NULLABLE"),
    ]


def get_device_schema():
    return [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("site_url", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("device", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("search_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("clicks", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("impressions", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("ctr", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("position", "FLOAT64", mode="NULLABLE"),
    ]


def get_country_schema():
    """NEW: Schema for gsc_by_country table."""
    return [
        bigquery.SchemaField("date", "DATE", mode="REQUIRED"),
        bigquery.SchemaField("site_url", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("country", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("search_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("clicks", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("impressions", "INT64", mode="REQUIRED"),
        bigquery.SchemaField("ctr", "FLOAT64", mode="NULLABLE"),
        bigquery.SchemaField("position", "FLOAT64", mode="NULLABLE"),
    ]


def delete_existing_data(client, table_id, start_date, end_date, site_url):
    """Delete existing data for the date range to prevent duplicates on re-fetch."""
    query = f"""
    DELETE FROM `{PROJECT_ID}.{DATASET_ID}.{table_id}`
    WHERE date BETWEEN @start_date AND @end_date
      AND site_url = @site_url
    """
    job_config = bigquery.QueryJobConfig(query_parameters=[
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        bigquery.ScalarQueryParameter("site_url", "STRING", site_url),
    ])
    client.query(query, job_config=job_config).result()


def write_to_bigquery(client, table_id, rows, schema):
    if not rows:
        return 0
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_id}"
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )
    job = client.load_table_from_json(rows, table_ref, job_config=job_config)
    job.result()
    return len(rows)


@functions_framework.http
def fetch_gsc_data(request):
    """Main entry point - fetches GSC data into 4 tables."""
    try:
        # Optional: allow days_back override via POST body
        days_back = DAYS_TO_FETCH
        try:
            request_json = request.get_json(silent=True) or {}
            days_back = int(request_json.get("days_back", DAYS_TO_FETCH))
        except Exception:
            pass

        creds = get_oauth_credentials_from_secret()
        service = build("searchconsole", "v1", credentials=creds)
        client = bigquery.Client(project=PROJECT_ID)

        # Support explicit start_date/end_date for backfill
        request_json = request.get_json(silent=True) or {}
        if request_json.get("start_date") and request_json.get("end_date"):
            start_date = datetime.strptime(request_json["start_date"], "%Y-%m-%d")
            end_date = datetime.strptime(request_json["end_date"], "%Y-%m-%d")
        else:
            end_date = datetime.utcnow() - timedelta(days=2)
            start_date = end_date - timedelta(days=days_back - 1)

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        logger.info(f"Fetching GSC data: {start_str} to {end_str}")

        # Delete existing data for this range (prevents duplicates)
        # Note: gsc_by_country added to the list
        for table_id in ["gsc_data", "gsc_totals", "gsc_by_device", "gsc_by_country"]:
            try:
                delete_existing_data(client, table_id, start_date.date(), end_date.date(), SITE_URL)
            except Exception as e:
                logger.warning(f"Could not delete from {table_id}: {e}")

        # Fetch and write to each table
        # 1. Full dimensional data
        full_rows = fetch_gsc_full(service, SITE_URL, start_str, end_str)
        full_transformed = transform_full_rows(full_rows, SITE_URL)
        full_inserted = write_to_bigquery(client, "gsc_data", full_transformed, get_full_schema())

        # 2. Daily totals
        totals_rows = fetch_gsc_totals(service, SITE_URL, start_str, end_str)
        totals_transformed = transform_totals_rows(totals_rows, SITE_URL)
        totals_inserted = write_to_bigquery(client, "gsc_totals", totals_transformed, get_totals_schema())

        # 3. Device breakdown
        device_rows = fetch_gsc_device(service, SITE_URL, start_str, end_str)
        device_transformed = transform_device_rows(device_rows, SITE_URL)
        device_inserted = write_to_bigquery(client, "gsc_by_device", device_transformed, get_device_schema())

        # 4. Country breakdown (NEW - matches GSC UI exactly)
        country_rows = fetch_gsc_country(service, SITE_URL, start_str, end_str)
        country_transformed = transform_country_rows(country_rows, SITE_URL)
        country_inserted = write_to_bigquery(client, "gsc_by_country", country_transformed, get_country_schema())

        return {
            "status": "success",
            "site_url": SITE_URL,
            "date_range": f"{start_str} to {end_str}",
            "gsc_data_rows": full_inserted,
            "gsc_totals_rows": totals_inserted,
            "gsc_by_device_rows": device_inserted,
            "gsc_by_country_rows": country_inserted,
        }, 200

    except Exception as e:
        logger.exception("Error during GSC fetch")
        return {"status": "error", "message": str(e)}, 500
