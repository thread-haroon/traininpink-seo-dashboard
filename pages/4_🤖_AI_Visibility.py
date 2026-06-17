"""AI Visibility Dashboard - Track GEO (Generative Engine Optimization) performance.
FIXED: Date picker UX + dark calendar popup styling.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.data_loader import load_ga4_ai_data, load_ga4_ai_summary, load_ga4_top_pages

st.set_page_config(
    page_title="AI Visibility | SEO Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium CSS styling with FIXED date picker
st.markdown("""
<style>
    /* Hide Streamlit branding AND deploy button AND header */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    .stDeployButton {display: none !important;}
    
    /* Reduce top padding */
    .block-container {
        padding-top: 1rem !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    /* Page title */
    .page-title {
        font-size: 36px;
        font-weight: 800;
        color: white;
        margin: 0 0 16px 0;
        background: linear-gradient(135deg, #fff 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Date range info bar at top */
    .date-info-bar {
        background: linear-gradient(135deg, rgba(167,139,250,0.15) 0%, rgba(139,92,246,0.05) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(167,139,250,0.3);
        border-radius: 12px;
        padding: 14px 20px;
        margin-bottom: 24px;
        color: white;
        font-size: 14px;
        font-weight: 500;
    }
    
    .date-info-bar strong {
        color: #c4b5fd;
        font-weight: 700;
    }
    
    .glass-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 20px;
        padding: 24px;
        margin-bottom: 16px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.3);
    }
    
    .kpi-label {
        color: rgba(255,255,255,0.6);
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    
    .kpi-value {
        color: white;
        font-size: 36px;
        font-weight: 800;
        margin: 0;
    }
    
    .kpi-delta {
        font-size: 13px;
        font-weight: 600;
        margin-top: 8px;
    }
    
    .kpi-delta.positive { color: #34d399; }
    .kpi-delta.negative { color: #f87171; }
    .kpi-delta.neutral { color: rgba(255,255,255,0.5); }
    
    .section-header {
        color: white;
        font-size: 22px;
        font-weight: 700;
        margin: 32px 0 16px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .stMarkdown { color: white; }
    h1, h2, h3, h4, h5, h6 { color: white !important; }
    
    /* === SIDEBAR === */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1538 0%, #2d2752 100%) !important;
    }
    
    section[data-testid="stSidebar"] * {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: white !important;
        font-weight: 700 !important;
    }
    
    section[data-testid="stSidebar"] label {
        color: rgba(255,255,255,0.85) !important;
        font-weight: 600 !important;
    }
    
    /* Sidebar selectbox styling - DARK background, WHITE text */
    section[data-testid="stSidebar"] [data-baseweb="select"] {
        background-color: rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
    }
    
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: transparent !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }
    
    section[data-testid="stSidebar"] [data-baseweb="select"] input {
        color: white !important;
    }
    
    section[data-testid="stSidebar"] [data-baseweb="select"] svg {
        fill: white !important;
    }
    
    /* Selectbox dropdown items */
    [data-baseweb="popover"] [role="option"] {
        color: #1a1538 !important;
        background-color: white !important;
    }
    
    [data-baseweb="popover"] [role="option"]:hover {
        background-color: #ede9fe !important;
    }
    
    /* Sidebar caption text */
    section[data-testid="stSidebar"] .stCaption {
        color: rgba(255,255,255,0.7) !important;
    }
    
    /* Sidebar links (page navigation) */
    section[data-testid="stSidebar"] a {
        color: rgba(255,255,255,0.85) !important;
        font-weight: 500 !important;
    }
    
    section[data-testid="stSidebar"] a:hover {
        color: #c4b5fd !important;
    }
    
    /* Sidebar horizontal rule */
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.15) !important;
    }
    
    /* ==================================== */
    /* 🎨 FIXED DATE INPUT STYLING          */
    /* ==================================== */
    
    /* Date input field in sidebar - DARK theme */
    section[data-testid="stSidebar"] [data-testid="stDateInput"] {
        background-color: transparent !important;
    }
    
    section[data-testid="stSidebar"] [data-testid="stDateInput"] > div {
        background-color: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
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
    
    /* Date input calendar icon */
    section[data-testid="stSidebar"] [data-testid="stDateInput"] svg {
        fill: rgba(255,255,255,0.7) !important;
    }
    
    /* Date input focus state */
    section[data-testid="stSidebar"] [data-testid="stDateInput"] > div:focus-within {
        border-color: #a78bfa !important;
        box-shadow: 0 0 0 2px rgba(167,139,250,0.2) !important;
    }
    
    /* ==================================== */
    /* 🗓️ CALENDAR POPUP - DARK THEME       */
    /* ==================================== */
    
    /* Calendar popup container */
    [data-baseweb="calendar"],
    [data-baseweb="datepicker"] {
        background-color: #1a1538 !important;
        color: white !important;
        border: 1px solid rgba(167,139,250,0.3) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px rgba(0,0,0,0.5) !important;
    }
    
    /* All calendar text */
    [data-baseweb="calendar"] * {
        color: white !important;
        border-color: rgba(255,255,255,0.1) !important;
    }
    
    /* Calendar headers (Mon, Tue, etc.) */
    [data-baseweb="calendar"] [role="presentation"] {
        color: rgba(255,255,255,0.5) !important;
        background-color: transparent !important;
    }
    
    /* Calendar day buttons */
    [data-baseweb="calendar"] [role="gridcell"] button,
    [data-baseweb="calendar"] [role="button"] {
        color: white !important;
        background-color: transparent !important;
        border-radius: 6px !important;
        transition: background-color 0.2s !important;
    }
    
    /* Hover state on day buttons */
    [data-baseweb="calendar"] [role="gridcell"] button:hover {
        background-color: rgba(167,139,250,0.3) !important;
        color: white !important;
    }
    
    /* Selected date */
    [data-baseweb="calendar"] [aria-selected="true"],
    [data-baseweb="calendar"] [aria-pressed="true"] {
        background-color: #a78bfa !important;
        color: white !important;
        font-weight: 700 !important;
    }
    
    /* Today indicator */
    [data-baseweb="calendar"] [aria-current="date"] {
        background-color: rgba(167,139,250,0.2) !important;
        color: #c4b5fd !important;
        border: 1px solid #a78bfa !important;
    }
    
    /* Disabled dates (outside min/max) */
    [data-baseweb="calendar"] [aria-disabled="true"] {
        color: rgba(255,255,255,0.2) !important;
        background-color: transparent !important;
    }
    
    /* Range selection (between start and end) */
    [data-baseweb="calendar"] [data-range-end="true"],
    [data-baseweb="calendar"] [data-range-start="true"] {
        background-color: #a78bfa !important;
        color: white !important;
    }
    
    [data-baseweb="calendar"] [data-range="true"] {
        background-color: rgba(167,139,250,0.25) !important;
        color: white !important;
    }
    
    /* Month/year header */
    [data-baseweb="calendar"] [role="heading"] {
        color: white !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }
    
    /* Navigation arrows (prev/next month) */
    [data-baseweb="calendar"] button[aria-label*="Previous"],
    [data-baseweb="calendar"] button[aria-label*="Next"] {
        background-color: transparent !important;
        color: white !important;
        border-radius: 6px !important;
    }
    
    [data-baseweb="calendar"] button[aria-label*="Previous"]:hover,
    [data-baseweb="calendar"] button[aria-label*="Next"]:hover {
        background-color: rgba(167,139,250,0.3) !important;
    }
    
    /* Navigation arrow SVG */
    [data-baseweb="calendar"] button svg {
        fill: white !important;
    }
    
    /* Month/year dropdown selectors in calendar */
    [data-baseweb="calendar"] select,
    [data-baseweb="calendar"] [role="combobox"] {
        background-color: rgba(255,255,255,0.1) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }
    
    /* Center align dataframe content */
    [data-testid="stDataFrame"] [role="cell"],
    [data-testid="stDataFrame"] [role="columnheader"] {
        text-align: center !important;
        justify-content: center !important;
    }
</style>
""", unsafe_allow_html=True)

# === LOAD DATA ===
try:
    full_data_all = load_ga4_ai_data()
except Exception as e:
    st.error(f"Failed to load data: {e}")
    st.stop()

if full_data_all.empty:
    st.warning("No AI traffic data available yet.")
    st.stop()

min_data_date = full_data_all['date'].min().date()
max_data_date = full_data_all['date'].max().date()


def get_date_range(option, anchor_date, custom_dates=None):
    """Calculate start/end dates based on option."""
    if option == "Last 7 days":
        return anchor_date - timedelta(days=7), anchor_date
    elif option == "Last 30 days":
        return anchor_date - timedelta(days=30), anchor_date
    elif option == "Last 90 days":
        return anchor_date - timedelta(days=90), anchor_date
    elif option == "Last 6 months":
        return anchor_date - timedelta(days=180), anchor_date
    elif option == "Last 12 months":
        return anchor_date - timedelta(days=365), anchor_date
    elif option == "All time":
        return min_data_date, anchor_date
    elif option == "Custom range" and custom_dates:
        if isinstance(custom_dates, tuple) and len(custom_dates) == 2:
            return custom_dates[0], custom_dates[1]
    return anchor_date - timedelta(days=30), anchor_date


# === SIDEBAR FILTERS ===
with st.sidebar:
    st.markdown("### 🌐 Website")
    st.selectbox(
        "Website",
        options=["https://www.traininpink.net/"],
        index=0,
        label_visibility="collapsed",
        key="website_select",
    )
    
    st.markdown("---")
    
    st.markdown("### 📅 Date Range")
    date_range_option = st.selectbox(
        "Select range",
        options=[
            "Last 7 days",
            "Last 30 days",
            "Last 90 days",
            "Last 6 months",
            "Last 12 months",
            "All time",
            "Custom range",
        ],
        index=4,  # Default: Last 12 months
        label_visibility="collapsed",
        key="date_range_select",
    )
    
    today = date.today()
    custom_dates = None
    
    # Show custom date picker if selected
    if date_range_option == "Custom range":
        custom_dates = st.date_input(
            "Pick dates",
            value=(today - timedelta(days=30), today),
            min_value=min_data_date,
            max_value=today,
            key="custom_dates",
        )
    
    # Calculate actual dates
    start_date, end_date = get_date_range(date_range_option, today, custom_dates)
    period_days = (end_date - start_date).days
    
    st.caption(f"📊 {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')} ({period_days} days)")
    
    st.markdown("---")
    
    # ============================================
    # COMPARISON DROPDOWN - 4 clean options
    # ============================================
    st.markdown("### ⚖️ Comparison")
    comparison_option = st.selectbox(
        "Compare against",
        options=[
            "Previous period",
            "Previous year",
            "Custom range",
            "No comparison",
        ],
        index=0,  # Default: Previous period
        label_visibility="collapsed",
        key="comparison_select",
        help="Previous period: same length ending day before main period. Previous year: same dates one year ago."
    )
    
    custom_compare_dates = None
    
    if comparison_option == "Custom range":
        default_compare_end = start_date - timedelta(days=1)
        default_compare_start = default_compare_end - timedelta(days=period_days)
        
        custom_compare_dates = st.date_input(
            "Pick comparison dates",
            value=(default_compare_start, default_compare_end),
            min_value=min_data_date,
            max_value=today,
            key="custom_compare_dates",
        )
    
    # Calculate comparison range
    if comparison_option == "Previous period":
        compare_end = start_date - timedelta(days=1)
        compare_start = compare_end - timedelta(days=period_days)
    elif comparison_option == "Previous year":
        compare_start = start_date - timedelta(days=365)
        compare_end = end_date - timedelta(days=365)
    elif comparison_option == "Custom range" and custom_compare_dates:
        if isinstance(custom_compare_dates, tuple) and len(custom_compare_dates) == 2:
            compare_start = custom_compare_dates[0]
            compare_end = custom_compare_dates[1]
        else:
            compare_start = None
            compare_end = None
    else:  # No comparison
        compare_start = None
        compare_end = None
    
    if compare_start and compare_end:
        compare_days = (compare_end - compare_start).days
        st.caption(f"⚖️ {compare_start.strftime('%Y-%m-%d')} → {compare_end.strftime('%Y-%m-%d')} ({compare_days} days)")

# === MAIN PAGE TITLE ===
st.markdown('<div class="page-title">🤖 AI Visibility</div>', unsafe_allow_html=True)

# === DATE INFO BAR ===
date_info = f"📅 <strong>Showing:</strong> {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')} ({period_days} days)"
if compare_start and compare_end:
    date_info += f" • ⚖️ <strong>Compared to:</strong> {compare_start.strftime('%Y-%m-%d')} → {compare_end.strftime('%Y-%m-%d')} ({comparison_option})"

st.markdown(f"""
<div class="date-info-bar">
    {date_info}
</div>
""", unsafe_allow_html=True)

# === FILTER DATA ===
mask = (full_data_all['date'].dt.date >= start_date) & (full_data_all['date'].dt.date <= end_date)
filtered_data_all = full_data_all[mask].copy()
filtered_data = filtered_data_all[filtered_data_all['sessions'] > 0].copy()
filtered_pages = filtered_data_all[filtered_data_all['page_path'] != ''].copy()

if compare_start and compare_end:
    compare_mask = (full_data_all['date'].dt.date >= compare_start) & (full_data_all['date'].dt.date <= compare_end)
    compare_data = full_data_all[compare_mask].copy()
else:
    compare_data = pd.DataFrame()

if filtered_data.empty:
    st.markdown(f"""
    <div class="glass-card" style="text-align: center; padding: 40px;">
        <div style="font-size: 48px; margin-bottom: 16px;">🤖</div>
        <h3 style="color: white; margin-bottom: 8px;">No AI Traffic in Selected Range</h3>
        <p style="color: rgba(255,255,255,0.7); margin-bottom: 16px;">
            No AI assistants (ChatGPT, Perplexity, etc.) sent visitors to your site between<br>
            <strong style="color: #c4b5fd;">{start_date.strftime('%B %d, %Y')} → {end_date.strftime('%B %d, %Y')}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# === AI PERFORMANCE OVERVIEW ===
st.markdown('<div class="section-header">📊 AI Performance Overview</div>', unsafe_allow_html=True)

total_sessions = int(filtered_data['sessions'].sum())
total_users = int(filtered_data['total_users'].sum())
total_engaged = int(filtered_data['engaged_sessions'].sum())

platform_summary = filtered_data.groupby('ai_platform').agg(
    sessions=('sessions', 'sum'),
).reset_index().sort_values('sessions', ascending=False)

if not platform_summary.empty:
    top_platform = platform_summary.iloc[0]['ai_platform']
    top_platform_sessions = int(platform_summary.iloc[0]['sessions'])
    top_platform_share = (top_platform_sessions / total_sessions * 100) if total_sessions > 0 else 0
else:
    top_platform = "N/A"
    top_platform_share = 0

if not compare_data.empty:
    compare_sessions = int(compare_data['sessions'].sum())
    compare_users = int(compare_data['total_users'].sum())
    compare_engaged = int(compare_data['engaged_sessions'].sum())
    
    sessions_delta_pct = ((total_sessions - compare_sessions) / compare_sessions * 100) if compare_sessions > 0 else (100 if total_sessions > 0 else 0)
    users_delta_pct = ((total_users - compare_users) / compare_users * 100) if compare_users > 0 else (100 if total_users > 0 else 0)
    engaged_delta_pct = ((total_engaged - compare_engaged) / compare_engaged * 100) if compare_engaged > 0 else (100 if total_engaged > 0 else 0)
else:
    sessions_delta_pct = None
    users_delta_pct = None
    engaged_delta_pct = None


def render_kpi(col, label, value, delta_pct, value_format="number"):
    if value_format == "number":
        value_str = f"{value:,}"
    elif value_format == "percent":
        value_str = f"{value:.0f}%"
    else:
        value_str = str(value)
    
    if delta_pct is not None:
        if delta_pct > 0:
            delta_class = "positive"
            arrow = "↑"
        elif delta_pct < 0:
            delta_class = "negative"
            arrow = "↓"
        else:
            delta_class = "neutral"
            arrow = "→"
        delta_html = f'<div class="kpi-delta {delta_class}">{arrow} {abs(delta_pct):.1f}% vs previous</div>'
    else:
        delta_html = ''
    
    col.markdown(f"""
    <div class="glass-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value_str}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


col1, col2, col3, col4 = st.columns(4)

render_kpi(col1, "Total AI Sessions", total_sessions, sessions_delta_pct)
render_kpi(col2, "Total AI Users", total_users, users_delta_pct)

engagement_rate = (total_engaged / total_sessions * 100) if total_sessions > 0 else 0
col3.markdown(f"""
<div class="glass-card">
    <div class="kpi-label">Top AI Source</div>
    <div class="kpi-value">{top_platform}</div>
    <div class="kpi-delta neutral">{top_platform_share:.0f}% of AI traffic</div>
</div>
""", unsafe_allow_html=True)

render_kpi(col4, "Engagement Rate", engagement_rate, engaged_delta_pct, value_format="percent")

# === SESSIONS BY AI PLATFORM ===
st.markdown('<div class="section-header">🎯 Sessions by AI Platform</div>', unsafe_allow_html=True)

platform_full = filtered_data.groupby('ai_platform').agg(
    total_sessions=('sessions', 'sum'),
    total_users=('total_users', 'sum'),
    total_engaged=('engaged_sessions', 'sum'),
).reset_index().sort_values('total_sessions', ascending=False)

platform_full['engagement_rate'] = (platform_full['total_engaged'] / platform_full['total_sessions']).fillna(0)

col_chart, col_table = st.columns([3, 2])

with col_chart:
    fig = px.bar(
        platform_full.sort_values('total_sessions', ascending=True),
        x='total_sessions',
        y='ai_platform',
        orientation='h',
        text='total_sessions',
        color='total_sessions',
        color_continuous_scale=['#a78bfa', '#8b5cf6', '#7c3aed'],
    )
    fig.update_traces(textposition='outside', textfont=dict(color='white', size=14))
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white', family='-apple-system, sans-serif'),
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title=''),
        yaxis=dict(title='', showgrid=False),
        showlegend=False,
        height=320,
        margin=dict(l=0, r=0, t=20, b=0),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    display_df = platform_full[['ai_platform', 'total_sessions', 'total_users', 'engagement_rate']].copy()
    display_df.columns = ['Platform', 'Sessions', 'Users', 'Engagement']
    display_df['Engagement'] = (display_df['Engagement'] * 100).round(0).astype(int).astype(str) + '%'
    
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        height=320,
    )

# === MONTHLY AI TRAFFIC TREND ===
st.markdown('<div class="section-header">📈 Monthly AI Traffic Trend</div>', unsafe_allow_html=True)

if not filtered_data.empty:
    monthly_data = filtered_data.copy()
    monthly_data['month'] = monthly_data['date'].dt.to_period('M').dt.to_timestamp()
    monthly_trend = monthly_data.groupby(['month', 'ai_platform'])['sessions'].sum().reset_index()
    
    all_months = pd.date_range(
        start=pd.Timestamp(start_date).to_period('M').to_timestamp(),
        end=pd.Timestamp(end_date).to_period('M').to_timestamp(),
        freq='MS',
    )
    
    all_platforms = monthly_trend['ai_platform'].unique() if not monthly_trend.empty else []
    
    if len(all_platforms) > 0:
        complete_grid = pd.MultiIndex.from_product(
            [all_months, all_platforms],
            names=['month', 'ai_platform']
        ).to_frame(index=False)
        
        monthly_complete = complete_grid.merge(
            monthly_trend,
            on=['month', 'ai_platform'],
            how='left'
        ).fillna({'sessions': 0})
        
        fig = px.bar(
            monthly_complete,
            x='month',
            y='sessions',
            color='ai_platform',
            barmode='group',
            color_discrete_map={
                'ChatGPT': '#10a37f',
                'Perplexity': '#20a8d8',
                'Claude': '#d97757',
                'Gemini': '#4285f4',
                'Copilot': '#0078d4',
                'Bing Chat': '#008373',
            },
        )
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(
                showgrid=True,
                gridcolor='rgba(255,255,255,0.1)',
                title='',
                tickformat='%b %Y',
                dtick='M1',
                tickangle=-45,
            ),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)', title='Sessions'),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(color='white'),
                title='',
            ),
            height=400,
            margin=dict(l=0, r=0, t=40, b=60),
            bargap=0.2,
            bargroupgap=0.1,
        )
        st.plotly_chart(fig, use_container_width=True)

# === TOP PAGES GETTING AI TRAFFIC ===
st.markdown('<div class="section-header">🔝 Top Pages Getting AI Traffic</div>', unsafe_allow_html=True)

top_pages_filtered = filtered_pages.groupby(['page_path', 'ai_platform']).agg(
    total_sessions=('total_users', 'sum'),
    total_users=('total_users', 'sum'),
    avg_engagement=('engagement_rate', 'mean'),
).reset_index().sort_values('total_sessions', ascending=False).head(15)

if not top_pages_filtered.empty:
    pages_display = top_pages_filtered.copy()
    pages_display.columns = ['Page Path', 'AI Platform', 'Sessions', 'Users', 'Engagement']
    pages_display['Engagement'] = (pages_display['Engagement'] * 100).round(0).astype(int).astype(str) + '%'
    
    st.dataframe(
        pages_display,
        hide_index=True,
        use_container_width=True,
        height=400,
        column_config={
            "Page Path": st.column_config.TextColumn("Page Path", width="large"),
            "AI Platform": st.column_config.TextColumn("AI Platform", width="small"),
            "Sessions": st.column_config.NumberColumn("Sessions", format="%d", width="small"),
            "Users": st.column_config.NumberColumn("Users", format="%d", width="small"),
            "Engagement": st.column_config.TextColumn("Engagement", width="small"),
        },
    )
else:
    st.info("No page data available for the selected date range.")

# === FOOTER ===
st.markdown("---")
st.caption(f"Data: GA4 (Website + Mobile App) | Updated daily at 6 AM UTC | AI sources: ChatGPT, Perplexity, Claude, Gemini, Copilot, Bing Chat, Pi, Poe, Character.AI, Grok, DeepSeek, Mistral, Hugging Face, and more")
