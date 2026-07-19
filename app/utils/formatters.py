"""Formatting helpers registered as Jinja filters in the app factory."""
from flask_login import current_user


def _default_currency() -> str:
    try:
        if current_user.is_authenticated and current_user.settings:
            return current_user.settings.currency
    except Exception:
        pass
    return "USD"


def format_currency(value, currency=None) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "-"
    currency = currency or _default_currency()
    symbol = {"USD": "$", "EUR": "€", "GBP": "£", "INR": "₹"}.get(currency, "$")
    sign = "-" if value < 0 else ""
    return f"{sign}{symbol}{abs(value):,.2f}"


def format_compact_number(value) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "-"
    for threshold, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "K")):
        if abs(value) >= threshold:
            return f"{value / threshold:,.1f}{suffix}"
    return f"{value:,.0f}"


def format_percent(value, decimals=1) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "-"
    return f"{value:,.{decimals}f}%"


def format_datetime(value, fmt="%b %d, %Y %I:%M %p") -> str:
    if value is None:
        return "-"
    return value.strftime(fmt)


def format_date(value, fmt="%b %d, %Y") -> str:
    if value is None:
        return "-"
    return value.strftime(fmt)


def register_template_filters(app):
    app.jinja_env.filters["currency"] = format_currency
    app.jinja_env.filters["compact"] = format_compact_number
    app.jinja_env.filters["percent"] = format_percent
    app.jinja_env.filters["datetime"] = format_datetime
    app.jinja_env.filters["dateonly"] = format_date
