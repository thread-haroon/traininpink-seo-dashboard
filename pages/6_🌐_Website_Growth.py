"""Website Growth Intelligence Dashboard
Organic SEO performance for traininpink.net + app.traininpink.net + www.traininpink.net
NO revenue (GA4 web ecommerce not configured) - focus on traffic, conversions, engagement"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.data_loader import (
    load_website_metrics, load_website_landing_pages,
    load_website_countries, load_website_events,
    get_website_country_list, get_website_hostname_list
)

st.set_page_config(
    page_title="Website Growth | Organic Intelligence",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    #MainMenu, footer, header, [data-testid="stHeader"], [data-testid="stToolbar"], .stDeployButton {
        display: none !important; visibility: hidden !important;
    }
    .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
    .stApp { background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0a0e27 100%); }
    .page-title {
        font-size: 38px; font-weight: 800; color: white; margin: 0 0 8px 0;
        background: linear-gradient(135deg, #fff 0%, #60a5fa 50%, #34d399 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    }
    .page-subtitle { color: rgba(255,255,255,0.6); font-size: 14px; margin-bottom: 16px; }
    .date-info-bar {
        background: linear-gradient(135deg, rgba(96,165,250,0.15) 0%, rgba(52,211,153,0.05) 100%);
        backdrop-filter: blur(20px); border: 1px solid rgba(96,165,250,0.3);
        border-radius: 12px; padding: 14px 20px; margin-bottom: 24px;
        color: white; font-size: 14px;
    }
    .date-info-bar strong { color: #93c5fd; font-weight: 700; }
    .glass-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.03) 100%);
        backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px; padding: 22px; margin-bottom: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .glass-card:hover { transform: translateY(-3px); box-shadow: 0 12px 40px rgba(0,0,0,0.3); }
    .glass-card-hero {
        background: linear-gradient(135deg, rgba(167,139,250,0.2) 0%, rgba(96,165,250,0.15) 50%, rgba(52,211,153,0.1) 100%);
        backdrop-filter: blur(20px); border: 1px solid rgba(167,139,250,0.3);
        border-radius: 16px; padding: 22px; margin-bottom: 16px;
        box-shadow: 0 8px 32px rgba(167,139,250,0.2);
    }
    .kpi-label { color: rgba(255,255,255,0.55); font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 6px; }
    .kpi-value { color: white; font-size: 30px; font-weight: 800; margin: 0; line-height: 1.1; }
    .kpi-delta { font-size: 12px; font-weight: 600; margin-top: 6px; }
    .kpi-delta.positive { color: #34d399; }
    .kpi-delta.negative { color: #f87171; }
    .kpi-delta.neutral { color: rgba(255,255,255,0.5); }
    .section-header {
        color: white; font-size: 24px; font-weight: 700; margin: 36px 0 16px 0;
        padding-bottom: 10px;
        border-bottom: 2px solid rgba(96,165,250,0.25);
    }
    .section-subtitle {
        color: rgba(255,255,255,0.55); font-size: 13px;
        margin-top: -10px; margin-bottom: 20px; font-style: italic;
    }
    .info-banner {
        background: linear-gradient(135deg, rgba(251,191,36,0.15) 0%, rgba(251,146,60,0.05) 100%);
        border: 1px solid rgba(251,191,36,0.3);
        border-radius: 10px; padding: 12px 16px; margin: 12px 0;
        color: #fde68a; font-size: 13px;
    }
    .stMarkdown { color: white; }
    h1, h2, h3, h4, h5, h6 { color: white !important; }
    section[data-testid="stSidebar"] { background: linear-gradient(180deg, #0f1729 0%, #1e2942 100%) !important; }
    section[data-testid="stSidebar"] * { color: white !important; }
    section[data-testid="stSidebar"] label { color: rgba(255,255,255,0.85) !important; font-weight: 600 !important; }
    section[data-testid="stSidebar"] [data-baseweb="select"] { background-color: rgba(255,255,255,0.08) !important; border-radius: 8px !important; }
    section[data-testid="stSidebar"] [data-baseweb="select"] > div { background-color: transparent !important; color: white !important; border: 1px solid rgba(255,255,255,0.15) !important; }
    section[data-testid="stSidebar"] [data-baseweb="select"] input { color: white !important; }
    section[data-testid="stSidebar"] [data-baseweb="select"] svg { fill: white !important; }
    [data-baseweb="popover"] [role="option"] { color: #1a1538 !important; background-color: white !important; }
    [data-baseweb="popover"] [role="option"]:hover { background-color: #ede9fe !important; }
    section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1) !important; }
    [data-testid="stDataFrame"] [role="cell"], [data-testid="stDataFrame"] [role="columnheader"] { text-align: center !important; }

    /* ==================================== */
    /* 🎨 FIXED DATE INPUT - DARK THEME     */
    /* ==================================== */
    section[data-testid="stSidebar"] [data-testid="stDateInput"] {
        background-color: transparent !important;
    }
    section[data-testid="stSidebar"] [data-testid="stDateInput"] > div {
        background-color: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stDateInput"] input {
        background-color: transparent !important;
        color: white !important;
        border: none !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stDateInput"] input::placeholder {
        color: rgba(255,255,255,0.5) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stDateInput"] svg {
        fill: rgba(255,255,255,0.7) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stDateInput"] > div:focus-within {
        border-color: #60a5fa !important;
        box-shadow: 0 0 0 2px rgba(96,165,250,0.2) !important;
    }
    /* CALENDAR POPUP - DARK */
    [data-baseweb="calendar"],
    [data-baseweb="datepicker"] {
        background-color: #0f1729 !important;
        color: white !important;
        border: 1px solid rgba(96,165,250,0.3) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5) !important;
    }
    [data-baseweb="calendar"] * {
        color: white !important;
        border-color: rgba(255,255,255,0.1) !important;
    }
    [data-baseweb="calendar"] [role="presentation"] {
        color: rgba(255,255,255,0.5) !important;
        background-color: transparent !important;
    }
    [data-baseweb="calendar"] [role="gridcell"] button,
    [data-baseweb="calendar"] [role="button"] {
        color: white !important;
        background-color: transparent !important;
        border-radius: 6px !important;
        transition: background-color 0.2s !important;
    }
    [data-baseweb="calendar"] [role="gridcell"] button:hover {
        background-color: rgba(96,165,250,0.3) !important;
        color: white !important;
    }
    [data-baseweb="calendar"] [aria-selected="true"],
    [data-baseweb="calendar"] [aria-pressed="true"] {
        background-color: #60a5fa !important;
        color: white !important;
        font-weight: 700 !important;
    }
    [data-baseweb="calendar"] [aria-current="date"] {
        background-color: rgba(96,165,250,0.2) !important;
        color: #93c5fd !important;
        border: 1px solid #60a5fa !important;
    }
    [data-baseweb="calendar"] [aria-disabled="true"] {
        color: rgba(255,255,255,0.2) !important;
        background-color: transparent !important;
    }
    [data-baseweb="calendar"] [data-range-end="true"],
    [data-baseweb="calendar"] [data-range-start="true"] {
        background-color: #60a5fa !important;
        color: white !important;
    }
    [data-baseweb="calendar"] [data-range="true"] {
        background-color: rgba(96,165,250,0.25) !important;
        color: white !important;
    }
    [data-baseweb="calendar"] [role="heading"] {
        color: white !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }
    [data-baseweb="calendar"] button[aria-label*="Previous"],
    [data-baseweb="calendar"] button[aria-label*="Next"] {
        background-color: transparent !important;
        color: white !important;
        border-radius: 6px !important;
    }
    [data-baseweb="calendar"] button[aria-label*="Previous"]:hover,
    [data-baseweb="calendar"] button[aria-label*="Next"]:hover {
        background-color: rgba(96,165,250,0.3) !important;
    }
    [data-baseweb="calendar"] button svg {
        fill: white !important;
    }
    [data-baseweb="calendar"] select,
    [data-baseweb="calendar"] [role="combobox"] {
        background-color: rgba(255,255,255,0.1) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }

</style>
""", unsafe_allow_html=True)


def format_number(value):
    if pd.isna(value) or value is None: return "0"
    if value >= 1_000_000: return f"{value/1_000_000:.2f}M"
    elif value >= 1_000: return f"{value/1_000:.1f}K"
    return f"{value:,.0f}"


def format_duration(seconds):
    if pd.isna(seconds) or seconds is None or seconds == 0: return "0s"
    if seconds >= 3600: return f"{seconds/3600:.1f}h"
    if seconds >= 60: return f"{seconds/60:.1f}m"
    return f"{seconds:.0f}s"


def get_date_range(option, anchor_date, custom_dates=None, min_date=None):
    if option == "Last 7 days": return anchor_date - timedelta(days=7), anchor_date
    elif option == "Last 28 days": return anchor_date - timedelta(days=28), anchor_date
    elif option == "Last 30 days": return anchor_date - timedelta(days=30), anchor_date
    elif option == "Last 90 days": return anchor_date - timedelta(days=90), anchor_date
    elif option == "Last 6 months": return anchor_date - timedelta(days=180), anchor_date
    elif option == "Last 12 months": return anchor_date - timedelta(days=365), anchor_date
    elif option == "All time" and min_date: return min_date, anchor_date
    elif option == "Custom range" and custom_dates and isinstance(custom_dates, tuple) and len(custom_dates) == 2:
        return custom_dates[0], custom_dates[1]
    return anchor_date - timedelta(days=28), anchor_date


def calc_delta(curr, prev):
    if prev == 0: return 100 if curr > 0 else 0
    return ((curr - prev) / prev) * 100


def render_kpi(col, label, value_str, delta_pct=None, hero=False):
    delta_html = ''
    if delta_pct is not None:
        if delta_pct > 0: cls, arrow = "positive", "↑"
        elif delta_pct < 0: cls, arrow = "negative", "↓"
        else: cls, arrow = "neutral", "→"
        delta_html = f'<div class="kpi-delta {cls}">{arrow} {abs(delta_pct):.1f}% vs previous</div>'
    card_class = "glass-card-hero" if hero else "glass-card"
    col.markdown(f"""
    <div class="{card_class}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value_str}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def filter_organic(df, organic_type='wider'):
    """Filter dataframe by organic type."""
    if df.empty:
        return df
    if organic_type == 'strict':
        return df[df['is_organic_strict'] == True].copy()
    elif organic_type == 'direct':
        return df[df['is_direct'] == True].copy()
    else:
        return df[df['is_organic_wider'] == True].copy()


# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("### 🌐 Website Growth Filters")
    st.markdown("---")
    
    st.markdown("### 🏷️ Hostname")
    try:
        all_hostnames = get_website_hostname_list()
        hostname = st.selectbox("Select hostname", options=["All"] + all_hostnames, index=0, label_visibility="collapsed")
    except:
        hostname = "All"
    
    st.markdown("---")
    st.markdown("### 📅 Date Range")
    date_range_option = st.selectbox(
        "Select range",
        options=["Last 7 days", "Last 28 days", "Last 30 days", "Last 90 days", "Last 6 months", "Last 12 months", "All time", "Custom range"],
        index=1, label_visibility="collapsed",
    )
    today = date.today()
    custom_dates = None
    min_date = date(2025, 5, 7)
    if date_range_option == "Custom range":
        custom_dates = st.date_input("Pick dates", value=(today - timedelta(days=28), today), min_value=min_date, max_value=today)
    start_date, end_date = get_date_range(date_range_option, today, custom_dates, min_date)
    period_days = (end_date - start_date).days
    st.caption(f"📊 {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')} ({period_days}d)")
    
    st.markdown("---")
    st.markdown("### 🌍 Country")
    try:
        countries = get_website_country_list()
        country = st.selectbox("Select country", options=["All"] + countries, index=0, label_visibility="collapsed")
    except:
        country = "All"
    
    st.markdown("---")
    st.markdown("### 🔄 Comparison")
    comparison_option = st.selectbox(
        "Compare against",
        options=[
            "Previous period",
            "Previous year",
            "Custom range",
            "No comparison",
        ],
        index=0, label_visibility="collapsed",
        help="Previous period: same length ending day before main period. Previous year: same dates one year ago."
    )
    
    compare_start = compare_end = None
    if comparison_option == "Previous period":
        compare_end = start_date - timedelta(days=1)
        compare_start = compare_end - timedelta(days=period_days)
    elif comparison_option == "Previous year":
        compare_start = start_date - timedelta(days=365)
        compare_end = end_date - timedelta(days=365)
    elif comparison_option == "Custom range":
        compare_custom_dates = st.date_input(
            "Pick comparison dates",
            value=(today - timedelta(days=60), today - timedelta(days=30)),
            min_value=min_date, max_value=today, key="compare_custom",
        )
        if compare_custom_dates and isinstance(compare_custom_dates, tuple) and len(compare_custom_dates) == 2:
            compare_start, compare_end = compare_custom_dates[0], compare_custom_dates[1]
    
    if compare_start and compare_end:
        compare_days = (compare_end - compare_start).days
        st.caption(f"⚖️ {compare_start.strftime('%Y-%m-%d')} → {compare_end.strftime('%Y-%m-%d')} ({compare_days}d)")


# ===== HEADER =====
st.markdown('<div class="page-title">🌐 Website Growth Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Organic SEO performance for traininpink.net</div>', unsafe_allow_html=True)

date_info = f"📅 <strong>Showing:</strong> {start_date.strftime('%b %d, %Y')} → {end_date.strftime('%b %d, %Y')} ({period_days}d)"
date_info += f" • 🏷️ <strong>Host:</strong> {hostname}"
if country != "All":
    date_info += f" • 🌍 <strong>Country:</strong> {country}"
if compare_start:
    date_info += f" • ⚖️ <strong>vs:</strong> {compare_start.strftime('%b %d')} → {compare_end.strftime('%b %d, %Y')}"
st.markdown(f'<div class="date-info-bar">{date_info}</div>', unsafe_allow_html=True)


# ===== LOAD DATA =====
try:
    with st.spinner("Loading website data..."):
        metrics_all = load_website_metrics(start_date, end_date, hostname)
        landing_all = load_website_landing_pages(start_date, end_date)
        countries_all = load_website_countries(start_date, end_date)
        events_all = load_website_events(start_date, end_date)
        if compare_start:
            metrics_compare_all = load_website_metrics(compare_start, compare_end, hostname)
            countries_compare_all = load_website_countries(compare_start, compare_end)
            events_compare_all = load_website_events(compare_start, compare_end)
        else:
            metrics_compare_all = pd.DataFrame()
            countries_compare_all = pd.DataFrame()
            events_compare_all = pd.DataFrame()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

if metrics_all.empty:
    st.warning("No website data in selected range.")
    st.stop()

# Apply country filter to all dataframes if needed
if country != "All":
    countries_all = countries_all[countries_all['country'] == country] if not countries_all.empty else countries_all


# ===== Filter to organic only =====
metrics_wider = filter_organic(metrics_all, 'wider')
metrics_strict = filter_organic(metrics_all, 'strict')
metrics_direct = filter_organic(metrics_all, 'direct')
landing_wider = filter_organic(landing_all, 'wider')
countries_wider = filter_organic(countries_all, 'wider')
events_wider = filter_organic(events_all, 'wider')


# ============================================
# SECTION 1: ORGANIC OVERVIEW
# ============================================
st.markdown('<div class="section-header">📊 Organic Overview</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Total organic website performance — Strict (Google/Bing search) + Direct (returning users)</div>', unsafe_allow_html=True)

total_active = int(metrics_wider['active_users'].sum())
total_new = int(metrics_wider['new_users'].sum())
total_returning = total_active - total_new
total_sessions = int(metrics_wider['sessions'].sum())
total_engaged = int(metrics_wider['engaged_sessions'].sum())
avg_engagement_rate = float(metrics_wider['engagement_rate'].mean() * 100) if not metrics_wider.empty else 0
avg_session_duration = float(metrics_wider['avg_session_duration'].mean()) if not metrics_wider.empty else 0
sessions_per_user = (total_sessions / total_active) if total_active > 0 else 0

# Conversion + subscription metrics from events
def get_event_count(df, name_or_list):
    if df.empty: return 0
    if isinstance(name_or_list, str): name_or_list = [name_or_list]
    return int(df[df['event_name'].isin(name_or_list)]['event_count'].sum())

conversions = get_event_count(events_wider, 'ga4convavanzate')
subscriptions = get_event_count(events_wider, ['subscription', 'webapp_successful_payment'])
trials = get_event_count(events_wider, 'website_free_trial_button')
quiz_starts = get_event_count(events_wider, 'quiz_start')
sign_ups = get_event_count(events_wider, 'sign in with email button')

conversion_rate = (subscriptions / total_sessions * 100) if total_sessions > 0 else 0

# Comparisons
if not metrics_compare_all.empty:
    m_cmp_w = filter_organic(metrics_compare_all, 'wider')
    e_cmp_w = filter_organic(events_compare_all, 'wider')
    p_active = int(m_cmp_w['active_users'].sum())
    p_new = int(m_cmp_w['new_users'].sum())
    p_returning = p_active - p_new
    p_sessions = int(m_cmp_w['sessions'].sum())
    p_subs = get_event_count(e_cmp_w, ['subscription', 'webapp_successful_payment'])
    p_conv = get_event_count(e_cmp_w, 'ga4convavanzate')
    p_eng_rate = float(m_cmp_w['engagement_rate'].mean() * 100) if not m_cmp_w.empty else 0
    p_conv_rate = (p_subs / p_sessions * 100) if p_sessions > 0 else 0
    d_active, d_new, d_returning = calc_delta(total_active, p_active), calc_delta(total_new, p_new), calc_delta(total_returning, p_returning)
    d_sessions, d_subs, d_conv = calc_delta(total_sessions, p_sessions), calc_delta(subscriptions, p_subs), calc_delta(conversions, p_conv)
    d_eng_rate, d_conv_rate = calc_delta(avg_engagement_rate, p_eng_rate), calc_delta(conversion_rate, p_conv_rate)
else:
    d_active = d_new = d_returning = d_sessions = d_subs = d_conv = d_eng_rate = d_conv_rate = None

row1 = st.columns(4)
render_kpi(row1[0], "Organic Users", format_number(total_active), d_active, hero=True)
render_kpi(row1[1], "New Users", format_number(total_new), d_new, hero=True)
render_kpi(row1[2], "Returning Users", format_number(total_returning), d_returning, hero=True)
render_kpi(row1[3], "Sessions", format_number(total_sessions), d_sessions, hero=True)

row2 = st.columns(4)
render_kpi(row2[0], "Subscriptions", format_number(subscriptions), d_subs, hero=True)
render_kpi(row2[1], "Conversions (GA4)", format_number(conversions), d_conv, hero=True)
render_kpi(row2[2], "Conversion Rate", f"{conversion_rate:.2f}%", d_conv_rate, hero=True)
render_kpi(row2[3], "Engagement Rate", f"{avg_engagement_rate:.1f}%", d_eng_rate, hero=True)


# ============================================
# SECTION 2: ORGANIC ACQUISITION
# ============================================
st.markdown('<div class="section-header">🌱 Organic Acquisition</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Where organic users come from: Google + Bing search + Direct visits</div>', unsafe_allow_html=True)

col_a, col_b = st.columns([2, 1])

with col_a:
    daily_trend = metrics_wider.groupby('date')[['active_users', 'new_users', 'sessions']].sum().reset_index()
    if not daily_trend.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_trend['date'], y=daily_trend['sessions'], name='Sessions',
            mode='lines', line=dict(color='#60a5fa', width=2.5),
            fill='tozeroy', fillcolor='rgba(96,165,250,0.1)',
        ))
        fig.add_trace(go.Scatter(
            x=daily_trend['date'], y=daily_trend['active_users'], name='Users',
            mode='lines', line=dict(color='#34d399', width=2.5),
        ))
        fig.add_trace(go.Scatter(
            x=daily_trend['date'], y=daily_trend['new_users'], name='New Users',
            mode='lines', line=dict(color='#a78bfa', width=2.5, dash='dot'),
        ))
        fig.update_layout(
            title=dict(text='Daily Organic Traffic Trend', font=dict(color='white', size=16)),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=''),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=''),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(color='white')),
            height=380, margin=dict(l=0, r=0, t=60, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

with col_b:
    # Source breakdown
    source_df = metrics_wider.groupby('source')['active_users'].sum().reset_index()
    source_df = source_df[source_df['active_users'] > 0].sort_values('active_users', ascending=False).head(8)
    if not source_df.empty:
        fig = go.Figure(data=[go.Pie(
            labels=source_df['source'], values=source_df['active_users'], hole=0.55,
            marker=dict(colors=['#34d399', '#60a5fa', '#a78bfa', '#fbbf24', '#f87171', '#06b6d4']),
            textinfo='percent', textfont=dict(color='white', size=12),
        )])
        fig.update_layout(
            title=dict(text='Organic Sources', font=dict(color='white', size=16)),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
            legend=dict(font=dict(color='white', size=11), orientation='v', x=1.05, y=0.5),
            height=380, margin=dict(l=0, r=0, t=60, b=0),
            annotations=[dict(text=f'{format_number(source_df["active_users"].sum())}<br>users', x=0.5, y=0.5, font=dict(size=14, color='white'), showarrow=False)],
        )
        st.plotly_chart(fig, use_container_width=True)

# Strict vs Direct comparison
col_s, col_d = st.columns(2)
strict_users = int(metrics_strict['active_users'].sum())
direct_users = int(metrics_direct['active_users'].sum())

col_s.markdown(f"""
<div class="glass-card" style="border-left: 4px solid #34d399;">
    <div class="kpi-label">🌱 Strict Organic (Google + Bing Search)</div>
    <div class="kpi-value">{format_number(strict_users)}</div>
    <div class="kpi-delta neutral">{int(metrics_strict['new_users'].sum()):,} new users • {int(metrics_strict['sessions'].sum()):,} sessions</div>
</div>
""", unsafe_allow_html=True)

col_d.markdown(f"""
<div class="glass-card" style="border-left: 4px solid #a78bfa;">
    <div class="kpi-label">💎 Direct (Returning Users)</div>
    <div class="kpi-value">{format_number(direct_users)}</div>
    <div class="kpi-delta neutral">{int(metrics_direct['new_users'].sum()):,} new users • {int(metrics_direct['sessions'].sum()):,} sessions</div>
</div>
""", unsafe_allow_html=True)


# ============================================
# SECTION 3: SUBSCRIPTION FUNNEL
# ============================================
st.markdown('<div class="section-header">🔄 Organic Subscription Funnel</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Quiz Start → Conversion (GA4) → Subscription — track the organic conversion path</div>', unsafe_allow_html=True)

# Build funnel
funnel_steps = [
    ("Organic Sessions", total_sessions),
    ("Quiz Starts", quiz_starts),
    ("Conversions", conversions),
    ("Subscriptions", subscriptions),
]
funnel_steps_filtered = [(name, val) for name, val in funnel_steps if val > 0]

if funnel_steps_filtered:
    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        names = [s[0] for s in funnel_steps_filtered]
        values = [s[1] for s in funnel_steps_filtered]
        fig = go.Figure(go.Funnel(
            y=names, x=values,
            textposition="inside", textinfo="value+percent initial",
            marker=dict(color=["#60a5fa", "#a78bfa", "#fbbf24", "#34d399"][:len(funnel_steps_filtered)]),
            connector=dict(line=dict(color="rgba(255,255,255,0.2)", width=1)),
        ))
        fig.update_layout(
            title=dict(text='Organic Conversion Funnel', font=dict(color='white', size=16)),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=14),
            height=440, margin=dict(l=0, r=0, t=60, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col_f2:
        st.markdown("##### Drop-off Rates")
        for i in range(1, len(funnel_steps_filtered)):
            prev_step = funnel_steps_filtered[i-1]
            curr_step = funnel_steps_filtered[i]
            rate = (curr_step[1] / prev_step[1] * 100) if prev_step[1] > 0 else 0
            drop = 100 - rate
            color = "#34d399" if rate > 10 else "#fbbf24" if rate > 1 else "#f87171"
            st.markdown(f"""
            <div class="glass-card" style="padding: 14px; margin-bottom: 8px; border-left: 3px solid {color};">
                <div style="color: rgba(255,255,255,0.7); font-size: 12px;">{prev_step[0]} → {curr_step[0]}</div>
                <div style="color: white; font-size: 20px; font-weight: 700; margin-top: 4px;">{rate:.2f}%</div>
                <div style="color: rgba(255,255,255,0.5); font-size: 11px;">{drop:.1f}% drop-off</div>
            </div>
            """, unsafe_allow_html=True)


# ============================================
# SECTION 4: ENGAGEMENT ANALYTICS
# ============================================
st.markdown('<div class="section-header">📈 Organic Engagement Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">How engaged are your organic visitors</div>', unsafe_allow_html=True)

eng_row = st.columns(4)
render_kpi(eng_row[0], "Avg Session Duration", format_duration(avg_session_duration))
render_kpi(eng_row[1], "Sessions per User", f"{sessions_per_user:.2f}")
render_kpi(eng_row[2], "Engaged Sessions", format_number(total_engaged))
render_kpi(eng_row[3], "Engagement Rate", f"{avg_engagement_rate:.1f}%")

# Daily engagement rate trend
if not metrics_wider.empty:
    daily_eng = metrics_wider.groupby('date').agg(
        engagement_rate=('engagement_rate', 'mean'),
        sessions=('sessions', 'sum'),
        engaged_sessions=('engaged_sessions', 'sum'),
    ).reset_index()
    daily_eng['engagement_rate_pct'] = daily_eng['engagement_rate'] * 100
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_eng['date'], y=daily_eng['engagement_rate_pct'],
        name='Engagement Rate %', mode='lines+markers',
        line=dict(color='#34d399', width=2.5), marker=dict(size=5),
    ))
    fig.update_layout(
        title=dict(text='Daily Engagement Rate Trend', font=dict(color='white', size=16)),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=''),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Engagement Rate (%)', ticksuffix='%'),
        height=320, margin=dict(l=0, r=0, t=60, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================
# SECTION 5: RETENTION
# ============================================
st.markdown('<div class="section-header">🔁 Organic Retention</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">New vs returning users over time</div>', unsafe_allow_html=True)

ret_row = st.columns(3)
returning_pct = (total_returning / total_active * 100) if total_active > 0 else 0
new_pct = (total_new / total_active * 100) if total_active > 0 else 0

render_kpi(ret_row[0], "Returning Users", format_number(total_returning))
render_kpi(ret_row[1], "New Users", format_number(total_new))
render_kpi(ret_row[2], "Returning %", f"{returning_pct:.1f}%")

# Daily new vs returning
if not metrics_wider.empty:
    daily_users = metrics_wider.groupby('date').agg(
        active_users=('active_users', 'sum'),
        new_users=('new_users', 'sum'),
    ).reset_index()
    daily_users['returning'] = daily_users['active_users'] - daily_users['new_users']
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_users['date'], y=daily_users['returning'],
        name='Returning', mode='lines', stackgroup='one',
        line=dict(color='#a78bfa', width=2),
        fillcolor='rgba(167,139,250,0.4)',
    ))
    fig.add_trace(go.Scatter(
        x=daily_users['date'], y=daily_users['new_users'],
        name='New', mode='lines', stackgroup='one',
        line=dict(color='#34d399', width=2),
        fillcolor='rgba(52,211,153,0.4)',
    ))
    fig.update_layout(
        title=dict(text='Daily New vs Returning Users', font=dict(color='white', size=16)),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=''),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=''),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(color='white')),
        height=350, margin=dict(l=0, r=0, t=60, b=0),
    )
    st.plotly_chart(fig, use_container_width=True)


# ============================================
# SECTION 6: COUNTRY GROWTH
# ============================================
st.markdown('<div class="section-header">🌍 Country Growth</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Organic users by country — Italy is your largest market</div>', unsafe_allow_html=True)

if not countries_wider.empty:
    country_summary = countries_wider.groupby('country').agg(
        active_users=('active_users', 'sum'),
        new_users=('new_users', 'sum'),
        sessions=('sessions', 'sum'),
    ).reset_index()
    country_summary = country_summary[country_summary['country'] != '(unknown)']
    country_summary = country_summary[country_summary['active_users'] > 0]
    
    col1, col2 = st.columns([3, 2])
    with col1:
        if not country_summary.empty:
            fig = px.choropleth(
                country_summary, locations='country', locationmode='country names',
                color='active_users', hover_name='country',
                hover_data={'active_users': True, 'new_users': True, 'sessions': True},
                color_continuous_scale=['#1e3a8a', '#3b82f6', '#60a5fa', '#34d399'],
                labels={'active_users': 'Organic Users'},
            )
            fig.update_layout(
                title=dict(text='Organic Users by Country', font=dict(color='white', size=16)),
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
                geo=dict(showframe=False, showcoastlines=True, coastlinecolor='rgba(255,255,255,0.2)',
                    bgcolor='rgba(0,0,0,0)', landcolor='rgba(255,255,255,0.05)',
                    showocean=True, oceancolor='rgba(0,0,0,0)'),
                height=500, margin=dict(l=0, r=0, t=60, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        top_countries = country_summary.sort_values('active_users', ascending=False).head(15).copy()
        top_countries['Users'] = top_countries['active_users'].apply(format_number)
        top_countries['New'] = top_countries['new_users'].apply(format_number)
        top_countries['Sessions'] = top_countries['sessions'].apply(format_number)
        display_tc = top_countries[['country', 'Users', 'New', 'Sessions']]
        display_tc.columns = ['Country', 'Users', 'New', 'Sessions']
        st.markdown("##### Top 15 Countries")
        st.dataframe(display_tc, hide_index=True, use_container_width=True, height=500)


# ============================================
# SECTION 7: LANDING PAGE INTELLIGENCE
# ============================================
st.markdown('<div class="section-header">📄 Top Organic Landing Pages</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Pages that bring in the most organic traffic</div>', unsafe_allow_html=True)

if not landing_wider.empty:
    # Clean landing pages: exclude (not set) and URLs with query parameters
    cleaned_landing = landing_wider.copy()
    cleaned_landing = cleaned_landing[cleaned_landing['landing_page'] != '(not set)']
    cleaned_landing = cleaned_landing[~cleaned_landing['landing_page'].str.contains(r'\?|&', regex=True, na=False)]
    
    page_summary = cleaned_landing.groupby('landing_page').agg(
        sessions=('sessions', 'sum'),
        active_users=('active_users', 'sum'),
        engaged_sessions=('engaged_sessions', 'sum'),
        bounce_rate=('bounce_rate', 'mean'),
    ).reset_index()
    page_summary = page_summary[page_summary['sessions'] > 0]
    page_summary['engagement_rate'] = (page_summary['engaged_sessions'] / page_summary['sessions'] * 100).fillna(0)
    page_summary = page_summary.sort_values('sessions', ascending=False).head(20)
    
    if not page_summary.empty:
        page_summary['Sessions'] = page_summary['sessions'].apply(format_number)
        page_summary['Users'] = page_summary['active_users'].apply(format_number)
        page_summary['Engagement %'] = page_summary['engagement_rate'].apply(lambda x: f"{x:.1f}%")
        page_summary['Bounce %'] = page_summary['bounce_rate'].apply(lambda x: f"{x*100:.1f}%")
        
        display_pages = page_summary[['landing_page', 'Sessions', 'Users', 'Engagement %', 'Bounce %']]
        display_pages.columns = ['Landing Page', 'Sessions', 'Users', 'Engagement %', 'Bounce %']
        
        st.dataframe(display_pages, hide_index=True, use_container_width=True, height=600,
                     column_config={
                         "Landing Page": st.column_config.TextColumn(width="large"),
                     })
        st.caption("ℹ️ Landing pages with URL parameters (e.g. ?coupon_code=) excluded for clarity. "
                   "(not set) entries also filtered out.")
    else:
        st.info("No clean landing pages in selected range.")


# ============================================
# SECTION 8: CONVERSION DETAILS
# ============================================
st.markdown('<div class="section-header">🎯 Conversion & Subscription Details</div>', unsafe_allow_html=True)
st.markdown('<div class="section-subtitle">Detailed conversion event breakdown</div>', unsafe_allow_html=True)

# Event KPI cards
ev_row = st.columns(4)
render_kpi(ev_row[0], "Quiz Starts", format_number(quiz_starts))
render_kpi(ev_row[1], "Sign-up Clicks", format_number(sign_ups))
render_kpi(ev_row[2], "Trial Starts", format_number(trials))
render_kpi(ev_row[3], "Subscriptions", format_number(subscriptions))

# Daily conversion events trend
if not events_wider.empty:
    important_events = ['quiz_start', 'ga4convavanzate', 'subscription', 'webapp_successful_payment']
    daily_events = events_wider[events_wider['event_name'].isin(important_events)].copy()
    if not daily_events.empty:
        daily_events_summary = daily_events.groupby(['date', 'event_name'])['event_count'].sum().reset_index()
        fig = px.line(
            daily_events_summary, x='date', y='event_count', color='event_name',
            color_discrete_map={
                'quiz_start': '#60a5fa',
                'ga4convavanzate': '#fbbf24',
                'subscription': '#34d399',
                'webapp_successful_payment': '#a78bfa',
            },
            markers=True,
        )
        fig.update_traces(line=dict(width=2), marker=dict(size=5))
        fig.update_layout(
            title=dict(text='Daily Conversion Events Trend', font=dict(color='white', size=16)),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'),
            xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=''),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Event Count'),
            legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, font=dict(color='white'), title=''),
            height=380, margin=dict(l=0, r=0, t=60, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)



