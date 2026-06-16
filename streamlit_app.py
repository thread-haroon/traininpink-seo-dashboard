"""SEO Dashboard - Main page (uses accurate gsc_totals + bing_totals)."""

import streamlit as st

from lib.data_loader import (
    get_available_sites,
    get_bing_totals_kpis,
    get_bing_totals_timeseries,
    get_gsc_totals_kpis,
    get_gsc_totals_timeseries,
)
from lib.filters import (
    GSC_DATA_LAG_DAYS,
    render_date_filters,
    render_site_filter,
)
from lib.kpi_cards import render_kpi_row
from lib.charts import render_combined_timeseries, render_source_comparison


st.set_page_config(
    page_title="SEO Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title("📊 SEO Dashboard")
st.caption("Combined view of Google Search Console + Bing Webmaster Tools")


# Sidebar filters
gsc_sites = get_available_sites("gsc_data")

selected_site = render_site_filter(gsc_sites, key_prefix="overview")
date_range = render_date_filters(
    key_prefix="overview",
    default_index=0,
    lag_days=GSC_DATA_LAG_DAYS,
)


# Banner
banner_text = "📅 **Showing:** " + str(date_range.current.start) + " → " + str(date_range.current.end) + " (" + str(date_range.current.days) + " days)"
if date_range.comparison:
    banner_text += "  •  ⚖️ **Compared to:** " + str(date_range.comparison.start) + " → " + str(date_range.comparison.end) + " (" + date_range.comparison_label + ")"
st.info(banner_text)
st.caption("✅ All KPIs match official GSC + Bing data")
st.markdown("---")


# Fetch accurate data
with st.spinner("Loading SEO data..."):
    gsc_current = get_gsc_totals_kpis(
        date_range.current.start,
        date_range.current.end,
        site_url=selected_site,
    )
    bing_current = get_bing_totals_kpis(
        date_range.current.start,
        date_range.current.end,
        site_url=selected_site,
    )

    gsc_previous = bing_previous = None
    if date_range.comparison:
        gsc_previous = get_gsc_totals_kpis(
            date_range.comparison.start,
            date_range.comparison.end,
            site_url=selected_site,
        )
        bing_previous = get_bing_totals_kpis(
            date_range.comparison.start,
            date_range.comparison.end,
            site_url=selected_site,
        )


# Combined KPIs
def combine_kpis(gsc, bing):
    total_imp = gsc["impressions"] + bing["impressions"]
    return {
        "clicks": gsc["clicks"] + bing["clicks"],
        "impressions": total_imp,
        "ctr": (gsc["clicks"] + bing["clicks"]) / max(total_imp, 1),
        "position": (
            (gsc["position"] * gsc["impressions"]) + (bing["position"] * bing["impressions"])
        ) / max(total_imp, 1),
    }


combined_current = combine_kpis(gsc_current, bing_current)
combined_previous = combine_kpis(gsc_previous, bing_previous) if gsc_previous and bing_previous else None


# Combined Totals section
st.subheader("🌐 Combined Totals (Google + Bing)")
render_kpi_row(combined_current, combined_previous, comparison_label=date_range.comparison_label)
st.markdown("---")


# Per-source breakdown
st.subheader("📈 By Source")

col_g, col_b = st.columns(2)

with col_g:
    st.markdown("**🔍 Google Search Console**")
    render_kpi_row(gsc_current, gsc_previous, comparison_label=date_range.comparison_label)

with col_b:
    st.markdown("**🅱️ Bing Webmaster**")
    render_kpi_row(bing_current, bing_previous, comparison_label=date_range.comparison_label, show_position=False)

st.markdown("---")


# Daily Trend Analysis
st.subheader("📈 Daily Trend Analysis")

metric_choice = st.radio(
    "Select metric:",
    options=["clicks", "impressions", "ctr"],
    horizontal=True,
    format_func=lambda x: {"clicks": "🖱️ Clicks", "impressions": "👁️ Impressions", "ctr": "📊 CTR"}[x],
)

with st.spinner("Loading daily trends..."):
    gsc_daily = get_gsc_totals_timeseries(
        date_range.current.start,
        date_range.current.end,
        site_url=selected_site,
    )
    bing_daily = get_bing_totals_timeseries(
        date_range.current.start,
        date_range.current.end,
        site_url=selected_site,
    )

render_combined_timeseries(gsc_daily, bing_daily, metric=metric_choice)
st.markdown("---")


# Source Comparison
st.subheader("⚖️ Source Comparison")

col_clicks, col_impressions = st.columns(2)
with col_clicks:
    render_source_comparison(gsc_current, bing_current, metric="clicks")
with col_impressions:
    render_source_comparison(gsc_current, bing_current, metric="impressions")


# Footer
st.markdown("---")
st.caption(
    "📅 " + str(date_range.current.start) + " to " + str(date_range.current.end) +
    " (" + str(date_range.current.days) + " days)"
)
st.caption("👉 Use the navigation in the sidebar to explore individual sources in detail.")
