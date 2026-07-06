"""Page 1: Google Search Console — uses accurate gsc_totals + gsc_by_device."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from lib.data_loader import (
    get_aggregate_kpis,
    get_available_countries,
    get_available_devices,
    get_available_sites,
    get_daily_timeseries,
    get_gsc_country_breakdown,
    get_gsc_device_breakdown,
    get_gsc_device_kpis,
    get_gsc_totals_kpis,
    get_gsc_totals_timeseries,
    get_top_dimension,
)
from lib.filters import (
    render_date_filters,
    render_dimension_filters,
    render_site_filter,
    COUNTRY_DISPLAY_NAMES,
    FEATURED_COUNTRIES,
)
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

use_accurate_totals = no_country and no_device
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


# ============================================
# 🌍 COUNTRY BREAKDOWN (NEW SECTION)
# ============================================
st.subheader("🌍 Country Breakdown")

if country and country != "_REST_OF_WORLD_":
    st.caption("💡 Country filter is active in sidebar. Change to 'All' to see full breakdown.")
else:
    st.caption("✅ Country data matches GSC UI exactly (using gsc_by_country table)")

with st.spinner("Loading country data..."):
    # Get top countries for current period - use ACCURATE gsc_by_country table
    # This matches GSC UI exactly (includes anonymized queries)
    current_countries_df = get_gsc_country_breakdown(
        date_range.current.start,
        date_range.current.end,
        site_url=selected_site,
        limit=50,
    )
    
    previous_countries_df = pd.DataFrame()
    if date_range.comparison:
        previous_countries_df = get_gsc_country_breakdown(
            date_range.comparison.start,
            date_range.comparison.end,
            site_url=selected_site,
            limit=100,  # Get more to match against top 15 current
        )

# Country code to full name mapping (ISO 3166-1 alpha-3)
COUNTRY_FULL_NAMES = {
    "ita": "🇮🇹 Italy",
    "gbr": "🇬🇧 United Kingdom",
    "are": "🇦🇪 United Arab Emirates",
    "usa": "🇺🇸 United States",
    "fra": "🇫🇷 France",
    "deu": "🇩🇪 Germany",
    "esp": "🇪🇸 Spain",
    "prt": "🇵🇹 Portugal",
    "nld": "🇳🇱 Netherlands",
    "bel": "🇧🇪 Belgium",
    "che": "🇨🇭 Switzerland",
    "aut": "🇦🇹 Austria",
    "swe": "🇸🇪 Sweden",
    "nor": "🇳🇴 Norway",
    "dnk": "🇩🇰 Denmark",
    "fin": "🇫🇮 Finland",
    "pol": "🇵🇱 Poland",
    "cze": "🇨🇿 Czech Republic",
    "hun": "🇭🇺 Hungary",
    "grc": "🇬🇷 Greece",
    "rou": "🇷🇴 Romania",
    "bgr": "🇧🇬 Bulgaria",
    "hrv": "🇭🇷 Croatia",
    "srb": "🇷🇸 Serbia",
    "svk": "🇸🇰 Slovakia",
    "svn": "🇸🇮 Slovenia",
    "lux": "🇱🇺 Luxembourg",
    "irl": "🇮🇪 Ireland",
    "isl": "🇮🇸 Iceland",
    "mlt": "🇲🇹 Malta",
    "cyp": "🇨🇾 Cyprus",
    "est": "🇪🇪 Estonia",
    "lva": "🇱🇻 Latvia",
    "ltu": "🇱🇹 Lithuania",
    "rus": "🇷🇺 Russia",
    "ukr": "🇺🇦 Ukraine",
    "tur": "🇹🇷 Turkey",
    "isr": "🇮🇱 Israel",
    "sau": "🇸🇦 Saudi Arabia",
    "qat": "🇶🇦 Qatar",
    "kwt": "🇰🇼 Kuwait",
    "bhr": "🇧🇭 Bahrain",
    "omn": "🇴🇲 Oman",
    "jor": "🇯🇴 Jordan",
    "lbn": "🇱🇧 Lebanon",
    "egy": "🇪🇬 Egypt",
    "mar": "🇲🇦 Morocco",
    "tun": "🇹🇳 Tunisia",
    "dza": "🇩🇿 Algeria",
    "lby": "🇱🇾 Libya",
    "zaf": "🇿🇦 South Africa",
    "nga": "🇳🇬 Nigeria",
    "ken": "🇰🇪 Kenya",
    "gha": "🇬🇭 Ghana",
    "eth": "🇪🇹 Ethiopia",
    "can": "🇨🇦 Canada",
    "mex": "🇲🇽 Mexico",
    "bra": "🇧🇷 Brazil",
    "arg": "🇦🇷 Argentina",
    "chl": "🇨🇱 Chile",
    "col": "🇨🇴 Colombia",
    "per": "🇵🇪 Peru",
    "ven": "🇻🇪 Venezuela",
    "ecu": "🇪🇨 Ecuador",
    "ury": "🇺🇾 Uruguay",
    "pry": "🇵🇾 Paraguay",
    "bol": "🇧🇴 Bolivia",
    "chn": "🇨🇳 China",
    "jpn": "🇯🇵 Japan",
    "kor": "🇰🇷 South Korea",
    "prk": "🇰🇵 North Korea",
    "twn": "🇹🇼 Taiwan",
    "hkg": "🇭🇰 Hong Kong",
    "mac": "🇲🇴 Macau",
    "sgp": "🇸🇬 Singapore",
    "mys": "🇲🇾 Malaysia",
    "tha": "🇹🇭 Thailand",
    "idn": "🇮🇩 Indonesia",
    "phl": "🇵🇭 Philippines",
    "vnm": "🇻🇳 Vietnam",
    "khm": "🇰🇭 Cambodia",
    "lao": "🇱🇦 Laos",
    "mmr": "🇲🇲 Myanmar",
    "ind": "🇮🇳 India",
    "pak": "🇵🇰 Pakistan",
    "bgd": "🇧🇩 Bangladesh",
    "lka": "🇱🇰 Sri Lanka",
    "npl": "🇳🇵 Nepal",
    "bhu": "🇧🇹 Bhutan",
    "afg": "🇦🇫 Afghanistan",
    "irn": "🇮🇷 Iran",
    "irq": "🇮🇶 Iraq",
    "syr": "🇸🇾 Syria",
    "yem": "🇾🇪 Yemen",
    "aus": "🇦🇺 Australia",
    "nzl": "🇳🇿 New Zealand",
    "fji": "🇫🇯 Fiji",
    "png": "🇵🇬 Papua New Guinea",
}


# Add display names for countries
def get_country_display(code):
    """Convert country code to full name with flag."""
    if not code:
        return "🌐 Unknown"
    code_lower = code.lower()
    if code_lower in COUNTRY_FULL_NAMES:
        return COUNTRY_FULL_NAMES[code_lower]
    # Fallback: uppercase the code with globe emoji
    return "🌍 " + code.upper()


if current_countries_df is None or current_countries_df.empty:
    st.info("No country data available for this period.")
else:
    # Prepare display dataframe
    display_df = current_countries_df.head(10).copy()
    display_df["Country"] = display_df["name"].apply(get_country_display)
    
    # Match with previous period data - both clicks AND impressions
    prev_clicks_lookup = {}
    prev_impressions_lookup = {}
    if not previous_countries_df.empty:
        for _, row in previous_countries_df.iterrows():
            prev_clicks_lookup[row["name"]] = row["clicks"]
            prev_impressions_lookup[row["name"]] = row["impressions"]
    
    display_df["prev_clicks"] = display_df["name"].apply(lambda c: prev_clicks_lookup.get(c, 0))
    display_df["prev_impressions"] = display_df["name"].apply(lambda c: prev_impressions_lookup.get(c, 0))
    
    # Calculate percentage change with COLORED indicators
    def calc_change(current, previous):
        """Calculate change % with green/red visual indicator."""
        if previous == 0:
            return "✨ New" if current > 0 else "—"
        change_pct = ((current - previous) / previous) * 100
        if change_pct > 0:
            return f"🟢 ↑ {abs(change_pct):.0f}%"
        elif change_pct < 0:
            return f"🔴 ↓ {abs(change_pct):.0f}%"
        else:
            return f"⚪ → 0%"
    
    def calc_clicks_change(row):
        return calc_change(row["clicks"], row["prev_clicks"])
    
    def calc_impressions_change(row):
        return calc_change(row["impressions"], row["prev_impressions"])
    
    display_df["Clicks Δ%"] = display_df.apply(calc_clicks_change, axis=1)
    display_df["Impr Δ%"] = display_df.apply(calc_impressions_change, axis=1)
    
    # ============================================
    # BAR CHART: Current vs Previous
    # ============================================
    top_10 = display_df.head(10).copy()
    
    fig = go.Figure()
    
    # Current period bars
    fig.add_trace(go.Bar(
        y=top_10["Country"],
        x=top_10["clicks"],
        name="Current period",
        orientation="h",
        marker=dict(color="#2563eb"),
        text=top_10["clicks"].apply(lambda x: f"{int(x):,}"),
        textposition="outside",
        textfont=dict(color="white"),
    ))
    
    # Previous period bars (only if comparison data exists)
    if not previous_countries_df.empty:
        fig.add_trace(go.Bar(
            y=top_10["Country"],
            x=top_10["prev_clicks"],
            name="Previous period",
            orientation="h",
            marker=dict(color="#94a3b8"),
            text=top_10["prev_clicks"].apply(lambda x: f"{int(x):,}"),
            textposition="outside",
            textfont=dict(color="white"),
        ))
    
    fig.update_layout(
        title="Top 10 Countries — Clicks Comparison",
        barmode="group",
        height=500,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
        xaxis=dict(
            title="Clicks",
            showgrid=True,
            gridcolor="rgba(255,255,255,0.1)",
        ),
        yaxis=dict(
            title="",
            autorange="reversed",  # Show top country at top
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=10, r=10, t=60, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # ============================================
    # DETAILED TABLE
    # ============================================
    st.markdown("**📋 Full Country Breakdown**")
    
    # Build table with both clicks AND impressions comparison
    table_df = display_df[[
        "Country", 
        "clicks", "prev_clicks", "Clicks Δ%",
        "impressions", "prev_impressions", "Impr Δ%",
        "ctr", "position"
    ]].copy()
    
    table_df.columns = [
        "Country", 
        "Clicks", "Prev Clicks", "Clicks Δ%",
        "Impressions", "Prev Impressions", "Impr Δ%",
        "CTR", "Position"
    ]
    
    # Format all numeric columns
    table_df["Clicks"] = table_df["Clicks"].apply(lambda x: f"{int(x):,}")
    table_df["Prev Clicks"] = table_df["Prev Clicks"].apply(lambda x: f"{int(x):,}")
    table_df["Impressions"] = table_df["Impressions"].apply(lambda x: f"{int(x):,}")
    table_df["Prev Impressions"] = table_df["Prev Impressions"].apply(lambda x: f"{int(x):,}")
    table_df["CTR"] = table_df["CTR"].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "—")
    table_df["Position"] = table_df["Position"].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "—")
    
    st.dataframe(
        table_df,
        hide_index=True,
        use_container_width=True,
        height=400,
        column_config={
            "Country": st.column_config.TextColumn("Country", width="medium"),
            "Clicks": st.column_config.TextColumn("Clicks", width="small"),
            "Prev Clicks": st.column_config.TextColumn("Prev Clicks", width="small"),
            "Clicks Δ%": st.column_config.TextColumn("Clicks Δ%", width="small"),
            "Impressions": st.column_config.TextColumn("Impressions", width="small"),
            "Prev Impressions": st.column_config.TextColumn("Prev Impressions", width="small"),
            "Impr Δ%": st.column_config.TextColumn("Impr Δ%", width="small"),
            "CTR": st.column_config.TextColumn("CTR", width="small"),
            "Position": st.column_config.TextColumn("Position", width="small"),
        },
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
        top_devices = get_gsc_device_breakdown(
            date_range.current.start,
            date_range.current.end,
            site_url=selected_site,
        )
    else:
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
