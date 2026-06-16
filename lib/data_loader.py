"""Data loader: queries BigQuery for GSC and Bing data.
Uses gsc_totals for accurate KPIs that match GSC UI exactly,
and gsc_data for detailed breakdowns (queries, pages, etc.)."""

import os
from datetime import date

import pandas as pd
import streamlit as st
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = "seo-and-aso-dashboard"
DATASET_ID = "seo_data"


@st.cache_resource
def get_bigquery_client():
    """Create a BigQuery client using service account credentials."""
    key_path = os.path.join(os.path.dirname(__file__), "..", "dashboard-reader-key.json")
    if os.path.exists(key_path):
        credentials = service_account.Credentials.from_service_account_file(key_path)
        return bigquery.Client(credentials=credentials, project=PROJECT_ID)

    try:
        if "gcp_service_account" in st.secrets:
            credentials = service_account.Credentials.from_service_account_info(
                st.secrets["gcp_service_account"]
            )
            return bigquery.Client(credentials=credentials, project=PROJECT_ID)
    except Exception:
        pass

    return bigquery.Client(project=PROJECT_ID)


def _bing_daily_traffic_filter():
    """Bing daily traffic rows have query=NULL AND page=NULL."""
    return "query IS NULL AND page IS NULL"


def _build_filter_clause(country, device, table=None):
    """Build SQL WHERE clauses for optional filters."""
    clauses = []
    params = []
    if country and country != "All":
        clauses.append("country = @country")
        params.append(bigquery.ScalarQueryParameter("country", "STRING", country))
    if device and device != "All":
        clauses.append("device = @device")
        params.append(bigquery.ScalarQueryParameter("device", "STRING", device))
    return (" AND ".join(clauses) if clauses else ""), params


@st.cache_data(ttl=600)
def get_gsc_totals_kpis(start_date, end_date, site_url=None):
    """Get accurate GSC KPIs from gsc_totals table - matches GSC UI exactly.
    Note: This table has NO dimensions (no country/device filtering).
    Use this for top-level KPI cards. Use get_aggregate_kpis for filtered/breakdowns."""
    client = get_bigquery_client()
    params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ]
    site_filter = ""
    if site_url:
        site_filter = "AND site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))

    query = """
    SELECT
      COALESCE(SUM(clicks), 0) AS clicks,
      COALESCE(SUM(impressions), 0) AS impressions,
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
      SAFE_DIVIDE(SUM(position * impressions), SUM(impressions)) AS position
    FROM `{p}.{d}.gsc_totals`
    WHERE date BETWEEN @start_date AND @end_date
    {site_filter}
    """.format(p=PROJECT_ID, d=DATASET_ID, site_filter=site_filter)

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    df = client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)

    if df.empty:
        return {"clicks": 0, "impressions": 0, "ctr": 0.0, "position": 0.0}
    row = df.iloc[0]
    return {
        "clicks": int(row["clicks"]) if pd.notna(row["clicks"]) else 0,
        "impressions": int(row["impressions"]) if pd.notna(row["impressions"]) else 0,
        "ctr": float(row["ctr"]) if pd.notna(row["ctr"]) else 0.0,
        "position": float(row["position"]) if pd.notna(row["position"]) else 0.0,
    }


@st.cache_data(ttl=600)
def get_gsc_totals_timeseries(start_date, end_date, site_url=None):
    """Get accurate daily timeseries from gsc_totals - matches GSC UI."""
    client = get_bigquery_client()
    params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ]
    site_filter = ""
    if site_url:
        site_filter = "AND site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))

    query = """
    SELECT
      date,
      SUM(clicks) AS clicks,
      SUM(impressions) AS impressions,
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
      SAFE_DIVIDE(SUM(position * impressions), SUM(impressions)) AS position
    FROM `{p}.{d}.gsc_totals`
    WHERE date BETWEEN @start_date AND @end_date
    {site_filter}
    GROUP BY date
    ORDER BY date
    """.format(p=PROJECT_ID, d=DATASET_ID, site_filter=site_filter)

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    df = client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=600)
def get_aggregate_kpis(table, start_date, end_date, country=None, device=None, site_url=None):
    """Get aggregate KPIs for the date range (with optional country/device filters).
    For bing_data: only counts daily traffic rows.
    For gsc_data: dimensional data — totals will be lower than GSC UI by design."""
    client = get_bigquery_client()
    extra_filter, params = _build_filter_clause(country, device, table)
    if site_url:
        extra_filter = (extra_filter + " AND " if extra_filter else "") + "site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))

    if table == "bing_data":
        bing_filter = _bing_daily_traffic_filter()
        extra_filter = (extra_filter + " AND " if extra_filter else "") + bing_filter

    where_extra = "AND " + extra_filter if extra_filter else ""

    query = """
    SELECT
      COALESCE(SUM(clicks), 0) AS clicks,
      COALESCE(SUM(impressions), 0) AS impressions,
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
      SAFE_DIVIDE(SUM(position * impressions), SUM(impressions)) AS position
    FROM `{project}.{dataset}.{table}`
    WHERE date BETWEEN @start_date AND @end_date
    {where_extra}
    """.format(project=PROJECT_ID, dataset=DATASET_ID, table=table, where_extra=where_extra)

    params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ] + params
    job_config = bigquery.QueryJobConfig(query_parameters=params)
    df = client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)

    if df.empty:
        return {"clicks": 0, "impressions": 0, "ctr": 0.0, "position": 0.0}
    row = df.iloc[0]
    return {
        "clicks": int(row["clicks"]) if pd.notna(row["clicks"]) else 0,
        "impressions": int(row["impressions"]) if pd.notna(row["impressions"]) else 0,
        "ctr": float(row["ctr"]) if pd.notna(row["ctr"]) else 0.0,
        "position": float(row["position"]) if pd.notna(row["position"]) else 0.0,
    }


@st.cache_data(ttl=600)
def get_daily_timeseries(table, start_date, end_date, country=None, device=None, site_url=None):
    """Get daily aggregated metrics for a line chart."""
    client = get_bigquery_client()
    extra_filter, params = _build_filter_clause(country, device, table)
    if site_url:
        extra_filter = (extra_filter + " AND " if extra_filter else "") + "site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))

    if table == "bing_data":
        bing_filter = _bing_daily_traffic_filter()
        extra_filter = (extra_filter + " AND " if extra_filter else "") + bing_filter

    where_extra = "AND " + extra_filter if extra_filter else ""

    query = """
    SELECT
      date,
      SUM(clicks) AS clicks,
      SUM(impressions) AS impressions,
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
      SAFE_DIVIDE(SUM(position * impressions), SUM(impressions)) AS position
    FROM `{project}.{dataset}.{table}`
    WHERE date BETWEEN @start_date AND @end_date
    {where_extra}
    GROUP BY date
    ORDER BY date
    """.format(project=PROJECT_ID, dataset=DATASET_ID, table=table, where_extra=where_extra)

    params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ] + params
    job_config = bigquery.QueryJobConfig(query_parameters=params)
    df = client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=600)
def get_weekly_timeseries(table, start_date, end_date, country=None, device=None, site_url=None):
    """Get WEEKLY aggregated metrics."""
    client = get_bigquery_client()
    extra_filter, params = _build_filter_clause(country, device, table)
    if site_url:
        extra_filter = (extra_filter + " AND " if extra_filter else "") + "site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))

    if table == "bing_data":
        bing_filter = _bing_daily_traffic_filter()
        extra_filter = (extra_filter + " AND " if extra_filter else "") + bing_filter

    where_extra = "AND " + extra_filter if extra_filter else ""

    query = """
    SELECT
      DATE_TRUNC(date, WEEK(MONDAY)) AS date,
      SUM(clicks) AS clicks,
      SUM(impressions) AS impressions,
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
      SAFE_DIVIDE(SUM(position * impressions), SUM(impressions)) AS position
    FROM `{project}.{dataset}.{table}`
    WHERE date BETWEEN @start_date AND @end_date
    {where_extra}
    GROUP BY 1
    ORDER BY 1
    """.format(project=PROJECT_ID, dataset=DATASET_ID, table=table, where_extra=where_extra)

    params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ] + params
    job_config = bigquery.QueryJobConfig(query_parameters=params)
    df = client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=600)
def get_top_dimension(table, dimension, start_date, end_date, limit=10, country=None, device=None, site_url=None):
    """Get top N values for a given dimension."""
    if dimension not in ("query", "page", "country", "device"):
        raise ValueError("Invalid dimension: " + dimension)
    client = get_bigquery_client()
    extra_filter, params = _build_filter_clause(country, device, table)
    if site_url:
        extra_filter = (extra_filter + " AND " if extra_filter else "") + "site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))

    where_extra = "AND " + extra_filter if extra_filter else ""

    query = """
    SELECT
      {dim} AS name,
      SUM(clicks) AS clicks,
      SUM(impressions) AS impressions,
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
      SAFE_DIVIDE(SUM(position * impressions), SUM(impressions)) AS position
    FROM `{project}.{dataset}.{table}`
    WHERE date BETWEEN @start_date AND @end_date
      AND {dim} IS NOT NULL
      AND {dim} != ''
    {where_extra}
    GROUP BY {dim}
    ORDER BY clicks DESC
    LIMIT {limit}
    """.format(project=PROJECT_ID, dataset=DATASET_ID, table=table, dim=dimension, where_extra=where_extra, limit=limit)

    params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ] + params
    job_config = bigquery.QueryJobConfig(query_parameters=params)
    return client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)


@st.cache_data(ttl=3600)
def get_available_sites(table):
    """Get list of unique site URLs in the table."""
    client = get_bigquery_client()
    query = "SELECT DISTINCT site_url FROM `" + PROJECT_ID + "." + DATASET_ID + "." + table + "` ORDER BY site_url"
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    return df["site_url"].tolist() if not df.empty else []


@st.cache_data(ttl=3600)
def get_available_countries(table, site_url=None):
    """Get list of unique countries with traffic, ordered by clicks."""
    client = get_bigquery_client()
    where = "WHERE country IS NOT NULL AND country != ''"
    params = []
    if site_url:
        where += " AND site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))
    query = "SELECT country, SUM(clicks) AS total_clicks FROM `" + PROJECT_ID + "." + DATASET_ID + "." + table + "` " + where + " GROUP BY country ORDER BY total_clicks DESC"
    job_config = bigquery.QueryJobConfig(query_parameters=params)
    df = client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)
    return df["country"].tolist() if not df.empty else []


@st.cache_data(ttl=3600)
def get_available_devices(table, site_url=None):
    """Get list of unique devices."""
    client = get_bigquery_client()
    where = "WHERE device IS NOT NULL AND device != ''"
    params = []
    if site_url:
        where += " AND site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))
    query = "SELECT DISTINCT device FROM `" + PROJECT_ID + "." + DATASET_ID + "." + table + "` " + where + " ORDER BY device"
    job_config = bigquery.QueryJobConfig(query_parameters=params)
    df = client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)
    return df["device"].tolist() if not df.empty else []


@st.cache_data(ttl=3600)
def get_data_date_range(table):
    """Get min and max dates available in the table."""
    client = get_bigquery_client()
    query = "SELECT MIN(date) AS min_date, MAX(date) AS max_date FROM `" + PROJECT_ID + "." + DATASET_ID + "." + table + "`"
    df = client.query(query).to_dataframe(create_bqstorage_client=False)
    if df.empty or pd.isna(df.iloc[0]["min_date"]):
        return None, None
    return df.iloc[0]["min_date"], df.iloc[0]["max_date"]

@st.cache_data(ttl=600)
def get_gsc_device_breakdown(start_date, end_date, site_url=None):
    """Get accurate device breakdown from gsc_by_device table - matches GSC UI exactly."""
    client = get_bigquery_client()
    params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ]
    site_filter = ""
    if site_url:
        site_filter = "AND site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))

    query = """
    SELECT
      device AS name,
      SUM(clicks) AS clicks,
      SUM(impressions) AS impressions,
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
      SAFE_DIVIDE(SUM(position * impressions), SUM(impressions)) AS position
    FROM `{p}.{d}.gsc_by_device`
    WHERE date BETWEEN @start_date AND @end_date
    {site_filter}
    GROUP BY device
    ORDER BY clicks DESC
    """.format(p=PROJECT_ID, d=DATASET_ID, site_filter=site_filter)

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    return client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)


@st.cache_data(ttl=600)
def get_gsc_device_kpis(start_date, end_date, device, site_url=None):
    """Get KPIs filtered by device - uses gsc_by_device for accuracy."""
    client = get_bigquery_client()
    params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
        bigquery.ScalarQueryParameter("device", "STRING", device),
    ]
    site_filter = ""
    if site_url:
        site_filter = "AND site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))

    query = """
    SELECT
      COALESCE(SUM(clicks), 0) AS clicks,
      COALESCE(SUM(impressions), 0) AS impressions,
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
      SAFE_DIVIDE(SUM(position * impressions), SUM(impressions)) AS position
    FROM `{p}.{d}.gsc_by_device`
    WHERE date BETWEEN @start_date AND @end_date
    AND device = @device
    {site_filter}
    """.format(p=PROJECT_ID, d=DATASET_ID, site_filter=site_filter)

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    df = client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)

    if df.empty:
        return {"clicks": 0, "impressions": 0, "ctr": 0.0, "position": 0.0}
    row = df.iloc[0]
    return {
        "clicks": int(row["clicks"]) if pd.notna(row["clicks"]) else 0,
        "impressions": int(row["impressions"]) if pd.notna(row["impressions"]) else 0,
        "ctr": float(row["ctr"]) if pd.notna(row["ctr"]) else 0.0,
        "position": float(row["position"]) if pd.notna(row["position"]) else 0.0,
    }

@st.cache_data(ttl=600)
def get_bing_totals_kpis(start_date, end_date, site_url=None):
    """Get accurate Bing KPIs from bing_totals table - matches Bing UI."""
    client = get_bigquery_client()
    params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ]
    site_filter = ""
    if site_url:
        site_filter = "AND site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))

    query = """
    SELECT
      COALESCE(SUM(clicks), 0) AS clicks,
      COALESCE(SUM(impressions), 0) AS impressions,
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
      SAFE_DIVIDE(SUM(position * impressions), SUM(impressions)) AS position
    FROM `{p}.{d}.bing_totals`
    WHERE date BETWEEN @start_date AND @end_date
    {site_filter}
    """.format(p=PROJECT_ID, d=DATASET_ID, site_filter=site_filter)

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    df = client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)

    if df.empty:
        return {"clicks": 0, "impressions": 0, "ctr": 0.0, "position": 0.0}
    row = df.iloc[0]
    return {
        "clicks": int(row["clicks"]) if pd.notna(row["clicks"]) else 0,
        "impressions": int(row["impressions"]) if pd.notna(row["impressions"]) else 0,
        "ctr": float(row["ctr"]) if pd.notna(row["ctr"]) else 0.0,
        "position": float(row["position"]) if pd.notna(row["position"]) else 0.0,
    }


@st.cache_data(ttl=600)
def get_bing_totals_timeseries(start_date, end_date, site_url=None):
    """Daily timeseries from bing_totals."""
    client = get_bigquery_client()
    params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ]
    site_filter = ""
    if site_url:
        site_filter = "AND site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))

    query = """
    SELECT
      date,
      SUM(clicks) AS clicks,
      SUM(impressions) AS impressions,
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
      SAFE_DIVIDE(SUM(position * impressions), SUM(impressions)) AS position
    FROM `{p}.{d}.bing_totals`
    WHERE date BETWEEN @start_date AND @end_date
    {site_filter}
    GROUP BY date
    ORDER BY date
    """.format(p=PROJECT_ID, d=DATASET_ID, site_filter=site_filter)

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    df = client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df


@st.cache_data(ttl=600)
def get_bing_top_keywords(start_date, end_date, limit=10, site_url=None):
    """Get top Bing keywords from bing_data (uses latest snapshot data).
    Note: Bing's keyword API returns rolling snapshots, not daily data."""
    client = get_bigquery_client()
    params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ]
    site_filter = ""
    if site_url:
        site_filter = "AND site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))

    query = """
    SELECT
      query AS name,
      SUM(clicks) AS clicks,
      SUM(impressions) AS impressions,
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
      SAFE_DIVIDE(SUM(position * impressions), SUM(impressions)) AS position
    FROM `{p}.{d}.bing_data`
    WHERE date BETWEEN @start_date AND @end_date
      AND query IS NOT NULL
      AND query != ''
    {site_filter}
    GROUP BY query
    ORDER BY clicks DESC
    LIMIT {limit}
    """.format(p=PROJECT_ID, d=DATASET_ID, site_filter=site_filter, limit=limit)

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    return client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)


@st.cache_data(ttl=600)
def get_bing_top_pages(start_date, end_date, limit=10, site_url=None):
    """Get top Bing pages from bing_data."""
    client = get_bigquery_client()
    params = [
        bigquery.ScalarQueryParameter("start_date", "DATE", start_date),
        bigquery.ScalarQueryParameter("end_date", "DATE", end_date),
    ]
    site_filter = ""
    if site_url:
        site_filter = "AND site_url = @site_url"
        params.append(bigquery.ScalarQueryParameter("site_url", "STRING", site_url))

    query = """
    SELECT
      page AS name,
      SUM(clicks) AS clicks,
      SUM(impressions) AS impressions,
      SAFE_DIVIDE(SUM(clicks), SUM(impressions)) AS ctr,
      SAFE_DIVIDE(SUM(position * impressions), SUM(impressions)) AS position
    FROM `{p}.{d}.bing_data`
    WHERE date BETWEEN @start_date AND @end_date
      AND page IS NOT NULL
      AND page != ''
    {site_filter}
    GROUP BY page
    ORDER BY clicks DESC
    LIMIT {limit}
    """.format(p=PROJECT_ID, d=DATASET_ID, site_filter=site_filter, limit=limit)

    job_config = bigquery.QueryJobConfig(query_parameters=params)
    return client.query(query, job_config=job_config).to_dataframe(create_bqstorage_client=False)



@st.cache_data(ttl=3600)
def load_ga4_ai_data(start_date=None, end_date=None):
    """Load GA4 AI referral data from BigQuery."""
    client = get_bigquery_client()
    
    where_clause = ""
    if start_date and end_date:
        where_clause = f"WHERE date BETWEEN '{start_date}' AND '{end_date}'"
    
    query = f"""
    SELECT
        date,
        source,
        medium,
        ai_platform,
        sessions,
        engaged_sessions,
        total_users,
        new_users,
        engagement_rate,
        avg_engagement_time,
        events_per_session,
        page_path
    FROM `seo-and-aso-dashboard.seo_data.ga4_ai_referrals`
    {where_clause}
    ORDER BY date DESC
    """
    
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data(ttl=3600)
def load_ga4_ai_summary():
    """Load AI traffic summary by platform."""
    client = get_bigquery_client()
    
    query = """
    SELECT
        ai_platform,
        COUNT(*) as records,
        SUM(sessions) as total_sessions,
        SUM(engaged_sessions) as total_engaged,
        SUM(total_users) as total_users,
        AVG(engagement_rate) as avg_engagement_rate,
        AVG(avg_engagement_time) as avg_session_duration,
        MIN(date) as earliest_date,
        MAX(date) as latest_date
    FROM `seo-and-aso-dashboard.seo_data.ga4_ai_referrals`
    GROUP BY ai_platform
    ORDER BY total_sessions DESC
    """
    
    return client.query(query).to_dataframe()


@st.cache_data(ttl=3600)
def load_ga4_top_pages(limit=20):
    """Load top pages getting AI traffic. Uses page-level data (total_users)."""
    client = get_bigquery_client()
    
    query = f"""
    SELECT
        page_path,
        ai_platform,
        SUM(total_users) as total_sessions,
        SUM(total_users) as total_users,
        AVG(engagement_rate) as avg_engagement
    FROM `seo-and-aso-dashboard.seo_data.ga4_ai_referrals`
    WHERE page_path IS NOT NULL 
      AND page_path != \'\'
      AND total_users > 0
    GROUP BY page_path, ai_platform
    ORDER BY total_users DESC
    LIMIT {limit}
    """
    
    return client.query(query).to_dataframe()




# ============================================================
# APP DATA LOADERS v2 - works with strict/direct/wider columns
# ============================================================

@st.cache_data(ttl=3600)
def load_app_metrics(start_date=None, end_date=None, platform=None, organic_only=False):
    """Load daily app metrics. Filtering happens in dashboard code, not here.
    organic_only param kept for backward compat but ignored - we load all data."""
    client = get_bigquery_client()
    
    where = ["1=1"]
    if start_date and end_date:
        where.append(f"date BETWEEN '{start_date}' AND '{end_date}'")
    if platform and platform != 'All':
        where.append(f"platform = '{platform}'")
    
    query = f"""
    SELECT 
        date, platform, source, medium,
        is_organic_strict, is_direct, is_organic_wider,
        active_users, new_users, total_users,
        sessions, engaged_sessions, first_opens,
        engagement_rate, avg_session_duration
    FROM `seo-and-aso-dashboard.seo_data.app_daily_metrics`
    WHERE {' AND '.join(where)}
    ORDER BY date DESC
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data(ttl=3600)
def load_app_revenue(start_date=None, end_date=None, platform=None, country=None, organic_only=False):
    """Load daily app revenue."""
    client = get_bigquery_client()
    
    where = ["1=1"]
    if start_date and end_date:
        where.append(f"date BETWEEN '{start_date}' AND '{end_date}'")
    if platform and platform != 'All':
        where.append(f"platform = '{platform}'")
    if country and country != 'All':
        where.append(f"country = '{country}'")
    
    query = f"""
    SELECT 
        date, platform, source, medium, country,
        is_organic_strict, is_direct, is_organic_wider,
        total_revenue, purchase_revenue, transactions,
        paying_users, avg_purchase_value
    FROM `seo-and-aso-dashboard.seo_data.app_daily_revenue`
    WHERE {' AND '.join(where)}
    ORDER BY date DESC
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data(ttl=3600)
def load_app_countries(start_date=None, end_date=None, platform=None, organic_only=False):
    """Load country-level data."""
    client = get_bigquery_client()
    
    where = ["1=1"]
    if start_date and end_date:
        where.append(f"date BETWEEN '{start_date}' AND '{end_date}'")
    if platform and platform != 'All':
        where.append(f"platform = '{platform}'")
    
    query = f"""
    SELECT 
        date, country, platform,
        is_organic_strict, is_direct, is_organic_wider,
        active_users, new_users, sessions,
        total_revenue, transactions
    FROM `seo-and-aso-dashboard.seo_data.app_daily_countries`
    WHERE {' AND '.join(where)}
    ORDER BY date DESC
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data(ttl=3600)
def get_app_country_list():
    """Get unique countries for filter dropdown."""
    client = get_bigquery_client()
    query = """
    SELECT DISTINCT country
    FROM `seo-and-aso-dashboard.seo_data.app_daily_countries`
    WHERE country IS NOT NULL AND country != '(unknown)'
    ORDER BY country
    """
    df = client.query(query).to_dataframe()
    return df['country'].tolist()


# ============================================================
# WEBSITE DATA LOADERS (traininpink.net + app.traininpink.net + www.)
# ============================================================

@st.cache_data(ttl=3600)
def load_website_metrics(start_date=None, end_date=None, hostname=None):
    """Load daily website metrics. No DB-level organic filter (filter in dashboard)."""
    client = get_bigquery_client()
    where = ["1=1"]
    if start_date and end_date:
        where.append(f"date BETWEEN '{start_date}' AND '{end_date}'")
    if hostname and hostname != 'All':
        where.append(f"hostname = '{hostname}'")
    
    query = f"""
    SELECT 
        date, hostname, source, medium,
        is_organic_strict, is_direct, is_organic_wider,
        active_users, new_users, total_users,
        sessions, engaged_sessions,
        engagement_rate, avg_session_duration, user_engagement_duration
    FROM `seo-and-aso-dashboard.seo_data.website_daily_metrics`
    WHERE {' AND '.join(where)}
    ORDER BY date DESC
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data(ttl=3600)
def load_website_landing_pages(start_date=None, end_date=None):
    """Load landing page data."""
    client = get_bigquery_client()
    where = ["1=1"]
    if start_date and end_date:
        where.append(f"date BETWEEN '{start_date}' AND '{end_date}'")
    query = f"""
    SELECT 
        date, landing_page, source, medium,
        is_organic_strict, is_direct, is_organic_wider,
        sessions, active_users, engaged_sessions, bounce_rate
    FROM `seo-and-aso-dashboard.seo_data.website_daily_landing_pages`
    WHERE {' AND '.join(where)}
    ORDER BY date DESC
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data(ttl=3600)
def load_website_countries(start_date=None, end_date=None):
    """Load country data."""
    client = get_bigquery_client()
    where = ["1=1"]
    if start_date and end_date:
        where.append(f"date BETWEEN '{start_date}' AND '{end_date}'")
    query = f"""
    SELECT 
        date, country, source, medium,
        is_organic_strict, is_direct, is_organic_wider,
        active_users, new_users, sessions, engaged_sessions
    FROM `seo-and-aso-dashboard.seo_data.website_daily_countries`
    WHERE {' AND '.join(where)}
    ORDER BY date DESC
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data(ttl=3600)
def load_website_events(start_date=None, end_date=None):
    """Load event data for funnel."""
    client = get_bigquery_client()
    where = ["1=1"]
    if start_date and end_date:
        where.append(f"date BETWEEN '{start_date}' AND '{end_date}'")
    query = f"""
    SELECT 
        date, event_name, source, medium,
        is_organic_strict, is_direct, is_organic_wider,
        event_count
    FROM `seo-and-aso-dashboard.seo_data.website_daily_events`
    WHERE {' AND '.join(where)}
    ORDER BY date DESC
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data(ttl=3600)
def get_website_country_list():
    """Get unique countries for filter dropdown."""
    client = get_bigquery_client()
    query = """
    SELECT DISTINCT country
    FROM `seo-and-aso-dashboard.seo_data.website_daily_countries`
    WHERE country IS NOT NULL AND country != '(unknown)'
    ORDER BY country
    """
    df = client.query(query).to_dataframe()
    return df['country'].tolist()


@st.cache_data(ttl=3600)
def get_website_hostname_list():
    """Get unique hostnames."""
    client = get_bigquery_client()
    query = """
    SELECT DISTINCT hostname
    FROM `seo-and-aso-dashboard.seo_data.website_daily_metrics`
    WHERE hostname IS NOT NULL
    ORDER BY hostname
    """
    df = client.query(query).to_dataframe()
    return df['hostname'].tolist()

# ============================================================
# APP STORE CONNECT LOADERS (Real iOS Apple data)
# ============================================================

@st.cache_data(ttl=3600)
def load_appstore_sales(start_date=None, end_date=None, country=None):
    """Load App Store Connect sales data (real Apple data).
    Product types decoded:
       1, 1F, 3F = First-time installs (free app)
       7F = App redownloads/updates (NOT new installs)
       IAY = New subscription
       IAS = Subscription renewal
       IA1 = One-time IAP"""
    client = get_bigquery_client()
    
    where = ["1=1"]
    if start_date and end_date:
        where.append(f"date BETWEEN '{start_date}' AND '{end_date}'")
    if country and country != 'All':
        where.append(f"country_code = '{country}'")
    
    query = f"""
    SELECT 
        date, app_id, sku, units, country_code, product_type,
        developer_proceeds_usd,
        CASE 
          WHEN product_type IN ('1', '1F', '3F') AND sku = 'com.traininpink.mobile' THEN 'install'
          WHEN product_type = '7F' AND sku = 'com.traininpink.mobile' THEN 'redownload'
          WHEN product_type = 'IAY' THEN 'subscription_new'
          WHEN product_type = 'IAS' THEN 'subscription_renewal'
          WHEN product_type = 'IA1' THEN 'iap'
          ELSE 'other'
        END as event_type
    FROM `seo-and-aso-dashboard.seo_data.appstore_daily_sales`
    WHERE {' AND '.join(where)}
    ORDER BY date DESC
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data(ttl=3600)
def get_appstore_country_list():
    """Get unique iOS country codes."""
    client = get_bigquery_client()
    query = """
    SELECT DISTINCT country_code
    FROM `seo-and-aso-dashboard.seo_data.appstore_daily_sales`
    WHERE country_code IS NOT NULL AND country_code != ''
    ORDER BY country_code
    """
    df = client.query(query).to_dataframe()
    return df['country_code'].tolist()

# ============================================================
# APP STORE CONNECT LOADERS (Real iOS Apple data)
# ============================================================

@st.cache_data(ttl=3600)
def load_appstore_sales(start_date=None, end_date=None, country=None):
    """Load App Store Connect sales data (real Apple data).
    Product types decoded:
       1, 1F, 3F = First-time installs (free app)
       7F = App redownloads/updates (NOT new installs)
       IAY = New subscription
       IAS = Subscription renewal
       IA1 = One-time IAP"""
    client = get_bigquery_client()
    
    where = ["1=1"]
    if start_date and end_date:
        where.append(f"date BETWEEN '{start_date}' AND '{end_date}'")
    if country and country != 'All':
        where.append(f"country_code = '{country}'")
    
    query = f"""
    SELECT 
        date, app_id, sku, units, country_code, product_type,
        developer_proceeds_usd,
        CASE 
          WHEN product_type IN ('1', '1F', '3F') AND sku = 'com.traininpink.mobile' THEN 'install'
          WHEN product_type = '7F' AND sku = 'com.traininpink.mobile' THEN 'redownload'
          WHEN product_type = 'IAY' THEN 'subscription_new'
          WHEN product_type = 'IAS' THEN 'subscription_renewal'
          WHEN product_type = 'IA1' THEN 'iap'
          ELSE 'other'
        END as event_type
    FROM `seo-and-aso-dashboard.seo_data.appstore_daily_sales`
    WHERE {' AND '.join(where)}
    ORDER BY date DESC
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data(ttl=3600)
def get_appstore_country_list():
    """Get unique iOS country codes."""
    client = get_bigquery_client()
    query = """
    SELECT DISTINCT country_code
    FROM `seo-and-aso-dashboard.seo_data.appstore_daily_sales`
    WHERE country_code IS NOT NULL AND country_code != ''
    ORDER BY country_code
    """
    df = client.query(query).to_dataframe()
    return df['country_code'].tolist()


# ============================================================
# APPLE SUBSCRIPTION LOADERS (Real iOS subscription business data)
# ============================================================

@st.cache_data(ttl=3600)
def load_appstore_subscriptions(start_date=None, end_date=None):
    """Load Apple subscription daily snapshots (active subscriber counts).
    Each row = one subscription product per country per day with active counts."""
    client = get_bigquery_client()
    
    where = ["1=1"]
    if start_date and end_date:
        where.append(f"date BETWEEN '{start_date}' AND '{end_date}'")
    
    query = f"""
    SELECT 
        date, app_id, subscription_name, subscription_apple_id, 
        subscription_group_id, duration,
        customer_price, customer_currency, developer_proceeds, proceeds_currency,
        country_code,
        active_standard_subs, active_free_trial_subs, 
        active_pay_up_front_subs, active_pay_as_you_go_subs,
        free_promotional_subs, pay_up_front_promotional_subs, pay_as_you_go_promotional_subs,
        marketing_opt_ins, billing_retry, grace_period
    FROM `seo-and-aso-dashboard.seo_data.appstore_daily_subscriptions`
    WHERE {' AND '.join(where)}
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data(ttl=3600)
def load_appstore_sub_events(start_date=None, end_date=None):
    """Load Apple subscription events (subscribe, renew, cancel, refund)."""
    client = get_bigquery_client()
    
    where = ["1=1"]
    if start_date and end_date:
        where.append(f"date BETWEEN '{start_date}' AND '{end_date}'")
    
    query = f"""
    SELECT 
        date, app_id, event_date, event_type,
        subscription_name, subscription_apple_id, subscription_group_id,
        duration, offer_type, consecutive_paid_periods,
        cancellation_reason, days_before_canceling, country_code, quantity
    FROM `seo-and-aso-dashboard.seo_data.appstore_daily_sub_events`
    WHERE {' AND '.join(where)}
    """
    df = client.query(query).to_dataframe()
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
    return df


@st.cache_data(ttl=3600)
def get_appstore_subscription_summary(start_date=None, end_date=None):
    """Get comprehensive iOS subscription business summary - matches App Store Connect."""
    client = get_bigquery_client()
    
    where_date = ""
    if start_date and end_date:
        where_date = f"AND date BETWEEN '{start_date}' AND '{end_date}'"
    
    # Get most recent snapshot date in range
    latest_date_query = f"""
    SELECT MAX(date) as latest_date
    FROM `seo-and-aso-dashboard.seo_data.appstore_daily_subscriptions`
    WHERE 1=1 {where_date}
    """
    latest_result = client.query(latest_date_query).to_dataframe()
    if latest_result.empty or pd.isna(latest_result['latest_date'].iloc[0]):
        return None
    latest_date = latest_result['latest_date'].iloc[0]
    
    # Active subscribers + MRR snapshot
    summary_query = f"""
    WITH latest_snapshot AS (
        SELECT 
            duration,
            SUM(active_standard_subs) as paying_subs,
            SUM(active_free_trial_subs) as trial_subs,
            SUM(active_pay_up_front_subs + active_pay_as_you_go_subs) as intro_offer_subs,
            SUM(active_standard_subs * developer_proceeds) as period_revenue_eur,
            SUM(active_standard_subs * customer_price) as customer_revenue_eur
        FROM `seo-and-aso-dashboard.seo_data.appstore_daily_subscriptions`
        WHERE date = '{latest_date}'
          AND active_standard_subs > 0
        GROUP BY duration
    )
    SELECT 
        duration,
        paying_subs, trial_subs, intro_offer_subs,
        ROUND(period_revenue_eur, 2) as period_revenue_eur,
        ROUND(customer_revenue_eur, 2) as customer_revenue_eur,
        ROUND(CASE duration
            WHEN '1 Month' THEN period_revenue_eur
            WHEN '3 Months' THEN period_revenue_eur / 3
            WHEN '6 Months' THEN period_revenue_eur / 6
            WHEN '1 Year' THEN period_revenue_eur / 12
            ELSE 0
        END, 2) as monthly_recurring_revenue_eur
    FROM latest_snapshot
    ORDER BY paying_subs DESC
    """
    df = client.query(summary_query).to_dataframe()
    return df, latest_date


# ============================================================
# ANDROID PLAN BREAKDOWN LOADER
# Uses GA4 raw event export from constant-host-348313 project
# ============================================================

@st.cache_data(ttl=3600)
def load_android_organic_by_plan(start_date=None, end_date=None):
    """Get Android new ORGANIC subscribers by plan from raw GA4 events.
    
    Returns DataFrame with: plan_duration, organic_new_subs, organic_revenue_eur
    Filters: medium='organic' AND source IN ('google', 'google-play')
    Uses Application Default Credentials (user account) for cross-project access.
    """
    # Use ADC (user credentials) for Traininpink project access
    # The service account key only has seo-and-aso-dashboard access
    import google.auth
    creds, _ = google.auth.default()
    client = bigquery.Client(credentials=creds, project="constant-host-348313")
    
    from datetime import datetime, timedelta
    
    if not start_date or not end_date:
        end_date = (datetime.now() - timedelta(days=1)).date()
        start_date = end_date - timedelta(days=28)
    
    start_str = start_date.strftime('%Y%m%d') if hasattr(start_date, 'strftime') else str(start_date).replace('-', '')
    end_str = end_date.strftime('%Y%m%d') if hasattr(end_date, 'strftime') else str(end_date).replace('-', '')
    lookback_str = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
    
    query = f"""
    WITH user_first_source AS (
        SELECT 
            user_pseudo_id,
            ANY_VALUE(traffic_source.source) as first_source,
            ANY_VALUE(traffic_source.medium) as first_medium
        FROM `constant-host-348313.analytics_328868717.events_*`
        WHERE _TABLE_SUFFIX BETWEEN '{lookback_str}' AND '{end_str}'
          AND platform = "ANDROID"
          AND event_name = "first_open"
        GROUP BY user_pseudo_id
    ),
    purchases AS (
        SELECT 
            user_pseudo_id,
            PARSE_DATE("%Y%m%d", event_date) as date,
            (SELECT value.string_value FROM UNNEST(event_params) WHERE key = "product_id") as product_id,
            (SELECT value.int_value FROM UNNEST(event_params) WHERE key = "value") as value_raw
        FROM `constant-host-348313.analytics_328868717.events_*`
        WHERE _TABLE_SUFFIX BETWEEN '{start_str}' AND '{end_str}'
          AND event_name = "in_app_purchase"
          AND platform = "ANDROID"
    )
    SELECT 
        CASE 
            WHEN p.product_id LIKE "%_1m_%" OR p.product_id = "tp_bundle_1m" THEN "1 Month"
            WHEN p.product_id LIKE "%_6m_%" OR p.product_id = "tp_bundle_6m" THEN "6 Months"
            WHEN p.product_id LIKE "%_1y_%" OR p.product_id = "tp_bundle_1y" THEN "1 Year"
            ELSE "Other"
        END as plan_duration,
        COUNT(DISTINCT p.user_pseudo_id) as organic_new_subs,
        COUNT(*) as purchase_events,
        ROUND(SUM(p.value_raw)/1000000.0, 2) as organic_revenue_eur,
        ROUND(AVG(p.value_raw)/1000000.0, 2) as avg_price_eur
    FROM purchases p
    LEFT JOIN user_first_source u USING(user_pseudo_id)
    WHERE u.first_medium = "organic"
      AND u.first_source IN ("google", "google-play")
      AND p.product_id IS NOT NULL
    GROUP BY plan_duration
    ORDER BY 
      CASE plan_duration
        WHEN '1 Month' THEN 1
        WHEN '6 Months' THEN 2
        WHEN '1 Year' THEN 3
        ELSE 4
      END
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        st.warning(f"Could not load Android plans: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_ios_new_subs_by_plan(start_date=None, end_date=None):
    """Get iOS new subscribers by plan from Apple subscription events.
    Apple doesn't share source attribution - returns TOTAL new subs by plan."""
    client = get_bigquery_client()
    
    where_date = ""
    if start_date and end_date:
        start_str = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
        end_str = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date)
        where_date = f"AND date BETWEEN '{start_str}' AND '{end_str}'"
    else:
        where_date = "AND date >= DATE_SUB(CURRENT_DATE(), INTERVAL 28 DAY)"
    
    query = f"""
    SELECT 
        duration as plan_duration,
        SUM(CASE WHEN event_type = 'Subscribe' THEN quantity ELSE 0 END) as paid_subs,
        SUM(CASE WHEN event_type = 'Start Introductory Offer' THEN quantity ELSE 0 END) as trial_subs,
        SUM(quantity) as total_new_subs
    FROM `seo-and-aso-dashboard.seo_data.appstore_daily_sub_events`
    WHERE event_type IN ('Subscribe', 'Start Introductory Offer')
      {where_date}
    GROUP BY plan_duration
    ORDER BY 
      CASE plan_duration
        WHEN '1 Month' THEN 1
        WHEN '6 Months' THEN 2
        WHEN '1 Year' THEN 3
        ELSE 4
      END
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        return pd.DataFrame()
