"""Page 3: Combined Sources - Google + Bing executive view.
Uses gsc_totals + bing_totals for accuracy. Same 3-day lag as other pages."""

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


# Page configuration
st.set_page_config(
    page_title="Combined Sources | SEO Dashboard",
    page_icon="🌐",
    layout="wide",
)


# Header
st.title("🌐 Combined Sources — Google + Bing")
st.caption("Side-by-side comparison of all search engine performance")
st.markdown("---")


# Sidebar filters - only site filter (no country/device since Bing has neither)
gsc_sites = get_available_sites("gsc_data")

selected_site = render_site_filter(gsc_sites, key_prefix="combined")
date_range = render_date_filters(
    key_prefix="combined",
    default_index=0,  # Default: Last 7 days
    lag_days=GSC_DATA_LAG_DAYS,  # Same 3-day lag as GSC and Bing
)


# Banner
banner_text = "📅 **Showing:** " + str(date_range.current.start) + " → " + str(date_range.current.end) + " (" + str(date_range.current.days) + " days)"
if date_range.comparison:
    banner_text += "  •  ⚖️ **Compared to:** " + str(date_range.comparison.start) + " → " + str(date_range.comparison.end) + " (" + date_range.comparison_label + ")"
st.info(banner_text)
st.caption("✅ All KPIs match official GSC + Bing UI exactly")
st.markdown("---")


# Fetch accurate data from both sources
with st.spinner("Loading data from both sources..."):
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


# Compute combined values
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


# Combined Totals
st.subheader("🌐 Combined Totals (Google + Bing)")
render_kpi_row(combined_current, combined_previous, comparison_label=date_range.comparison_label)
st.markdown("---")


# Side-by-Side
st.subheader("⚖️ Side-by-Side Comparison")

col_g, col_b = st.columns(2)

with col_g:
    st.markdown("### 🔍 Google Search Console")
    render_kpi_row(gsc_current, gsc_previous, comparison_label=date_range.comparison_label)

with col_b:
    st.markdown("### 🅱️ Bing Webmaster")
    render_kpi_row(bing_current, bing_previous, comparison_label=date_range.comparison_label, show_position=False)

st.markdown("---")


# Daily Trends — Google vs Bing (much cleaner than weekly)
st.subheader("📈 Daily Trends — Google vs Bing")

metric_choice = st.radio(
    "Select metric:",
    options=["clicks", "impressions", "ctr"],
    horizontal=True,
    format_func=lambda x: {"clicks": "🖱️ Clicks", "impressions": "👁️ Impressions", "ctr": "📊 CTR"}[x],
    key="combined_metric",
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


# Source Share
st.subheader("📊 Source Share")

col1, col2 = st.columns(2)

with col1:
    render_source_comparison(gsc_current, bing_current, metric="clicks")

with col2:
    render_source_comparison(gsc_current, bing_current, metric="impressions")


# Share percentages
total_clicks = gsc_current["clicks"] + bing_current["clicks"]
total_impressions = gsc_current["impressions"] + bing_current["impressions"]

if total_clicks > 0:
    gsc_click_share = gsc_current["clicks"] / total_clicks * 100
    bing_click_share = bing_current["clicks"] / total_clicks * 100
    st.info(
        "📊 **Click share:** Google = **{:.1f}%** | Bing = **{:.1f}%**".format(
            gsc_click_share, bing_click_share
        )
    )

if total_impressions > 0:
    gsc_imp_share = gsc_current["impressions"] / total_impressions * 100
    bing_imp_share = bing_current["impressions"] / total_impressions * 100
    st.info(
        "👁️ **Impression share:** Google = **{:.1f}%** | Bing = **{:.1f}%**".format(
            gsc_imp_share, bing_imp_share
        )
    )


# Footer
st.markdown("---")
st.caption(
    "📅 Showing **" + str(date_range.current.start) + "** to **" +
    str(date_range.current.end) + "** (" + str(date_range.current.days) + " days)"
)
