"""Plotly chart components for the dashboard."""

from typing import Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


PRIMARY_COLOR = "#FF4B8B"
SECONDARY_COLOR = "#7B68EE"
COMPARISON_COLOR = "#999999"
GRID_COLOR = "rgba(255, 255, 255, 0.1)"


def _get_yaxis_format(metric):
    """Return appropriate Y-axis format for each metric type."""
    if metric == "ctr":
        return {"tickformat": ".1%", "title": "CTR (%)"}
    elif metric == "position":
        return {"tickformat": ".1f", "title": "Position"}
    else:
        return {"tickformat": ",.0f", "title": metric.title()}


def _get_hover_format(metric):
    """Return appropriate hover format for each metric."""
    if metric == "ctr":
        return ":.2%"
    elif metric == "position":
        return ":.1f"
    else:
        return ":,.0f"


def render_time_series_chart(current_df, metric="clicks", title=None, previous_df=None,
                              comparison_label="Previous period", height=400):
    """Render a time series line chart with optional comparison overlay."""
    if current_df.empty:
        st.info("No data available for this date range.")
        return

    yaxis_format = _get_yaxis_format(metric)
    hover_fmt = _get_hover_format(metric)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=current_df["date"],
        y=current_df[metric],
        mode="lines+markers",
        name="Current",
        line=dict(color=PRIMARY_COLOR, width=3),
        marker=dict(size=6),
        fill="tozeroy",
        fillcolor="rgba(255, 75, 139, 0.1)",
        hovertemplate="<b>%{x|%b %d, %Y}</b><br>" + metric.title() + ": %{y" + hover_fmt + "}<extra></extra>",
    ))

    if previous_df is not None and not previous_df.empty:
        date_diff = current_df["date"].iloc[0] - previous_df["date"].iloc[0]
        previous_aligned = previous_df.copy()
        previous_aligned["display_date"] = previous_aligned["date"] + date_diff

        fig.add_trace(go.Scatter(
            x=previous_aligned["display_date"],
            y=previous_aligned[metric],
            mode="lines",
            name=comparison_label,
            line=dict(color=COMPARISON_COLOR, width=2, dash="dot"),
            hovertemplate="<b>%{customdata|%b %d, %Y}</b><br>" + metric.title() + ": %{y" + hover_fmt + "}<extra></extra>",
            customdata=previous_aligned["date"],
        ))

    # Constrain X-axis to current data range only (no empty space at end)
    fig.update_layout(
        title=title or "Daily " + metric.title() + " Trend",
        xaxis_title="Date",
        yaxis_title=yaxis_format["title"],
        height=height,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(
            range=[current_df["date"].min(), current_df["date"].max()],
        ),
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, showgrid=True)
    fig.update_yaxes(gridcolor=GRID_COLOR, showgrid=True, tickformat=yaxis_format["tickformat"])

    if metric == "position":
        fig.update_yaxes(autorange="reversed")

    st.plotly_chart(fig, use_container_width=True)


def render_top_table(df, dimension_label="Item", max_rows=10, hide_position=False):
    """Render a styled table of top results."""
    if df.empty:
        st.info("No " + dimension_label.lower() + " data available.")
        return

    display_df = df.head(max_rows).copy()

    display_df = display_df.rename(columns={
        "name": dimension_label,
        "clicks": "Clicks",
        "impressions": "Impressions",
        "ctr": "CTR",
        "position": "Position",
    })

    if "CTR" in display_df.columns:
        display_df["CTR"] = display_df["CTR"].apply(lambda x: "{:.2f}%".format(x*100) if pd.notna(x) else "—")

    if "Position" in display_df.columns:
        if hide_position:
            display_df = display_df.drop(columns=["Position"])
        else:
            display_df["Position"] = display_df["Position"].apply(lambda x: "{:.1f}".format(x) if pd.notna(x) and x > 0 else "—")

    for col in ["Clicks", "Impressions"]:
        if col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: "{:,}".format(int(x)) if pd.notna(x) else "—")

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_source_comparison(gsc_kpis, bing_kpis, metric="clicks"):
    """Side-by-side comparison of GSC vs Bing for a given metric."""
    fig = go.Figure(data=[
        go.Bar(
            name="Google",
            x=["Google Search Console"],
            y=[gsc_kpis.get(metric, 0)],
            marker_color="#4285F4",
            text=["{:,.0f}".format(gsc_kpis.get(metric, 0))],
            textposition="outside",
        ),
        go.Bar(
            name="Bing",
            x=["Bing Webmaster"],
            y=[bing_kpis.get(metric, 0)],
            marker_color="#00809D",
            text=["{:,.0f}".format(bing_kpis.get(metric, 0))],
            textposition="outside",
        ),
    ])

    fig.update_layout(
        title=metric.title() + ": Google vs Bing",
        showlegend=False,
        height=350,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=20),
    )
    fig.update_yaxes(gridcolor=GRID_COLOR)

    st.plotly_chart(fig, use_container_width=True)


def render_combined_timeseries(gsc_df, bing_df, metric="clicks", height=400):
    """Render a chart with both GSC and Bing data overlaid."""
    yaxis_format = _get_yaxis_format(metric)
    hover_fmt = _get_hover_format(metric)

    fig = go.Figure()

    if not gsc_df.empty:
        fig.add_trace(go.Scatter(
            x=gsc_df["date"],
            y=gsc_df[metric],
            mode="lines+markers",
            name="Google",
            line=dict(color="#4285F4", width=3),
            marker=dict(size=6),
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Google: %{y" + hover_fmt + "}<extra></extra>",
        ))

    if not bing_df.empty:
        fig.add_trace(go.Scatter(
            x=bing_df["date"],
            y=bing_df[metric],
            mode="lines+markers",
            name="Bing",
            line=dict(color="#00809D", width=3),
            marker=dict(size=6),
            hovertemplate="<b>%{x|%b %d, %Y}</b><br>Bing: %{y" + hover_fmt + "}<extra></extra>",
        ))

    # Determine date range for combined chart
    all_dates = []
    if not gsc_df.empty:
        all_dates.extend([gsc_df["date"].min(), gsc_df["date"].max()])
    if not bing_df.empty:
        all_dates.extend([bing_df["date"].min(), bing_df["date"].max()])
    
    xaxis_config = {}
    if all_dates:
        xaxis_config = dict(range=[min(all_dates), max(all_dates)])

    fig.update_layout(
        title="Daily " + metric.title() + ": Google vs Bing",
        xaxis_title="Date",
        yaxis_title=yaxis_format["title"],
        height=height,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=xaxis_config,
    )
    fig.update_xaxes(gridcolor=GRID_COLOR, showgrid=True)
    fig.update_yaxes(gridcolor=GRID_COLOR, showgrid=True, tickformat=yaxis_format["tickformat"])

    if metric == "position":
        fig.update_yaxes(autorange="reversed")

    st.plotly_chart(fig, use_container_width=True)
