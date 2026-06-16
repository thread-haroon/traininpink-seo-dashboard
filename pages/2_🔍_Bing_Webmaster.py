"""Page 2: Bing Webmaster - clean executive view with KPIs + daily trend.
Uses 3-day lag to match GSC for consistent date ranges across pages."""

import pandas as pd
import streamlit as st

from lib.data_loader import (
    get_available_sites,
    get_bing_totals_kpis,
    get_bing_totals_timeseries,
)
from lib.filters import (
    BING_PRESET_RANGES,
    GSC_DATA_LAG_DAYS,
    render_date_filters,
    render_site_filter,
)
from lib.kpi_cards import render_kpi_row
from lib.charts import render_time_series_chart


# Page configuration
st.set_page_config(
    page_title="Bing Webmaster | SEO Dashboard",
    page_icon="🅱️",
    layout="wide",
)


# Header
st.title("🅱️ Bing Webmaster")
st.markdown("---")


# Sidebar filters (Bing-specific)
bing_sites = get_available_sites("bing_data")

selected_site = render_site_filter(bing_sites, key_prefix="bing")
date_range = render_date_filters(
    key_prefix="bing",
    preset_dict=BING_PRESET_RANGES,
    default_index=0,  # Default: Last 7 days
    lag_days=GSC_DATA_LAG_DAYS,  # Use SAME 3-day lag as GSC for consistency
)


# Banner
banner_text = "📅 **Showing:** " + str(date_range.current.start) + " → " + str(date_range.current.end) + " (" + str(date_range.current.days) + " days)"
if date_range.comparison:
    banner_text += "  •  ⚖️ **Compared to:** " + str(date_range.comparison.start) + " → " + str(date_range.comparison.end) + " (" + date_range.comparison_label + ")"
st.info(banner_text)
st.caption("✅ KPIs match Bing Webmaster Tools UI exactly")
st.caption("📌 Date range matches Google Search Console for cross-source comparability")
st.markdown("---")


# Fetch KPI data
with st.spinner("Loading Bing data..."):
    current_kpis = get_bing_totals_kpis(
        date_range.current.start,
        date_range.current.end,
        site_url=selected_site,
    )
    previous_kpis = None
    if date_range.comparison:
        previous_kpis = get_bing_totals_kpis(
            date_range.comparison.start,
            date_range.comparison.end,
            site_url=selected_site,
        )


# KPI Row - hide position for Bing (per user preference)
st.subheader("📊 Key Metrics")
render_kpi_row(current_kpis, previous_kpis, comparison_label=date_range.comparison_label, show_position=False)
st.markdown("---")


# Daily Trend Chart
st.subheader("📈 Daily Trend in Bing")

metric_choice = st.radio(
    "Select metric to chart:",
    options=["clicks", "impressions", "ctr"],
    horizontal=True,
    format_func=lambda x: {"clicks": "🖱️ Clicks", "impressions": "👁️ Impressions", "ctr": "📊 CTR"}[x],
    key="bing_metric",
)

with st.spinner("Loading time series..."):
    current_daily = get_bing_totals_timeseries(
        date_range.current.start,
        date_range.current.end,
        site_url=selected_site,
    )
    previous_daily = None
    if date_range.comparison:
        previous_daily = get_bing_totals_timeseries(
            date_range.comparison.start,
            date_range.comparison.end,
            site_url=selected_site,
        )

render_time_series_chart(
    current_daily,
    metric=metric_choice,
    previous_df=previous_daily,
    comparison_label=date_range.comparison_label,
    title="Bing — Daily " + metric_choice.title(),
)


# Footer
st.markdown("---")
st.caption("📅 Data range: " + str(date_range.current.start) + " to " + str(date_range.current.end) + " (" + str(date_range.current.days) + " days)")
st.caption("ℹ️ Bing Webmaster Tools API does not provide device-level breakdown data")
