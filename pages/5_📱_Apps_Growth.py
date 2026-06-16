"""📱 Apps Growth Dashboard — NEW Installs

GA4 UI VERIFIED NUMBERS (28 days):
   🤖 Android Organic: 1,656 (Play Store 1,626 + Google 30)
   🍎 iOS Total New: 5,530
   📊 Combined: 7,186

UPDATE WEEKLY:
   1. GA4 → Reports → Acquisition → User acquisition
   2. Filter Platform = Android, get google-play/organic and google/organic
   3. Filter Platform = iOS, get total new users
   4. Update GA4_UI_NUMBERS below
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta, datetime

# ============================================
# 📌 GA4 UI VERIFIED NUMBERS (UPDATE WEEKLY)
# ============================================

GA4_UI_NUMBERS = {
    "period_days": 28,
    "end_date": "2026-05-17",
    "start_date": "2026-04-19",
    
    # Android - from GA4 UI with Platform=Android filter
    "android_play_store_organic": 1626,  # google-play / organic
    "android_google_organic": 30,         # google / organic
    "android_total_new": 2569,            # All sources combined
    
    # iOS - from GA4 UI with Platform=iOS filter  
    "ios_total_new": 5530,                # All sources (ATT blocks attribution)
    
    "last_verified": "2026-05-17",
}

GA4_UI_NUMBERS["android_total_organic"] = (
    GA4_UI_NUMBERS["android_play_store_organic"] + 
    GA4_UI_NUMBERS["android_google_organic"]
)
GA4_UI_NUMBERS["total_new_installs"] = (
    GA4_UI_NUMBERS["android_total_organic"] +
    GA4_UI_NUMBERS["ios_total_new"]
)

# ============================================
# PAGE CONFIG
# ============================================

st.set_page_config(
    page_title="Apps Growth - New Installs",
    page_icon="📱",
    layout="wide",
)

st.title("📱 Apps Growth - New Installs")
st.caption(
    f"Period: {GA4_UI_NUMBERS['start_date']} to {GA4_UI_NUMBERS['end_date']} "
    f"({GA4_UI_NUMBERS['period_days']} days)"
)

st.divider()

# ============================================
# SECTION 1: TOTAL NEW INSTALLS
# ============================================

st.header("📊 Total New Installs (iOS + Android)")
st.caption(
    f"Combined new app installs across both platforms over {GA4_UI_NUMBERS['period_days']} days."
)

total = GA4_UI_NUMBERS["total_new_installs"]
android_org = GA4_UI_NUMBERS["android_total_organic"]
ios_new = GA4_UI_NUMBERS["ios_total_new"]
daily_avg = total / GA4_UI_NUMBERS["period_days"]

kpi1, kpi2, kpi3 = st.columns(3)
with kpi1:
    st.metric(
        "📊 Total New Installs",
        f"{total:,}",
        help=f"Android organic ({android_org}) + iOS total ({ios_new})",
    )
    st.caption("Combined platforms")

with kpi2:
    st.metric(
        "📈 Daily Average",
        f"{daily_avg:.1f}",
        help=f"Average new installs per day",
    )
    st.caption(f"Per day over {GA4_UI_NUMBERS['period_days']} days")

with kpi3:
    weekly_rate = daily_avg * 7
    st.metric(
        "📅 Weekly Rate",
        f"{weekly_rate:,.0f}",
        help="New installs per week (estimated)",
    )
    st.caption("Average weekly")

# Pie chart showing platform breakdown
fig_pie = go.Figure(
    data=[
        go.Pie(
            labels=["🤖 Android Organic", "🍎 iOS Total New"],
            values=[android_org, ios_new],
            hole=0.5,
            marker=dict(colors=["#34D399", "#60A5FA"]),
            textinfo="label+percent+value",
            textposition="outside",
            hovertemplate="<b>%{label}</b><br>Installs: %{value:,}<br>Share: %{percent}<extra></extra>",
        )
    ]
)
fig_pie.update_layout(
    title=dict(
        text="Platform Distribution",
        font=dict(size=18),
        x=0.5,
    ),
    height=400,
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    showlegend=False,
    margin=dict(l=20, r=20, t=60, b=20),
)
st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ============================================
# SECTION 2: ANDROID NEW ORGANIC
# ============================================

st.header("🤖 Android NEW ORGANIC Installs")
st.caption(
    f"GA4-verified organic installs over {GA4_UI_NUMBERS['period_days']} days."
)

play_store = GA4_UI_NUMBERS["android_play_store_organic"]
google_web = GA4_UI_NUMBERS["android_google_organic"]
android_total_org = GA4_UI_NUMBERS["android_total_organic"]

a_kpi1, a_kpi2, a_kpi3 = st.columns(3)
with a_kpi1:
    st.metric(
        "🤖 Android Organic",
        f"{android_total_org:,}",
        help="GA4 verified NEW Android organic users",
    )
    st.caption("Total organic")

with a_kpi2:
    st.metric(
        "🎯 Play Store ASO",
        f"{play_store:,}",
        help="google-play / organic - direct Play Store search discovery",
    )
    pct_play = (play_store / android_total_org * 100) if android_total_org > 0 else 0
    st.caption(f"{pct_play:.0f}% of Android organic")

with a_kpi3:
    st.metric(
        "🌐 Google Web Search",
        f"{google_web:,}",
        help="google / organic - Google search → Play Store",
    )
    pct_google = (google_web / android_total_org * 100) if android_total_org > 0 else 0
    st.caption(f"{pct_google:.0f}% of Android organic")

# Android source breakdown chart
fig_android = go.Figure(
    data=[
        go.Bar(
            x=["🎯 Play Store ASO", "🌐 Google Web Search"],
            y=[play_store, google_web],
            marker=dict(color=["#34D399", "#60A5FA"]),
            text=[f"{play_store:,}", f"{google_web:,}"],
            textposition="auto",
            hovertemplate="<b>%{x}</b><br>Installs: %{y:,}<extra></extra>",
        )
    ]
)
fig_android.update_layout(
    title=dict(
        text=f"🤖 Android Organic Sources — {GA4_UI_NUMBERS['period_days']} Days",
        font=dict(size=18),
    ),
    height=400,
    xaxis=dict(title=""),
    yaxis=dict(title="New Organic Installs"),
    plot_bgcolor="rgba(0, 0, 0, 0)",
    paper_bgcolor="rgba(0, 0, 0, 0)",
    margin=dict(l=40, r=20, t=60, b=20),
)
st.plotly_chart(fig_android, use_container_width=True)

st.divider()

# ============================================
# SECTION 3: iOS TOTAL NEW INSTALLS
# ============================================

st.header("🍎 iOS Total NEW Installs")
st.caption(
    f"All new iOS installs over {GA4_UI_NUMBERS['period_days']} days "
    f"(source attribution limited by Apple ATT)."
)

ios_daily_avg = ios_new / GA4_UI_NUMBERS["period_days"]

i_kpi1, i_kpi2, i_kpi3 = st.columns(3)
with i_kpi1:
    st.metric(
        "🍎 iOS Total NEW Installs",
        f"{ios_new:,}",
        help="All new iOS installs (sources blocked by Apple ATT)",
    )
    st.caption("All sources combined")

with i_kpi2:
    st.metric(
        "📈 Daily Average",
        f"{ios_daily_avg:.1f}",
        help="Average iOS new installs per day",
    )
    st.caption(f"Per day over {GA4_UI_NUMBERS['period_days']} days")

with i_kpi3:
    ios_weekly = ios_daily_avg * 7
    st.metric(
        "📅 Weekly Rate",
        f"{ios_weekly:,.0f}",
        help="iOS new installs per week (estimated)",
    )
    st.caption("Average weekly")

st.warning(
    "⚠️ **Why iOS shows TOTAL (not organic):** "
    "Apple's App Tracking Transparency (ATT) framework prevents GA4 from tracking "
    "acquisition sources for most iOS users. This number represents ALL new iOS installs "
    "(organic, paid, direct combined). Industry-wide iOS attribution problem since iOS 14.5."
)
