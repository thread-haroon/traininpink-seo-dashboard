"""Page 1: Google Search Console — uses accurate gsc_totals + gsc_by_device."""

import streamlit as st

from lib.data_loader import (
    get_aggregate_kpis,
    get_available_countries,
    get_available_devices,
    get_available_sites,
    get_daily_timeseries,
    get_gsc_device_breakdown,
    get_gsc_device_kpis,
    get_gsc_totals_kpis,
    get_gsc_totals_timeseries,
    get_top_dimension,
)
from lib.filters import render_date_filters, render_dimension_filters, render_site_filter
from lib.kpi_cards import render_kpi_row
from lib.charts import render_time_series_chart, render_top_table


st.set_page_config(
    page_title="Google Search Console | SEO Dashboard",
    page_icon="🔍",
    layout="wide",
)


# Header
st.title("🔍 Google Search Console")


# Sidebar filters
gsc_sites = get_available_sites("gsc_data")
gsc_countries = get_available_countries("gsc_data")
gsc_devices = get_available_devices("gsc_data")

selected_site = render_site_filter(gsc_sites, key_prefix="gsc")
date_range = render_date_filters(key_prefix="gsc", default_index=0)
country, device = render_dimension_filters(gsc_countries, gsc_devices, key_prefix="gsc")

country_filter_for_query = country
if country == "_REST_OF_WORLD_":
    country_filter_for_query = None

# Determine which data source to use
no_country = (country is None or country == "_REST_OF_WORLD_")
no_device = (device is None)

# Use accurate totals when no filters - matches GSC UI exactly
use_accurate_totals = no_country and no_device
# Use accurate device data when only device filter applied (no country)
use_accurate_device = no_country and not no_device

# Banner
banner_text = "📅 **Showing:** " + str(date_range.current.start) + " → " + str(date_range.current.end) + " (" + str(date_range.current.days) + " days)"
if date_range.comparison:
    banner_text += "  •  ⚖️ **Compared to:** " + str(date_range.comparison.start) + " → " + str(date_range.comparison.end) + " (" + date_range.comparison_label + ")"
st.info(banner_text)

if use_accurate_totals or use_accurate_device:
    st.caption("✅ KPIs match GSC official UI exactly")
else:
    st.caption("⚠️ Country-filtered data may show 10-20% lower than GSC UI totals (Google's privacy filtering)")

if country == "_REST_OF_WORLD_":
    st.caption("💡 Showing 'Rest of the world' — excludes Italy, UK, UAE, USA")

st.markdown("---")


# Fetch KPI data
with st.spinner("Loading GSC data..."):
    if use_accurate_totals:
        current_kpis = get_gsc_totals_kpis(
            date_range.current.start,
            date_range.current.end,
            site_url=selected_site,
        )
    elif use_accurate_device:
        current_kpis = get_gsc_device_kpis(
            date_range.current.start,
            date_range.current.end,
            device=device,
            site_url=selected_site,
        )
    else:
        current_kpis = get_aggregate_kpis(
            "gsc_data",
            date_range.current.start,
            date_range.current.end,
            country=country_filter_for_query,
            device=device,
            site_url=selected_site,
        )

    previous_kpis = None
    if date_range.comparison:
        if use_accurate_totals:
            previous_kpis = get_gsc_totals_kpis(
                date_range.comparison.start,
                date_range.comparison.end,
                site_url=selected_site,
            )
        elif use_accurate_device:
            previous_kpis = get_gsc_device_kpis(
                date_range.comparison.start,
                date_range.comparison.end,
                device=device,
                site_url=selected_site,
            )
        else:
            previous_kpis = get_aggregate_kpis(
                "gsc_data",
                date_range.comparison.start,
                date_range.comparison.end,
                country=country_filter_for_query,
                device=device,
                site_url=selected_site,
            )


# KPI Row
st.subheader("📊 Key Metrics")
render_kpi_row(current_kpis, previous_kpis, comparison_label=date_range.comparison_label)
st.markdown("---")


# Daily Trend
st.subheader("📈 Daily Trend in Google Search Console")

metric_choice = st.radio(
    "Select metric to chart:",
    options=["clicks", "impressions", "ctr", "position"],
    horizontal=True,
    format_func=lambda x: {"clicks": "🖱️ Clicks", "impressions": "👁️ Impressions", "ctr": "📊 CTR", "position": "🎯 Position"}[x],
    key="gsc_metric",
)

with st.spinner("Loading time series..."):
    if use_accurate_totals:
        current_daily = get_gsc_totals_timeseries(
            date_range.current.start,
            date_range.current.end,
            site_url=selected_site,
        )
    else:
        current_daily = get_daily_timeseries(
            "gsc_data",
            date_range.current.start,
            date_range.current.end,
            country=country_filter_for_query,
            device=device,
            site_url=selected_site,
        )

    previous_daily = None
    if date_range.comparison:
        if use_accurate_totals:
            previous_daily = get_gsc_totals_timeseries(
                date_range.comparison.start,
                date_range.comparison.end,
                site_url=selected_site,
            )
        else:
            previous_daily = get_daily_timeseries(
                "gsc_data",
                date_range.comparison.start,
                date_range.comparison.end,
                country=country_filter_for_query,
                device=device,
                site_url=selected_site,
            )

render_time_series_chart(
    current_daily,
    metric=metric_choice,
    previous_df=previous_daily,
    comparison_label=date_range.comparison_label,
    title="GSC — Daily " + metric_choice.title(),
)
st.markdown("---")


# Device Breakdown — uses accurate gsc_by_device when no country filter
st.subheader("📱 Device Breakdown")

if no_country:
    st.caption("✅ Device data matches GSC UI exactly")
else:
    st.caption("⚠️ Device data may show 10-20% lower when filtered by country")

with st.spinner("Loading device data..."):
    if no_country:
        # Use accurate device data
        top_devices = get_gsc_device_breakdown(
            date_range.current.start,
            date_range.current.end,
            site_url=selected_site,
        )
    else:
        # Fall back to dimensional data when country filter is active
        top_devices = get_top_dimension(
            "gsc_data",
            "device",
            date_range.current.start,
            date_range.current.end,
            limit=10,
            country=country_filter_for_query,
            site_url=selected_site,
        )

render_top_table(top_devices, dimension_label="Device", hide_position=True)


# Footer
st.markdown("---")
st.caption("📅 Data range: " + str(date_range.current.start) + " to " + str(date_range.current.end) + " | Filters: country=" + (country if country else "all") + ", device=" + (device if device else "all"))
