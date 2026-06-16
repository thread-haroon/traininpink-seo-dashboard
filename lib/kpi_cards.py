"""KPI card components - uses Streamlit native st.metric() with smart delta logic."""

from typing import Optional

import streamlit as st


def format_number(value):
    """Format a number with commas - EXACT precision."""
    if value is None:
        return "—"
    if isinstance(value, float):
        if value == int(value):
            return "{:,}".format(int(value))
        return "{:,.1f}".format(value)
    return "{:,}".format(int(value))


def format_percentage(value, decimals=2):
    """Format a fraction as a percentage."""
    if value is None:
        return "—"
    return ("{:." + str(decimals) + "f}%").format(value * 100)


def format_position(value):
    """Format an SEO ranking position."""
    if value is None or value == 0:
        return "—"
    return "{:.1f}".format(value)


def _render_metric_with_correct_color(label, value, current, previous, lower_is_better=False, comparison_label="", help_prefix=""):
    """Render a Streamlit metric with EXPLICIT correct color logic.
    
    Streamlit's color logic:
    - delta_color="normal": green for positive, red for negative (default)
    - delta_color="inverse": red for positive, green for negative
    - delta_color="off": grey
    
    For metrics where higher is better (clicks, impressions, CTR):
        increase → green, decrease → red → use "normal"
    
    For metrics where lower is better (position):
        decrease → green, increase → red → use "inverse"
    """
    if previous is None or previous == 0 or abs(previous) < 0.001:
        st.metric(label=label, value=value)
        return

    delta = current - previous
    delta_pct = (delta / previous) * 100

    if abs(delta_pct) < 0.01:
        st.metric(label=label, value=value, delta="0.0%", delta_color="off")
        return

    # Format the delta string with sign
    sign = "+" if delta_pct > 0 else ""
    delta_str = "{}{:.1f}%".format(sign, delta_pct)

    # Choose color based on what is_good means for this metric
    # For higher-is-better metrics: use "normal" (green for positive, red for negative)
    # For lower-is-better metrics: use "inverse" (red for positive, green for negative)
    if lower_is_better:
        color = "inverse"
    else:
        color = "normal"

    help_text = None
    if comparison_label:
        help_text = "vs " + comparison_label + ": " + str(help_prefix) if help_prefix else "vs " + comparison_label

    st.metric(
        label=label,
        value=value,
        delta=delta_str,
        delta_color=color,
        help=help_text,
    )


def render_kpi_row(current_kpis, previous_kpis=None, comparison_label="", show_position=True):
    """Render KPI cards with correct color logic."""
    if show_position:
        col1, col2, col3, col4 = st.columns(4)
    else:
        col1, col2, col3 = st.columns(3)

    # Total Clicks (higher = better)
    with col1:
        clicks = current_kpis.get("clicks", 0)
        prev = previous_kpis.get("clicks", 0) if previous_kpis else None
        _render_metric_with_correct_color(
            "🖱️ Total Clicks",
            format_number(clicks),
            clicks,
            prev,
            lower_is_better=False,
            comparison_label=comparison_label,
            help_prefix=format_number(prev) if prev else "",
        )

    # Total Impressions (higher = better)
    with col2:
        impressions = current_kpis.get("impressions", 0)
        prev = previous_kpis.get("impressions", 0) if previous_kpis else None
        _render_metric_with_correct_color(
            "👁️ Total Impressions",
            format_number(impressions),
            impressions,
            prev,
            lower_is_better=False,
            comparison_label=comparison_label,
            help_prefix=format_number(prev) if prev else "",
        )

    # Average CTR (higher = better)
    with col3:
        ctr = current_kpis.get("ctr", 0.0)
        prev = previous_kpis.get("ctr", 0.0) if previous_kpis else None
        _render_metric_with_correct_color(
            "📊 Average CTR",
            format_percentage(ctr),
            ctr,
            prev,
            lower_is_better=False,
            comparison_label=comparison_label,
            help_prefix=format_percentage(prev) if prev else "",
        )

    # Average Position (LOWER = better) - special handling
    if show_position:
        with col4:
            position = current_kpis.get("position", 0.0)
            prev = previous_kpis.get("position", 0.0) if previous_kpis else None
            if prev and prev > 0:
                delta = position - prev
                if abs(delta) < 0.05:
                    st.metric(
                        label="🎯 Avg Position",
                        value=format_position(position),
                        delta="No change",
                        delta_color="off",
                    )
                else:
                    # For position: lower number = better ranking
                    # So pass delta as-is (negative if improved, positive if dropped)
                    # And use "inverse" color so:
                    #   - negative delta (improved) → green
                    #   - positive delta (dropped) → red
                    if delta < 0:
                        # Ranking improved
                        delta_str = "{:.1f} (improved)".format(delta)
                    else:
                        # Ranking dropped
                        delta_str = "+{:.1f} (dropped)".format(delta)

                    help_text = "vs " + comparison_label + ": " + format_position(prev) + " (lower=better)" if comparison_label else None
                    st.metric(
                        label="🎯 Avg Position",
                        value=format_position(position),
                        delta=delta_str,
                        delta_color="inverse",
                        help=help_text,
                    )
            else:
                st.metric(label="🎯 Avg Position", value=format_position(position))


def calculate_delta(current, previous, lower_is_better=False):
    """Backward compat wrapper."""
    if previous is None or previous == 0 or abs(previous) < 0.001:
        return None, "off"
    delta = current - previous
    delta_pct = (delta / previous) * 100
    if abs(delta_pct) < 0.01:
        return "0.0%", "off"
    sign = "+" if delta_pct > 0 else ""
    label = "{}{:.1f}%".format(sign, delta_pct)
    color = "inverse" if lower_is_better else "normal"
    return label, color


def calculate_position_delta(current, previous):
    """Backward compat wrapper."""
    if previous is None or previous == 0 or abs(previous) < 0.001:
        return None, "off"
    delta = current - previous
    if abs(delta) < 0.05:
        return "No change", "off"
    if delta < 0:
        return "{:.1f} (improved)".format(delta), "inverse"
    else:
        return "+{:.1f} (dropped)".format(delta), "inverse"


def render_single_kpi(label, value, previous_value=None, comparison_label="", value_format="number", lower_is_better=False):
    """Render a single KPI card."""
    if value_format == "percentage":
        formatted = format_percentage(value)
    elif value_format == "position":
        formatted = format_position(value)
    else:
        formatted = format_number(value)

    if previous_value is not None and previous_value > 0:
        if value_format == "position":
            delta = value - previous_value
            if abs(delta) < 0.05:
                st.metric(label=label, value=formatted, delta="No change", delta_color="off")
            elif delta < 0:
                st.metric(label=label, value=formatted, delta="{:.1f} (improved)".format(delta), delta_color="inverse")
            else:
                st.metric(label=label, value=formatted, delta="+{:.1f} (dropped)".format(delta), delta_color="inverse")
        else:
            delta = value - previous_value
            delta_pct = (delta / previous_value) * 100
            sign = "+" if delta_pct > 0 else ""
            delta_str = "{}{:.1f}%".format(sign, delta_pct)
            color = "inverse" if lower_is_better else "normal"
            st.metric(label=label, value=formatted, delta=delta_str, delta_color=color)
    else:
        st.metric(label=label, value=formatted)
