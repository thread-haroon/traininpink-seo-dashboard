"""Date filter helpers - matches GSC's 3-day reporting lag."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Optional

import streamlit as st
from dateutil.relativedelta import relativedelta


@dataclass
class DateRange:
    start: date
    end: date

    @property
    def days(self):
        return (self.end - self.start).days + 1

    def __str__(self):
        return str(self.start) + " to " + str(self.end)


@dataclass
class ComparisonRange:
    """Holds the current period and an optional comparison period."""
    current: DateRange
    comparison: Optional[DateRange]
    comparison_label: str


# GSC lag is 3 days for finalized data (matches GSC UI)
GSC_DATA_LAG_DAYS = 3
# Bing publishes daily traffic faster (~2 days)
BING_DATA_LAG_DAYS = 2

PRESET_RANGES = {
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 3 months": 90,
    "Last 6 months": 180,
    "Last 12 months": 365,
    "Last 18 months": 540,
    "Last 24 months": 730,
    "Custom": None,
}

BING_PRESET_RANGES = {
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 6 months": 180,
    "Last 12 months": 365,
    "Last 18 months": 540,
    "Last 24 months": 730,
    "Custom": None,
}

# CLEAN comparison options - only 4 options (industry standard)
COMPARISON_OPTIONS = [
    "Previous period",
    "Previous year",
    "Custom range",
    "No comparison",
]

FEATURED_COUNTRIES = ["ita", "gbr", "are", "usa"]
COUNTRY_DISPLAY_NAMES = {
    "ita": "🇮🇹 Italy",
    "gbr": "🇬🇧 United Kingdom",
    "are": "🇦🇪 UAE",
    "usa": "🇺🇸 USA",
}


def _today_minus(days_back):
    return (datetime.utcnow() - timedelta(days=days_back)).date()


def _get_preset_range(preset, preset_dict=None, lag_days=GSC_DATA_LAG_DAYS):
    """Build a DateRange for a named preset, accounting for data lag."""
    if preset_dict is None:
        preset_dict = PRESET_RANGES
    end = _today_minus(lag_days)  # GSC: 3 days, Bing: 2 days
    if preset in preset_dict and preset_dict[preset] is not None:
        days = preset_dict[preset]
        start = end - timedelta(days=days - 1)
        return DateRange(start=start, end=end)
    return DateRange(start=end - timedelta(days=29), end=end)


def _compute_comparison_range(current, mode, custom_start=None, custom_end=None, lag_days=GSC_DATA_LAG_DAYS):
    """Compute the comparison date range based on the selected mode."""
    if mode == "No comparison":
        return None
    if mode == "Previous period":
        days = current.days
        prev_end = current.start - timedelta(days=1)
        prev_start = prev_end - timedelta(days=days - 1)
        return DateRange(start=prev_start, end=prev_end)
    if mode == "Previous year":
        prev_start = current.start - relativedelta(years=1)
        prev_end = current.end - relativedelta(years=1)
        return DateRange(start=prev_start, end=prev_end)
    if mode == "Custom range" and custom_start and custom_end:
        return DateRange(start=custom_start, end=custom_end)
    return None


def render_date_filters(key_prefix="main", preset_dict=None, default_index=0, lag_days=GSC_DATA_LAG_DAYS):
    """Render date range + comparison controls in the sidebar."""
    if preset_dict is None:
        preset_dict = PRESET_RANGES

    st.sidebar.markdown("### 📅 Date Range")
    preset = st.sidebar.selectbox(
        "Select range",
        options=list(preset_dict.keys()),
        index=default_index,
        key=key_prefix + "_preset",
    )
    if preset == "Custom":
        end_default = _today_minus(lag_days)
        start_default = end_default - timedelta(days=29)
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start = st.date_input("Start", value=start_default, key=key_prefix + "_start")
        with col2:
            end = st.date_input("End", value=end_default, key=key_prefix + "_end")
        if start > end:
            st.sidebar.error("Start date must be before end date")
            current = _get_preset_range("Last 7 days", preset_dict, lag_days)
        else:
            current = DateRange(start=start, end=end)
    else:
        current = _get_preset_range(preset, preset_dict, lag_days)
    st.sidebar.caption("📊 " + str(current.start) + " → " + str(current.end) + " (" + str(current.days) + " days)")

    st.sidebar.markdown("### 🔄 Comparison")
    comparison_mode = st.sidebar.selectbox(
        "Compare against",
        options=COMPARISON_OPTIONS,
        index=0,  # Default: Previous period
        key=key_prefix + "_comparison",
        help="Previous period: same length ending day before main period. Previous year: same dates one year ago."
    )
    custom_comp_start = custom_comp_end = None
    if comparison_mode == "Custom range":
        col1, col2 = st.sidebar.columns(2)
        with col1:
            custom_comp_start = st.date_input(
                "Compare start",
                value=current.start - timedelta(days=current.days),
                key=key_prefix + "_comp_start",
            )
        with col2:
            custom_comp_end = st.date_input(
                "Compare end",
                value=current.start - timedelta(days=1),
                key=key_prefix + "_comp_end",
            )
    comparison = _compute_comparison_range(
        current, comparison_mode, custom_comp_start, custom_comp_end, lag_days
    )
    if comparison:
        st.sidebar.caption("⚖️ Comparing to: " + str(comparison.start) + " → " + str(comparison.end))
    return ComparisonRange(
        current=current,
        comparison=comparison,
        comparison_label=comparison_mode,
    )


def _build_country_options(available_countries):
    available_lower = [c.lower() for c in available_countries]
    options = ["All"]
    has_featured = []
    for code in FEATURED_COUNTRIES:
        if code in available_lower:
            options.append(COUNTRY_DISPLAY_NAMES[code])
            has_featured.append(code)
    if any(c not in FEATURED_COUNTRIES for c in available_lower):
        options.append("🌍 Rest of the world")
    return options, has_featured


def _resolve_country_filter(selection, available_countries):
    if selection == "All":
        return None
    for code, display in COUNTRY_DISPLAY_NAMES.items():
        if selection == display:
            return code
    if selection == "🌍 Rest of the world":
        return "_REST_OF_WORLD_"
    return None


def render_dimension_filters(available_countries, available_devices, key_prefix="main"):
    """Render country + device filters in the sidebar."""
    st.sidebar.markdown("### 🌍 Filters")
    country_options, has_featured = _build_country_options(available_countries)
    country_selection = st.sidebar.selectbox(
        "Country",
        options=country_options,
        index=0,
        key=key_prefix + "_country",
    )
    country = _resolve_country_filter(country_selection, available_countries)

    device_options = ["All"] + available_devices
    device_selection = st.sidebar.selectbox(
        "Device",
        options=device_options,
        index=0,
        key=key_prefix + "_device",
    )
    device = device_selection if device_selection != "All" else None

    return country, device


def render_device_filter(available_devices, key_prefix="main"):
    """Render only device filter (for Bing page which lacks country data)."""
    st.sidebar.markdown("### 🌍 Filters")
    device_options = ["All"] + available_devices
    device_selection = st.sidebar.selectbox(
        "Device",
        options=device_options,
        index=0,
        key=key_prefix + "_device",
    )
    return device_selection if device_selection != "All" else None


def render_site_filter(available_sites, key_prefix="main"):
    """Render website selector in the sidebar."""
    if not available_sites:
        return None
    st.sidebar.markdown("### 🌐 Website")
    options = ["All sites"] + available_sites
    selected = st.sidebar.selectbox(
        "Website",
        options=options,
        index=1 if len(available_sites) >= 1 else 0,
        key=key_prefix + "_site",
    )
    return selected if selected != "All sites" else None
